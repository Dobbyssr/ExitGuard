"""case 라우터 — 얇게: 검증→서비스 호출→예외 번역→응답 변환(api-spec §2-1·§2-2·§2-4)."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin, get_current_user
from app.core.schemas import Badge, Envelope, Meta, Pagination
from app.db import get_db
from app.domains.case.dependencies import get_case_service
from app.domains.case.models import Case, CaseStatus, Item
from app.domains.case.schemas import (
    ApprovalCreate,
    ApprovalResponse,
    ApproveRequest,
    ApproveResponseData,
    CaseCreate,
    CaseDetailResponse,
    CaseResponse,
    CaseSummaryResponse,
    GateResponse,
    ItemResponse,
    RailSummary,
    ReviewRequest,
)
from app.domains.case.service import CaseDetail, CaseService, GateComputation
from app.domains.catalog.models import Standard
from app.domains.evidence.schemas import EvidenceResponse
from app.domains.shared.enums import Rail
from app.domains.shared.exceptions import InvalidStateError, NotFoundError
from app.domains.user.models import User

router = APIRouter(tags=["case"])


def _not_found(exc: NotFoundError) -> HTTPException:
    return HTTPException(
        404, detail={"code": "NOT_FOUND", "message": exc.message, "fields": None}
    )


def _invalid_transition(exc: InvalidStateError) -> HTTPException:
    return HTTPException(
        409,
        detail={
            "code": "INVALID_TRANSITION",
            "message": exc.message,
            "fields": exc.fields,
        },
    )


def _build_item_response(
    item: Item, standards_by_id: dict[int, Standard]
) -> ItemResponse:
    """Item ORM + standard_ids → badges 조립(api-spec §1-6)."""
    badges = [
        Badge(
            tier=standards_by_id[sid].tier,
            title=standards_by_id[sid].title,
            url=standards_by_id[sid].source_url,
            version=standards_by_id[sid].version,
        )
        for sid in (item.standard_ids or [])
        if sid in standards_by_id
    ]
    return ItemResponse(
        id=item.id,
        case_id=item.case_id,
        rail=item.rail,
        code=item.code,
        name=item.name,
        kind=item.kind,
        status=item.status,
        blocking=item.blocking,
        sub=item.sub,
        deadline=item.deadline,
        detail=item.detail,
        badges=badges,
    )


def _build_gate_response(case_id: int, gate: GateComputation) -> GateResponse:
    return GateResponse(
        case_id=case_id,
        rail_completion=gate.rail_completion,
        overall_completion=gate.overall_completion,
        risk_count=gate.risk_count,
        defensible=gate.defensible,
    )


def _build_case_detail_response(detail: CaseDetail) -> CaseDetailResponse:
    items_by_rail: dict[Rail, list[ItemResponse]] = {rail: [] for rail in Rail}
    for item in detail.items:
        items_by_rail[item.rail].append(
            _build_item_response(item, detail.standards_by_id)
        )
    rails = {
        rail.value: RailSummary(
            rail=rail,
            completion=detail.gate.rail_completion[rail],
            items=items_by_rail[rail],
        )
        for rail in Rail
    }
    return CaseDetailResponse(
        case=CaseResponse.model_validate(detail.case),
        gate=_build_gate_response(detail.case.id, detail.gate),
        rails=rails,
        items=[item for items in items_by_rail.values() for item in items],
    )


def _build_case_summary(case: Case, gate: GateComputation) -> CaseSummaryResponse:
    dday = (case.exit_date - date.today()).days
    return CaseSummaryResponse(
        id=case.id,
        subject_name=case.subject_name,
        subject_job=case.subject_job,
        subject_rank=case.subject_rank,
        exit_reason=case.exit_reason,
        exit_date=case.exit_date,
        status=case.status,
        overall_completion=gate.overall_completion,
        risk_count=gate.risk_count,
        dday=dday,
    )


@router.post("/cases", response_model=Envelope[CaseDetailResponse], status_code=201)
async def create_case(
    payload: CaseCreate,
    db: AsyncSession = Depends(get_db),
    service: CaseService = Depends(get_case_service),
    actor: User = Depends(get_current_user),
) -> Envelope[CaseDetailResponse]:
    """케이스 접수(CM-04) — `POST /cases`."""
    case = await service.create_case(db, payload, actor)
    detail = await service.get_case_detail(db, case.id)
    return Envelope(
        data=_build_case_detail_response(detail),
        meta=Meta(toast=f"✓ {case.subject_name} 케이스가 등록되었습니다"),
    )


@router.get("/cases", response_model=Envelope[list[CaseSummaryResponse]])
async def list_cases(
    filter: Literal["all", "in_progress", "review_waiting", "completed"] = "all",
    q: str | None = None,
    sort: str = "default",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    service: CaseService = Depends(get_case_service),
) -> Envelope[list[CaseSummaryResponse]]:
    """케이스 목록(CM-03) — `GET /cases`."""
    status_filter = None if filter == "all" else CaseStatus(filter)
    pairs, total = await service.list_cases(
        db, status_filter=status_filter, q=q, sort=sort, page=page, size=size
    )
    total_pages = max(1, -(-total // size))
    return Envelope(
        data=[_build_case_summary(case, gate) for case, gate in pairs],
        meta=Meta(
            pagination=Pagination(
                page=page, size=size, total=total, total_pages=total_pages
            )
        ),
    )


@router.get("/cases/{case_id}", response_model=Envelope[CaseDetailResponse])
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    service: CaseService = Depends(get_case_service),
) -> Envelope[CaseDetailResponse]:
    """케이스 상세(CM-07) — `GET /cases/{id}`."""
    try:
        detail = await service.get_case_detail(db, case_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc
    return Envelope(data=_build_case_detail_response(detail))


@router.get("/cases/{case_id}/gate", response_model=Envelope[GateResponse])
async def get_gate(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    service: CaseService = Depends(get_case_service),
) -> Envelope[GateResponse]:
    """통합 게이트 집계(CM-08) — `GET /cases/{id}/gate`."""
    try:
        gate = await service.get_gate(db, case_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc
    return Envelope(data=_build_gate_response(case_id, gate))


@router.post("/cases/{case_id}/approve", response_model=Envelope[ApproveResponseData])
async def approve_case(
    case_id: int,
    payload: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    service: CaseService = Depends(get_case_service),
    actor: User = Depends(get_current_admin),
) -> Envelope[ApproveResponseData]:
    """퇴사 승인 확정(CM-08, T3) — `POST /cases/{id}/approve`."""
    try:
        case, evidence = await service.approve_case(db, case_id, payload, actor)
    except NotFoundError as exc:
        raise _not_found(exc) from exc
    except InvalidStateError as exc:
        raise _invalid_transition(exc) from exc
    return Envelope(
        data=ApproveResponseData(
            case=CaseResponse.model_validate(case),
            evidence=EvidenceResponse.model_validate(evidence),
        ),
        meta=Meta(toast="✓ 방어 가능 상태로 승인되었습니다"),
    )


@router.post("/items/{item_id}/submit", response_model=Envelope[ApprovalResponse])
async def submit_item(
    item_id: int,
    payload: ApprovalCreate,
    db: AsyncSession = Depends(get_db),
    service: CaseService = Depends(get_case_service),
    actor: User = Depends(get_current_user),
) -> Envelope[ApprovalResponse]:
    """상신(CM-10) — `POST /items/{id}/submit`."""
    try:
        approval = await service.submit_item(db, item_id, payload, actor)
    except NotFoundError as exc:
        raise _not_found(exc) from exc
    except InvalidStateError as exc:
        raise _invalid_transition(exc) from exc
    return Envelope(data=ApprovalResponse.model_validate(approval))


@router.post("/items/{item_id}/review", response_model=Envelope[ApprovalResponse])
async def review_item(
    item_id: int,
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    service: CaseService = Depends(get_case_service),
    actor: User = Depends(get_current_admin),
) -> Envelope[ApprovalResponse]:
    """검토(CM-10) — `POST /items/{id}/review`."""
    try:
        approval = await service.review_item(db, item_id, payload, actor)
    except NotFoundError as exc:
        raise _not_found(exc) from exc
    except InvalidStateError as exc:
        raise _invalid_transition(exc) from exc
    return Envelope(data=ApprovalResponse.model_validate(approval))
