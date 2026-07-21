"""케이스(case) 도메인 서비스 — 접수·게이트 집계·상태머신·승인 확정(§8 도메인 메서드 위치).

유비쿼터스 언어: '케이스' = 퇴사 1건이 3레일을 관통하는 단위(예: 김민준 퇴사).
증적 봉인은 EvidenceRepository를 직접 주입받아 호출한다(EvidenceService 경유 금지 —
service→service 직접호출은 도메인 경계 붕괴, backend/CLAUDE.md §1 / 도비 브리프 명시).
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.case.models import (
    Approval,
    ApprovalDecision,
    Case,
    CaseStatus,
    ExitReason,
    Item,
    ItemStatus,
)
from app.domains.case.repository import CaseRepository
from app.domains.case.schemas import (
    ApprovalCreate,
    ApproveRequest,
    CaseCreate,
    ReviewRequest,
)
from app.domains.catalog.models import Profile, Standard
from app.domains.catalog.repository import CatalogRepository
from app.domains.evidence.models import Evidence, EvidenceEventType, EvidenceOrigin
from app.domains.evidence.repository import EvidenceRepository
from app.domains.shared.enums import Rail
from app.domains.shared.exceptions import InvalidStateError, NotFoundError
from app.domains.user.models import User

# 유형 규칙(§4) — 항목코드별로 "해당없음(na)" 처리되는 exit_reason 집합.
# 지금은 L-09(해고예고 30일)가 유일한 예: 실제 '해고'가 아니면 예고 의무가 없다.
# 별도 스키마 컬럼을 새로 만들지 않고(계약 미확정 구멍) 서비스 레벨 상수로 처리 —
# 레일별 규칙이 늘어나면 그때 data-model에 정식 필드로 승격(도비/헤르미온느 조율).
_NOT_APPLICABLE_RULES: dict[str, frozenset[ExitReason]] = {
    "L-09": frozenset(
        {
            ExitReason.voluntary,
            ExitReason.recommended_resignation,
            ExitReason.contract_expiry,
        }
    ),
}


def _resolve_initial_status(exit_reason: ExitReason, code: str) -> ItemStatus:
    """접수 시 항목 초기 상태 — 유형 규칙에 해당하면 not_applicable, 아니면 pending."""
    if exit_reason in _NOT_APPLICABLE_RULES.get(code, frozenset()):
        return ItemStatus.not_applicable
    return ItemStatus.pending


@dataclass(frozen=True)
class ItemCount:
    """게이트 계산 입력 단위 — 실물 Item 또는 GROUP BY 집계행 어느 쪽에서도 만들 수 있다."""

    rail: Rail
    status: ItemStatus
    blocking: bool
    count: int


@dataclass(frozen=True)
class GateComputation:
    """Gate(§5) 파생값. 저장하지 않는다 — 매번 Item에서 다시 계산."""

    rail_completion: dict[Rail, int]
    overall_completion: int
    risk_count: int
    defensible: bool


def compute_gate_from_counts(counts: Sequence[ItemCount]) -> GateComputation:
    """§5 결정론적 계산식(freeze) — (rail,status,blocking,count) 집계로부터 게이트 산출.

    순수함수. 목록(CM-03)은 GROUP BY 집계행을, 상세는 실물 Item(count=1×N)을 넣는다.
    """
    rail_applicable: dict[Rail, int] = dict.fromkeys(Rail, 0)
    rail_approved: dict[Rail, int] = dict.fromkeys(Rail, 0)
    total_applicable = 0
    total_approved = 0
    risk_count = 0
    for c in counts:
        if c.status != ItemStatus.not_applicable:
            rail_applicable[c.rail] += c.count
            total_applicable += c.count
        if c.status == ItemStatus.approved:
            rail_approved[c.rail] += c.count
            total_approved += c.count
        if c.blocking and c.status not in (
            ItemStatus.approved,
            ItemStatus.not_applicable,
        ):
            risk_count += c.count

    rail_completion = {
        rail: round(100 * rail_approved[rail] / max(1, rail_applicable[rail]))
        for rail in Rail
    }
    overall_completion = round(100 * total_approved / max(1, total_applicable))
    return GateComputation(
        rail_completion=rail_completion,
        overall_completion=overall_completion,
        risk_count=risk_count,
        defensible=risk_count == 0,
    )


def compute_gate(items: Sequence[Item]) -> GateComputation:
    """실물 Item 목록으로부터 게이트 산출(단건 상세/gate 엔드포인트용)."""
    counts = [
        ItemCount(rail=i.rail, status=i.status, blocking=i.blocking, count=1)
        for i in items
    ]
    return compute_gate_from_counts(counts)


def recompute_status(current_status: CaseStatus, items: Sequence[Item]) -> CaseStatus:
    """Case.status 파생(§3-1-1) — completed는 종단상태(자동으로 되돌리지 않는다)."""
    if current_status == CaseStatus.completed:
        return current_status
    has_submitted = any(i.status == ItemStatus.submitted for i in items)
    return CaseStatus.review_waiting if has_submitted else CaseStatus.in_progress


@dataclass
class CaseDetail:
    """케이스 상세 조립 결과 — router가 이걸 Pydantic 응답으로 변환한다."""

    case: Case
    items: list[Item]
    gate: GateComputation
    standards_by_id: dict[int, Standard] = field(default_factory=dict)


_SORT_KEYS = {
    "deadline": lambda case, gate: case.exit_date,
    "risk": lambda case, gate: -gate.risk_count,
    "completion": lambda case, gate: gate.overall_completion,
    "name": lambda case, gate: case.subject_name,
}


class CaseService:
    """케이스 수명주기(접수→상신/검토→게이트→승인) 비즈니스 로직."""

    def __init__(
        self,
        case_repo: CaseRepository,
        catalog_repo: CatalogRepository,
        evidence_repo: EvidenceRepository,
    ) -> None:
        self.case_repo = case_repo
        self.catalog_repo = catalog_repo
        self.evidence_repo = evidence_repo

    async def create_case(
        self, db: AsyncSession, payload: CaseCreate, actor: User
    ) -> Case:
        """케이스 접수(CM-04) — profile_id 있으면 rail_map의 템플릿을 Item으로 복제(§3-7)."""
        case = await self.case_repo.create_case(
            db,
            subject_name=payload.subject_name,
            subject_job=payload.subject_job,
            subject_rank=payload.subject_rank,
            subject_role_title=payload.subject_role_title,
            exit_reason=payload.exit_reason,
            reason_text=payload.reason_text,
            exit_date=payload.exit_date,
            intake_route=payload.intake_route,
            profile_id=payload.profile_id,
            created_by=actor.id,
        )
        if payload.profile_id is not None:
            profile = await self.catalog_repo.get_profile(db, payload.profile_id)
            if profile is not None:
                await self._apply_profile(db, case, profile)
        await db.flush()
        return case

    async def _apply_profile(
        self, db: AsyncSession, case: Case, profile: Profile
    ) -> None:
        """profile.rail_map → 각 RailTemplate의 TemplateItem을 Item으로 복제(빈 종이 금지)."""
        for rail_key, rail_template_id in profile.rail_map.items():
            if not rail_template_id:
                continue
            template_items = await self.catalog_repo.list_template_items(
                db, rail_template_id
            )
            for ti in template_items:
                item = Item(
                    case_id=case.id,
                    rail=Rail(rail_key),
                    code=ti.code,
                    name=ti.name,
                    kind=ti.kind,
                    status=_resolve_initial_status(case.exit_reason, ti.code),
                    blocking=ti.blocking,
                    standard_ids=ti.standard_ids,
                    # detail_schema는 Phase 1에서 레일별로 "채워진 값"까지 겸한다(MVP는
                    # 회사 커스텀이 없어 스키마=값). 노무는 deadline_rule 등(§2-2)을 여기서
                    # 그대로 복제해 받는다 — case 도메인은 내용을 모른 채 통째로 옮길 뿐이다.
                    detail=ti.detail_schema,
                )
                await self.case_repo.add_item(db, item)
        await db.flush()

    async def get_case_detail(self, db: AsyncSession, case_id: int) -> CaseDetail:
        """케이스 상세(CM-07) — case+gate+items+근거배지 원천(Standard) 조립."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        items = await self.case_repo.get_items_by_case(db, case_id)
        gate = compute_gate(items)
        standard_ids = sorted({sid for i in items for sid in (i.standard_ids or [])})
        standards = await self.catalog_repo.get_standards_by_ids(db, standard_ids)
        return CaseDetail(
            case=case,
            items=items,
            gate=gate,
            standards_by_id={s.id: s for s in standards},
        )

    async def get_gate(self, db: AsyncSession, case_id: int) -> GateComputation:
        """통합 게이트 집계(CM-08) — mutation 없는 순수 파생 조회."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        items = await self.case_repo.get_items_by_case(db, case_id)
        return compute_gate(items)

    async def list_cases(
        self,
        db: AsyncSession,
        *,
        status_filter: CaseStatus | None,
        q: str | None,
        sort: str,
        page: int,
        size: int,
    ) -> tuple[list[tuple[Case, GateComputation]], int]:
        """목록(CM-03) — 필터·검색 후 1쿼리 집계로 게이트 계산, 정렬·페이지는 파이썬에서."""
        cases = await self.case_repo.list_cases(db, status_filter=status_filter, q=q)
        rows = await self.case_repo.get_item_counts(db, [c.id for c in cases])
        counts_by_case: dict[int, list[ItemCount]] = defaultdict(list)
        for row in rows:
            counts_by_case[row.case_id].append(
                ItemCount(
                    rail=row.rail,
                    status=row.status,
                    blocking=row.blocking,
                    count=row.cnt,
                )
            )
        paired = [
            (case, compute_gate_from_counts(counts_by_case.get(case.id, [])))
            for case in cases
        ]
        key_fn = _SORT_KEYS.get(sort)
        if key_fn is not None:
            paired.sort(key=lambda pair: key_fn(pair[0], pair[1]))
        else:
            paired.sort(key=lambda pair: pair[0].created_at, reverse=True)
        total = len(paired)
        start = (page - 1) * size
        return paired[start : start + size], total

    async def _recompute_case_status(self, db: AsyncSession, case_id: int) -> None:
        """항목 전이 후 Case.status 재파생(§3-1-1)."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            return
        items = await self.case_repo.get_items_by_case(db, case_id)
        case.status = recompute_status(case.status, items)
        # updated_at은 DB onupdate 트리거라 async 세션에서 지연로드(MissingGreenlet)를
        # 일으킨다 — Approval.submitted_at/Evidence.sealed_at과 같은 이유로 명시 설정.
        case.updated_at = datetime.now(UTC)
        await db.flush()

    async def submit_item(
        self, db: AsyncSession, item_id: int, payload: ApprovalCreate, actor: User
    ) -> Approval:
        """상신(CM-10) — pending|rejected → submitted, Approval 생성 + 증적 자동봉인."""
        item = await self.case_repo.get_item(db, item_id)
        if item is None:
            raise NotFoundError(f"항목을 찾을 수 없습니다(id={item_id})")
        if item.status not in (ItemStatus.pending, ItemStatus.rejected):
            raise InvalidStateError(
                f"'{item.status.value}' 상태에서는 상신할 수 없습니다",
                fields={"current_status": item.status.value},
            )

        attachments = (
            [a.model_dump() for a in payload.attachments]
            if payload.attachments
            else None
        )
        approval = Approval(
            item_id=item.id,
            submitter_id=actor.id,
            memo=payload.memo,
            attachments=attachments,
            signed=payload.signed,
            submitted_at=datetime.now(UTC),
        )
        await self.case_repo.add_approval(db, approval)
        item.status = ItemStatus.submitted
        await db.flush()
        await self._recompute_case_status(db, item.case_id)

        await self.evidence_repo.append(
            db,
            case_id=item.case_id,
            event_type=EvidenceEventType.item_submitted,
            origin=EvidenceOrigin.auto,
            actor=actor.name,
            action=f"{item.name} 상신",
            payload={
                "item_code": item.code,
                "item_status": item.status.value,
                "memo": payload.memo,
                "attachments": attachments,
                "signed": payload.signed,
                "submitted_by": actor.name,
            },
        )
        return approval

    async def review_item(
        self, db: AsyncSession, item_id: int, payload: ReviewRequest, actor: User
    ) -> Approval:
        """검토(CM-10) — submitted → approved|rejected + 증적 자동봉인."""
        item = await self.case_repo.get_item(db, item_id)
        if item is None:
            raise NotFoundError(f"항목을 찾을 수 없습니다(id={item_id})")
        if item.status != ItemStatus.submitted:
            raise InvalidStateError(
                f"'{item.status.value}' 상태에서는 검토할 수 없습니다",
                fields={"current_status": item.status.value},
            )
        approval = await self.case_repo.get_pending_approval(db, item_id)
        if approval is None:
            raise InvalidStateError("검토 대기 중인 상신 기록이 없습니다")

        approval.reviewer_id = actor.id
        approval.reviewed_at = datetime.now(UTC)
        if payload.memo:
            # 검토 메모(확인 근거/반려 사유) — 계약(§3-3)에 별도 리뷰메모 컬럼이 없어
            # basis_note("기준 근거 문구")를 검토 시점 메모로 재사용한다(스키마 변경 없음).
            approval.basis_note = payload.memo

        if payload.decision == "confirmed":
            approval.decision = ApprovalDecision.confirmed
            item.status = ItemStatus.approved
            event_type = EvidenceEventType.item_confirmed
            action = f"{item.name} 확인완료"
        else:
            approval.decision = ApprovalDecision.rejected
            item.status = ItemStatus.rejected
            event_type = EvidenceEventType.item_rejected
            action = f"{item.name} 반려"

        await db.flush()
        await self._recompute_case_status(db, item.case_id)

        evidence_payload: dict = {
            "item_code": item.code,
            "decision": approval.decision.value if approval.decision else None,
            "reviewer": actor.name,
        }
        if payload.decision == "confirmed":
            evidence_payload["basis_note"] = approval.basis_note
        else:
            evidence_payload["reason"] = payload.memo

        await self.evidence_repo.append(
            db,
            case_id=item.case_id,
            event_type=event_type,
            origin=EvidenceOrigin.auto,
            actor=actor.name,
            action=action,
            payload=evidence_payload,
        )
        return approval

    async def approve_case(
        self, db: AsyncSession, case_id: int, payload: ApproveRequest, actor: User
    ) -> tuple[Case, Evidence]:
        """승인 확정(T3) — approvable(defensible && submitted==0)만 통과, 우회 없음."""
        case = await self.case_repo.get_case(db, case_id)
        if case is None:
            raise NotFoundError(f"케이스를 찾을 수 없습니다(id={case_id})")
        items = await self.case_repo.get_items_by_case(db, case_id)
        gate = compute_gate(items)
        submitted_count = sum(1 for i in items if i.status == ItemStatus.submitted)

        if not (gate.defensible and submitted_count == 0):
            raise InvalidStateError(
                "미해소 리스크 또는 미검토 상신이 남아 있어 승인할 수 없습니다",
                fields={
                    "risk_count": gate.risk_count,
                    "submitted_count": submitted_count,
                },
            )

        case.status = CaseStatus.completed
        case.updated_at = datetime.now(UTC)
        await db.flush()

        evidence_payload = {
            "overall_completion": gate.overall_completion,
            "rail_completion": {r.value: v for r, v in gate.rail_completion.items()},
            "risk_count": gate.risk_count,
            "defensible": gate.defensible,
            "approved_by": actor.name,
            "approved_at": datetime.now(UTC).isoformat(),
        }
        if payload.memo:
            evidence_payload["memo"] = payload.memo

        evidence = await self.evidence_repo.append(
            db,
            case_id=case_id,
            event_type=EvidenceEventType.case_approved,
            origin=EvidenceOrigin.auto,
            actor=actor.name,
            action="방어 가능 상태로 승인",
            payload=evidence_payload,
        )
        return case, evidence
