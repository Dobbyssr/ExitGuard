"""compare 라우터 — 얇게(api-spec §2-3). 검증→서비스 호출→예외 번역→응답 변환."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.schemas import Envelope
from app.db import get_db
from app.domains.compare.dependencies import get_compare_service
from app.domains.compare.schemas import CompareInput, CompareResult
from app.domains.compare.service import CompareService
from app.domains.shared.exceptions import CompareFailedError, NotFoundError
from app.domains.user.models import User

router = APIRouter(tags=["compare"])


def _compare_failed(exc: CompareFailedError) -> HTTPException:
    return HTTPException(
        422,
        detail={"code": "COMPARE_FAILED", "message": exc.message, "fields": exc.fields},
    )


@router.post("/compare", response_model=Envelope[CompareResult])
async def compare(
    payload: CompareInput,
    db: AsyncSession = Depends(get_db),
    service: CompareService = Depends(get_compare_service),
) -> Envelope[CompareResult]:
    """공용 대조 호출(CM-05/LB-04/TS-05) — `POST /compare`."""
    try:
        result = await service.compare(db, payload)
    except CompareFailedError as exc:
        raise _compare_failed(exc) from exc
    return Envelope(data=result)


@router.post(
    "/cases/{case_id}/intake-compare",
    response_model=Envelope[CompareResult],
)
async def intake_compare(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    service: CompareService = Depends(get_compare_service),
    actor: User = Depends(get_current_user),
) -> Envelope[CompareResult]:
    """인테이크 대조 래퍼(CM-05) — `POST /cases/{id}/intake-compare`."""
    try:
        result = await service.intake_compare(db, case_id, actor)
    except NotFoundError as exc:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": exc.message, "fields": None}
        ) from exc
    except CompareFailedError as exc:
        raise _compare_failed(exc) from exc
    return Envelope(data=result)
