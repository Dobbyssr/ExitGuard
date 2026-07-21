"""compare 도메인 서비스 — LLM seam(신호추출) → 결정론 조립 파이프라인(data-model §6-4).

파이프라인(고정 순서, §6-4):
  reason_text → ① signal_extractor(seam, 규칙기반) → SignalExtraction
              → ② 화이트리스트 검증(라벨 폐집합·evidence_span 부분문자열)
              → ③ 신호→요구요소 매핑 → ④ 코퍼스 필터(LaborPrecedent)
              → ⑤ 5행 템플릿 조립 → ⑥ unmet_count·badges → ⑦ boundary_notice 삽입
판단·문구생성은 전부 ②~⑦(결정론)이 소유한다 — LLM(①)은 신호만 낸다("GPT 래퍼 아님"의 증명).
5행 shape·boundary_notice는 정상/실패(fallback) 어떤 경로에서도 깨지지 않는다.

MVP는 노무(labor) 레일만 구현한다(other rails = 대표3 몫, §7). intake-compare 경로는
CaseRepository로 실제 케이스의 Item을 읽어 LB-03 unmet_count·L-04 D-day를 채우고,
결과 확정 시 EvidenceRepository로 `compare_recorded` 봉인까지 같은 트랜잭션에서 수행한다
(CaseService→EvidenceRepository와 동일한 패턴 — service→service 직접호출 금지, §1).
"""

from collections.abc import Sequence
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import Badge
from app.domains.case.repository import CaseRepository
from app.domains.catalog.models import StandardTier
from app.domains.catalog.repository import CatalogRepository
from app.domains.compare.schemas import (
    CaseFacts,
    CompareInput,
    CompareResult,
    CompareRow,
    CompareRowKind,
    Signal,
)
from app.domains.compare.signal_extractor import extract_signals
from app.domains.evidence.models import EvidenceEventType, EvidenceOrigin
from app.domains.evidence.repository import EvidenceRepository
from app.domains.labor.models import (
    DISMISSAL_CASE_TYPES,
    LaborPrecedent,
    LaborRequiredElement,
)
from app.domains.labor.repository import LaborRepository
from app.domains.labor.rollup import LaborRollup, compute_labor_rollup
from app.domains.shared.enums import Rail
from app.domains.shared.exceptions import CompareFailedError, NotFoundError
from app.domains.user.models import User

BOUNDARY_NOTICE = (
    "본 결과는 위법 여부를 판정하지 않습니다. 공개된 법령·판례 기준과 회사 입력 상태의 "
    "대조 결과·기한만 제공하며, 구체 사건의 판단은 전문가의 몫입니다."
)

# MVP 화이트리스트(§5-1) — written_notice 단일 요소만 실제 대조한다. dismissal_notice·
# just_cause는 enum에 존재하되 이 폐집합 밖이라 신호가 와도 드롭된다(§6-4 검증).
_ALLOWED_LABELS: tuple[str, ...] = (LaborRequiredElement.written_notice.value,)

_WRITTEN_NOTICE_STANDARD_TITLES = (
    "근로기준법 제27조",
    "중앙노동위원회 주요 판정례 (서면통지 위반 계열)",
    "고용노동부 해고·금품청산 관련 안내",
)

_FALLBACK_RISK_TEXT = "확인된 신호가 없어 공개 판정례 인용 없이 기준 대조만 제공합니다."


def validate_signals(signals: Sequence[Signal], reason_text: str) -> list[Signal]:
    """화이트리스트 검증(§6-4 ②) — 폐집합 밖 라벨, evidence_span 비-부분문자열 신호를 드롭한다.

    순수함수로 분리해 signal_extractor 없이도 단위테스트할 수 있게 한다(환각 차단 로직의
    핵심이라 별도 검증).
    """
    valid: list[Signal] = []
    for signal in signals:
        if signal.label not in _ALLOWED_LABELS:
            continue
        if not signal.evidence_span or signal.evidence_span not in reason_text:
            continue
        valid.append(signal)
    return valid


def _dday_text(deadline: date | None) -> str:
    """잔여일 표기 — 양수 D-n(남음)/음수 D+n(경과)/미정(§1-7 "미충족 N건/D-day" 프레이밍만)."""
    if deadline is None:
        return "미정"
    delta = (deadline - date.today()).days
    return f"D-{delta}" if delta >= 0 else f"D+{abs(delta)}"


def _build_risk_text(precedents: Sequence[LaborPrecedent]) -> str:
    """risk 행(§5-3) — 사례 프레이밍 고정, 실측 seq만 치환(단정 금지)."""
    lead_text = (
        "구두·약식으로 통보하고 서면통지가 누락된 경우, 공개 판정례에서 "
        "부당해고로 판정된 사례가 있습니다."
    )
    if not precedents:
        return lead_text
    seqs = "·".join(str(p.seq) for p in precedents[:3])
    lead = precedents[0]
    return f"{lead_text} (중앙노동위 판정례 순번 {seqs}: {lead.title})"


def _standard_url(badges: Sequence[Badge]) -> str | None:
    l1 = next((b for b in badges if b.tier == StandardTier.L1), None)
    return l1.url if l1 is not None else (badges[0].url if badges else None)


class CompareService:
    """compare 파이프라인 조립 — 노무(labor) 레일 규칙을 채운 결정론 단계 소유자."""

    def __init__(
        self,
        catalog_repo: CatalogRepository,
        labor_repo: LaborRepository,
        case_repo: CaseRepository,
        evidence_repo: EvidenceRepository,
    ) -> None:
        self.catalog_repo = catalog_repo
        self.labor_repo = labor_repo
        self.case_repo = case_repo
        self.evidence_repo = evidence_repo

    async def compare(
        self,
        db: AsyncSession,
        input: CompareInput,
        *,
        labor_rollup: LaborRollup | None = None,
        l04_deadline: date | None = None,
    ) -> CompareResult:
        """`CompareInput` → `CompareResult`(§6). MVP는 rail=labor만 지원한다."""
        if input.rail != Rail.labor:
            raise CompareFailedError(
                f"MVP는 노무(labor) 레일만 지원합니다(rail={input.rail.value})"
            )

        extraction = extract_signals(
            input.case_facts.reason_text or "", _ALLOWED_LABELS
        )
        valid_signals = validate_signals(
            extraction.signals, input.case_facts.reason_text or ""
        )

        if not valid_signals:
            return await self._build_fallback(db, input, labor_rollup)
        return await self._build_written_notice_result(
            db, input, labor_rollup, l04_deadline
        )

    async def intake_compare(
        self, db: AsyncSession, case_id: int, actor: User
    ) -> CompareResult:
        """인테이크 대조 래퍼(CM-05, api-spec §2-3) — 케이스에서 case_facts 자동 채움.

        내부적으로 `compare()`를 호출하되, 실제 케이스의 노무 Item으로 LB-03 unmet_count·
        L-04 금품청산 D-day를 채우고, 확정된 결과를 `compare_recorded`로 자동 봉인한다
        (data-model §3-4-1 — 방어 리포트가 재계산 없이 이 스냅샷을 인용).
        """
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")

        items = await self.case_repo.get_items_by_case(db, case_id)
        labor_items = [i for i in items if i.rail == Rail.labor]
        rollup = compute_labor_rollup(labor_items)
        l04 = next((i for i in labor_items if i.code == "L-04"), None)

        compare_input = CompareInput(
            rail=Rail.labor,
            subject="LB-04:written_notice",
            case_facts=CaseFacts(
                reason_text=case.reason_text,
                exit_reason=case.exit_reason,
                exit_date=case.exit_date,
                job=case.subject_job,
                rank=case.subject_rank,
            ),
            item_context=None,
        )
        result = await self.compare(
            db,
            compare_input,
            labor_rollup=rollup,
            l04_deadline=l04.deadline if l04 is not None else None,
        )

        await self.evidence_repo.append(
            db,
            case_id=case.id,
            event_type=EvidenceEventType.compare_recorded,
            origin=EvidenceOrigin.auto,
            actor=actor.name,
            action="판정례 대조 결과 확정",
            payload=result.model_dump(mode="json"),
        )
        return result

    async def _build_written_notice_result(
        self,
        db: AsyncSession,
        input: CompareInput,
        labor_rollup: LaborRollup | None,
        l04_deadline: date | None,
    ) -> CompareResult:
        """유효 신호(written_notice) 있을 때의 본 경로 — 코퍼스 필터·5행 조립(§5-3)."""
        precedents = await self.labor_repo.find_by_element_and_categories(
            db, LaborRequiredElement.written_notice, DISMISSAL_CASE_TYPES
        )
        standards = await self.catalog_repo.list_standards(
            db, rail=Rail.labor, titles=_WRITTEN_NOTICE_STANDARD_TITLES
        )
        badges = [
            Badge(tier=s.tier, title=s.title, url=s.source_url, version=s.version)
            for s in standards
        ]
        status_text, unmet_count = self._status_row(labor_rollup, l04_deadline)

        rows = [
            CompareRow(
                kind=CompareRowKind.procedure,
                text="회사사유 텍스트에서 구두·문자 통보 정황 신호가 확인됩니다.",
            ),
            CompareRow(
                kind=CompareRowKind.standard,
                text=(
                    "근로기준법 제27조 — 해고 시 해고사유와 시기를 서면으로 "
                    "통지해야 합니다."
                ),
            ),
            CompareRow(kind=CompareRowKind.risk, text=_build_risk_text(precedents)),
            CompareRow(kind=CompareRowKind.status, text=status_text),
            CompareRow(
                kind=CompareRowKind.source,
                text="근로기준법 제27조(국가법령정보) · 중앙노동위원회 주요 판정례",
                url=_standard_url(badges),
            ),
        ]
        return CompareResult(
            rail=Rail.labor,
            subject=input.subject,
            rows=rows,
            unmet_count=unmet_count,
            badges=badges,
            boundary_notice=BOUNDARY_NOTICE,
            expert_referral=True,
        )

    async def _build_fallback(
        self,
        db: AsyncSession,
        input: CompareInput,
        labor_rollup: LaborRollup | None,
    ) -> CompareResult:
        """Fallback(§6-4) — 유효 신호 0건. 5행 shape·boundary_notice는 그대로 유지한다."""
        refs = input.item_context.standard_refs if input.item_context else []
        standards = await self.catalog_repo.get_standards_by_ids(db, refs)
        badges = [
            Badge(tier=s.tier, title=s.title, url=s.source_url, version=s.version)
            for s in standards
        ]
        status_text, unmet_count = self._status_row(labor_rollup, None)
        standard_text = (
            f"{badges[0].title} 등 케이스에 연계된 근거 기준을 참고하세요."
            if badges
            else "케이스에 연계된 근거 기준이 없어 표시할 대조 기준이 없습니다."
        )
        source_text = (
            " · ".join(b.title for b in badges)
            if badges
            else "연계된 근거 기준이 없습니다."
        )

        rows = [
            CompareRow(
                kind=CompareRowKind.procedure, text="추가 신호가 확인되지 않았습니다."
            ),
            CompareRow(kind=CompareRowKind.standard, text=standard_text),
            CompareRow(kind=CompareRowKind.risk, text=_FALLBACK_RISK_TEXT),
            CompareRow(kind=CompareRowKind.status, text=status_text),
            CompareRow(
                kind=CompareRowKind.source, text=source_text, url=_standard_url(badges)
            ),
        ]
        return CompareResult(
            rail=Rail.labor,
            subject=input.subject,
            rows=rows,
            unmet_count=unmet_count,
            badges=badges,
            boundary_notice=BOUNDARY_NOTICE,
            expert_referral=None,
        )

    def _status_row(
        self, labor_rollup: LaborRollup | None, l04_deadline: date | None
    ) -> tuple[str, int]:
        """status 행(§5-3) — "미충족 N건 · 지급기한 D-day". 케이스 연계 없으면 일반 안내."""
        if labor_rollup is None:
            return (
                "공개 기준 대조 결과입니다. 케이스와 연계하면 미충족 건수·기한이 "
                "함께 제공됩니다.",
                0,
            )
        text = (
            f"노무 검사 항목 {labor_rollup.total_count}건 중 "
            f"미충족 {labor_rollup.unmet_count}건 · "
            f"금품청산(제36조) 지급기한 {_dday_text(l04_deadline)}"
        )
        return text, labor_rollup.unmet_count
