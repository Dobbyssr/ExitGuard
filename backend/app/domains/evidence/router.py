"""evidence 라우터 — 얇게: 검증→서비스 호출→예외 번역→응답 변환(api-spec §2-5)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.core.schemas import Envelope, Meta
from app.db import get_db
from app.domains.evidence.dependencies import get_evidence_service
from app.domains.evidence.schemas import EvidenceCreate, EvidenceResponse
from app.domains.evidence.service import EvidenceService
from app.domains.shared.exceptions import NotFoundError
from app.domains.user.models import User

router = APIRouter(tags=["evidence"])


@router.post(
    "/cases/{case_id}/evidence",
    response_model=Envelope[EvidenceResponse],
    status_code=201,
)
async def create_manual_evidence(
    case_id: int,
    payload: EvidenceCreate,
    db: AsyncSession = Depends(get_db),
    service: EvidenceService = Depends(get_evidence_service),
    _admin: User = Depends(get_current_admin),
) -> Envelope[EvidenceResponse]:
    """수동 보충 봉인(CM-12) — `POST /cases/{id}/evidence`."""
    try:
        evidence = await service.manual_seal(db, case_id, payload)
    except NotFoundError as exc:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": exc.message, "fields": None}
        ) from exc
    return Envelope(data=EvidenceResponse.model_validate(evidence))


@router.get(
    "/cases/{case_id}/evidence",
    response_model=Envelope[list[EvidenceResponse]],
)
async def list_evidence(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    service: EvidenceService = Depends(get_evidence_service),
) -> Envelope[list[EvidenceResponse]]:
    """증적 아카이브/봉인 뷰(CM-12/CM-14) — `GET /cases/{id}/evidence`."""
    try:
        entries, meta = await service.get_archive(db, case_id)
    except NotFoundError as exc:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": exc.message, "fields": None}
        ) from exc
    return Envelope(
        data=[EvidenceResponse.model_validate(e) for e in entries],
        meta=Meta(
            seal_status=meta.seal_status,
            total_count=meta.total_count,
            last_sealed_at=meta.last_sealed_at,
            head_hash=meta.head_hash,
        ),
    )
