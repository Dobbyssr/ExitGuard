"""Item 상태머신(data-model §4) — service+Mock repo 유닛 테스트. 실 DB 불필요."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.domains.case.models import (
    Approval,
    ApprovalDecision,
    Case,
    CaseStatus,
    Item,
    ItemStatus,
)
from app.domains.case.schemas import ApprovalCreate, ReviewRequest
from app.domains.case.service import CaseService
from app.domains.shared.enums import ItemKind, Rail
from app.domains.shared.exceptions import InvalidStateError
from app.domains.user.models import Role, User


def _item(status: ItemStatus, item_id: int = 1, case_id: int = 1) -> Item:
    item = Item(
        case_id=case_id,
        rail=Rail.labor,
        code="L-01",
        name="테스트 항목",
        kind=ItemKind.statutory,
        status=status,
        blocking=True,
    )
    item.id = item_id
    return item


def _case(case_id: int = 1, status: CaseStatus = CaseStatus.in_progress) -> Case:
    case = Case(
        subject_name="홍길동",
        subject_job="개발",
        subject_rank="사원",
        exit_reason="voluntary",
        exit_date=date(2026, 1, 1),
        intake_route="groupware",
        created_by=1,
    )
    case.id = case_id
    case.status = status
    return case


def _actor(role: Role) -> User:
    user = User(name="테스트유저", email=f"{role.value}@test.example", role=role)
    user.id = 1
    return user


def _service(case_repo: AsyncMock) -> CaseService:
    return CaseService(case_repo, AsyncMock(), AsyncMock())


async def test_submit_item_when_pending_transitions_to_submitted() -> None:
    item = _item(ItemStatus.pending)
    case = _case()
    case_repo = AsyncMock()
    case_repo.get_item.return_value = item
    case_repo.get_case.return_value = case
    case_repo.get_items_by_case.return_value = [item]
    service = _service(case_repo)

    approval = await service.submit_item(
        AsyncMock(), 1, ApprovalCreate(memo="상신 메모", signed=True), _actor(Role.user)
    )

    assert item.status == ItemStatus.submitted
    assert approval.memo == "상신 메모"
    case_repo.add_approval.assert_awaited_once()
    service.evidence_repo.append.assert_awaited_once()  # type: ignore[attr-defined]


async def test_submit_item_when_rejected_transitions_to_submitted_again() -> None:
    """재상신 — rejected → submitted도 허용된다(§4)."""
    item = _item(ItemStatus.rejected)
    case_repo = AsyncMock()
    case_repo.get_item.return_value = item
    case_repo.get_case.return_value = _case()
    case_repo.get_items_by_case.return_value = [item]
    service = _service(case_repo)

    await service.submit_item(
        AsyncMock(), 1, ApprovalCreate(signed=True), _actor(Role.user)
    )

    assert item.status == ItemStatus.submitted


@pytest.mark.parametrize(
    "status", [ItemStatus.approved, ItemStatus.submitted, ItemStatus.not_applicable]
)
async def test_submit_item_when_invalid_status_raises_409(status: ItemStatus) -> None:
    """approved/submitted/not_applicable 상태에서 상신 시도 → INVALID_TRANSITION."""
    item = _item(status)
    case_repo = AsyncMock()
    case_repo.get_item.return_value = item
    service = _service(case_repo)

    with pytest.raises(InvalidStateError):
        await service.submit_item(
            AsyncMock(), 1, ApprovalCreate(signed=True), _actor(Role.user)
        )


async def test_review_item_when_confirmed_transitions_to_approved() -> None:
    item = _item(ItemStatus.submitted)
    pending_approval = Approval(
        item_id=item.id, submitter_id=1, signed=True, submitted_at=datetime.now(UTC)
    )
    case_repo = AsyncMock()
    case_repo.get_item.return_value = item
    case_repo.get_pending_approval.return_value = pending_approval
    case_repo.get_case.return_value = _case(status=CaseStatus.review_waiting)
    case_repo.get_items_by_case.return_value = [item]
    service = _service(case_repo)

    result = await service.review_item(
        AsyncMock(), 1, ReviewRequest(decision="confirmed"), _actor(Role.admin)
    )

    assert item.status == ItemStatus.approved
    assert result.decision == ApprovalDecision.confirmed
    service.evidence_repo.append.assert_awaited_once()  # type: ignore[attr-defined]


async def test_review_item_when_rejected_transitions_to_rejected() -> None:
    item = _item(ItemStatus.submitted)
    pending_approval = Approval(
        item_id=item.id, submitter_id=1, signed=True, submitted_at=datetime.now(UTC)
    )
    case_repo = AsyncMock()
    case_repo.get_item.return_value = item
    case_repo.get_pending_approval.return_value = pending_approval
    case_repo.get_case.return_value = _case(status=CaseStatus.review_waiting)
    case_repo.get_items_by_case.return_value = [item]
    service = _service(case_repo)

    result = await service.review_item(
        AsyncMock(),
        1,
        ReviewRequest(decision="rejected", memo="첨부 누락"),
        _actor(Role.admin),
    )

    assert item.status == ItemStatus.rejected
    assert result.decision == ApprovalDecision.rejected


async def test_review_item_when_not_submitted_raises_409() -> None:
    """pending 상태 항목을 검토하려 하면 INVALID_TRANSITION(api-spec §2-4)."""
    item = _item(ItemStatus.pending)
    case_repo = AsyncMock()
    case_repo.get_item.return_value = item
    service = _service(case_repo)

    with pytest.raises(InvalidStateError):
        await service.review_item(
            AsyncMock(), 1, ReviewRequest(decision="confirmed"), _actor(Role.admin)
        )
