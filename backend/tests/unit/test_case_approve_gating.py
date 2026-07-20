"""Case.approve 승인조건(data-model §3-1-1) — service+Mock repo 유닛 테스트."""

from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.domains.case.models import Case, CaseStatus, Item, ItemStatus
from app.domains.case.schemas import ApproveRequest
from app.domains.case.service import CaseService
from app.domains.shared.enums import ItemKind, Rail
from app.domains.shared.exceptions import InvalidStateError
from app.domains.user.models import Role, User


def _item(status: ItemStatus, blocking: bool = True) -> Item:
    return Item(
        case_id=1,
        rail=Rail.labor,
        code="L-01",
        name="테스트 항목",
        kind=ItemKind.statutory,
        status=status,
        blocking=blocking,
    )


def _case() -> Case:
    case = Case(
        subject_name="홍길동",
        subject_job="개발",
        subject_rank="사원",
        exit_reason="voluntary",
        exit_date=date(2026, 1, 1),
        intake_route="groupware",
        created_by=1,
    )
    case.id = 1
    case.status = CaseStatus.in_progress
    return case


def _admin() -> User:
    user = User(name="관리자", email="admin@test.example", role=Role.admin)
    user.id = 1
    return user


async def test_approve_case_when_all_resolved_transitions_to_completed() -> None:
    """defensible=true·submitted=0 → 승인 성공 + case_approved 자동봉인."""
    items = [_item(ItemStatus.approved), _item(ItemStatus.not_applicable)]
    case_repo = AsyncMock()
    case_repo.get_case.return_value = _case()
    case_repo.get_items_by_case.return_value = items
    evidence_repo = AsyncMock()
    service = CaseService(case_repo, AsyncMock(), evidence_repo)

    case, evidence = await service.approve_case(
        AsyncMock(), 1, ApproveRequest(), _admin()
    )

    assert case.status == CaseStatus.completed
    evidence_repo.append.assert_awaited_once()
    _, kwargs = evidence_repo.append.await_args
    assert kwargs["payload"]["risk_count"] == 0
    assert kwargs["payload"]["defensible"] is True


async def test_approve_case_when_risk_unresolved_raises_409_with_fields() -> None:
    """defensible=false(미해소 blocking 리스크) → 거부 + risk_count/submitted_count 포함."""
    items = [_item(ItemStatus.pending)]  # blocking=True, 미충족 → risk_count=1
    case_repo = AsyncMock()
    case_repo.get_case.return_value = _case()
    case_repo.get_items_by_case.return_value = items
    service = CaseService(case_repo, AsyncMock(), AsyncMock())

    with pytest.raises(InvalidStateError) as exc_info:
        await service.approve_case(AsyncMock(), 1, ApproveRequest(), _admin())

    assert exc_info.value.fields == {"risk_count": 1, "submitted_count": 0}


async def test_approve_case_when_submitted_pending_review_raises_409() -> None:
    """defensible=true(risk_count=0)이어도 submitted 항목이 남아있으면 거부(우회 승인 없음)."""
    items = [
        _item(ItemStatus.submitted, blocking=False)
    ]  # non-blocking이라 risk_count엔 안 잡힘
    case_repo = AsyncMock()
    case_repo.get_case.return_value = _case()
    case_repo.get_items_by_case.return_value = items
    service = CaseService(case_repo, AsyncMock(), AsyncMock())

    with pytest.raises(InvalidStateError) as exc_info:
        await service.approve_case(AsyncMock(), 1, ApproveRequest(), _admin())

    assert exc_info.value.fields == {"risk_count": 0, "submitted_count": 1}
