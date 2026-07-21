"""evidence 도메인 서비스 — 수동 보충 봉인(CM-12)·증적 아카이브 조회(CM-14)·방어 리포트(CM-13, B1).

자동 봉인(item_submitted 등)은 case 도메인의 mutation과 한 트랜잭션에서 일어나야 하므로
CaseService가 EvidenceRepository를 직접 주입받아 호출한다(§1 도메인 경계 — service→service
금지). 여기 EvidenceService는 evidence 자체가 주체인 엔드포인트(수동봉인·아카이브·리포트)를 다룬다.

`export_report`는 CaseRepository·CatalogRepository도 주입받는다(브리프 지시 — 도메인 간
필요 데이터는 그 도메인 repository로, service→service 직접호출 금지 원칙 그대로 적용).
게이트 재계산(`compute_gate`)만은 예외로 `case.service`에서 순수함수를 그대로 가져다 쓴다 —
§5 계산식이 두 곳에 따로 구현되면 freeze 공식이 갈라질 위험이 있어(단일 진실 원천), case
서비스 인스턴스를 호출하는 게 아니라 부작용 없는 함수 1개를 재사용하는 것뿐이다.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import Badge
from app.domains.case.models import CaseStatus, Item, ItemStatus
from app.domains.case.repository import CaseRepository
from app.domains.case.service import GateComputation, compute_gate
from app.domains.catalog.repository import CatalogRepository
from app.domains.compare.service import BOUNDARY_NOTICE
from app.domains.evidence.models import Evidence, EvidenceEventType, EvidenceOrigin
from app.domains.evidence.schemas import (
    DefenseReport,
    DefenseReportCase,
    DefenseReportCompareFinding,
    DefenseReportEvidenceChain,
    DefenseReportEvidenceEntry,
    DefenseReportKpi,
    DefenseReportRailSummary,
    EvidenceCreate,
)
from app.domains.evidence.repository import EvidenceRepository
from app.domains.shared.enums import Rail
from app.domains.shared.exceptions import NotFoundError

_APPLICABLE_UNMET_STATUSES = (
    ItemStatus.pending,
    ItemStatus.submitted,
    ItemStatus.rejected,
)


class ArchiveMeta:
    """증적 아카이브 조회 meta — router가 core.Meta로 옮겨 담는다(경량 값 객체)."""

    def __init__(
        self,
        *,
        seal_status: str,
        total_count: int,
        last_sealed_at: datetime | None,
        head_hash: str | None,
    ) -> None:
        self.seal_status = seal_status
        self.total_count = total_count
        self.last_sealed_at = last_sealed_at
        self.head_hash = head_hash


def _seal_status(case_status: CaseStatus) -> Literal["sealed", "accruing"]:
    """sealed = 케이스가 승인 완료(completed)돼 증적 체인이 확정됨 / accruing = 축적 중."""
    return "sealed" if case_status == CaseStatus.completed else "accruing"


class EvidenceService:
    """증적 수동 봉인·아카이브 조회·방어 리포트 조립 비즈니스 로직."""

    def __init__(
        self,
        evidence_repo: EvidenceRepository,
        case_repo: CaseRepository,
        catalog_repo: CatalogRepository,
    ) -> None:
        self.evidence_repo = evidence_repo
        self.case_repo = case_repo
        self.catalog_repo = catalog_repo

    async def manual_seal(
        self, db: AsyncSession, case_id: int, payload: EvidenceCreate
    ) -> Evidence:
        """수동 보충 봉인 — 자동 봉인 트리거로 안 잡히는 처리를 관리자가 직접 기록."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        return await self.evidence_repo.append(
            db,
            case_id=case_id,
            event_type=payload.event_type,
            origin=EvidenceOrigin.manual,
            actor=payload.actor,
            action=payload.action,
            payload=payload.payload,
            document_ref=payload.document_ref,
        )

    async def get_archive(
        self, db: AsyncSession, case_id: int
    ) -> tuple[list[Evidence], ArchiveMeta]:
        """증적 아카이브 목록 + 봉인 상태 요약(CM-14)."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        entries = await self.evidence_repo.list_by_case(db, case_id)
        meta = ArchiveMeta(
            seal_status=_seal_status(case.status),
            total_count=len(entries),
            last_sealed_at=entries[-1].sealed_at if entries else None,
            head_hash=entries[-1].integrity_hash if entries else None,
        )
        return entries, meta

    async def export_report(self, db: AsyncSession, case_id: int) -> DefenseReport:
        """방어 리포트 Export(CM-13, B1) — 봉인 증적·게이트·compare 스냅샷의 파생 뷰(§10).

        저장 엔티티 아님 — 매 호출 조립. `kpi`만 봉인된 `case_approved` 스냅샷이 있으면
        그걸 우선 인용하고(재계산 아님), 없으면 §5 게이트를 라이브 계산한다(§10 규약).
        `compare_findings`는 `compare_recorded` 스냅샷을 그대로 인용한다(§3-4-1 재현성).
        """
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        items = await self.case_repo.get_items_by_case(db, case_id)
        entries = await self.evidence_repo.list_by_case(db, case_id)

        gate = compute_gate(items)  # 레일 요약(rails)엔 항상 라이브 게이트를 쓴다.
        kpi = await self._build_kpi(gate, entries)
        rails = await self._build_rails(db, items, gate)
        compare_findings = _build_compare_findings(entries)
        evidence_chain = _build_evidence_chain(entries, case.status)

        return DefenseReport(
            case=DefenseReportCase(
                id=case.id,
                subject_name=case.subject_name,
                subject_job=case.subject_job,
                subject_rank=case.subject_rank,
                exit_reason=case.exit_reason,
                exit_date=case.exit_date,
                status=case.status,
            ),
            generated_at=datetime.now(UTC),
            kpi=kpi,
            rails=rails,
            compare_findings=compare_findings,
            evidence_chain=evidence_chain,
            boundary_notice=BOUNDARY_NOTICE,
        )

    async def _build_kpi(
        self, gate: GateComputation, entries: Sequence[Evidence]
    ) -> DefenseReportKpi:
        """봉인된 `case_approved` 스냅샷이 있으면 그걸 우선 인용, 없으면 §5 라이브 계산(§10)."""
        sealed = next(
            (
                e.payload
                for e in reversed(entries)
                if e.event_type == EvidenceEventType.case_approved
            ),
            None,
        )
        if sealed is not None:
            return DefenseReportKpi(
                overall_completion=sealed["overall_completion"],
                rail_completion=sealed["rail_completion"],
                risk_count=sealed["risk_count"],
                defensible=sealed["defensible"],
            )
        return DefenseReportKpi(
            overall_completion=gate.overall_completion,
            rail_completion=gate.rail_completion,
            risk_count=gate.risk_count,
            defensible=gate.defensible,
        )

    async def _build_rails(
        self, db: AsyncSession, items: Sequence[Item], gate: GateComputation
    ) -> list[DefenseReportRailSummary]:
        """레일별 완료율(라이브 게이트)·미충족 건수·근거배지(§10 `rails`)."""
        rails = []
        for rail in Rail:
            rail_items = [i for i in items if i.rail == rail]
            unmet = sum(1 for i in rail_items if i.status in _APPLICABLE_UNMET_STATUSES)
            standard_ids = sorted(
                {sid for i in rail_items for sid in (i.standard_ids or [])}
            )
            standards = await self.catalog_repo.get_standards_by_ids(db, standard_ids)
            badges = [
                Badge(tier=s.tier, title=s.title, url=s.source_url, version=s.version)
                for s in standards
            ]
            rails.append(
                DefenseReportRailSummary(
                    rail=rail,
                    completion=gate.rail_completion[rail],
                    unmet_count=unmet,
                    badges=badges,
                )
            )
        return rails


def _build_compare_findings(
    entries: Sequence[Evidence],
) -> list[DefenseReportCompareFinding]:
    """봉인된 `compare_recorded` 이벤트 전체를 스냅샷 그대로 인용(§3-4-1·§10) — 재계산 없음."""
    findings = []
    for e in entries:
        if e.event_type != EvidenceEventType.compare_recorded:
            continue
        payload = e.payload
        findings.append(
            DefenseReportCompareFinding(
                rail=payload["rail"],
                subject=payload["subject"],
                rows=payload["rows"],
                unmet_count=payload["unmet_count"],
                badges=payload["badges"],
                boundary_notice=payload["boundary_notice"],
                sealed_seq=e.seq,
            )
        )
    return findings


def _build_evidence_chain(
    entries: Sequence[Evidence], case_status: CaseStatus
) -> DefenseReportEvidenceChain:
    """증적 체인 요약 — `head_hash`가 위변조 검증 앵커(§10)."""
    return DefenseReportEvidenceChain(
        total_count=len(entries),
        seal_status=_seal_status(case_status),
        first_seq=entries[0].seq if entries else 0,
        last_seq=entries[-1].seq if entries else 0,
        head_hash=entries[-1].integrity_hash if entries else None,
        entries=[
            DefenseReportEvidenceEntry(
                seq=e.seq,
                occurred_at=e.occurred_at,
                actor=e.actor,
                action=e.action,
                event_type=e.event_type,
                integrity_hash=e.integrity_hash,
            )
            for e in entries
        ],
    )
