"""evidence 라우터 — 얇게: 검증→서비스 호출→예외 번역→응답 변환(api-spec §2-5)."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.core.schemas import Envelope, Meta
from app.db import get_db
from app.domains.evidence.dependencies import get_evidence_service
from app.domains.evidence.schemas import DefenseReport, EvidenceCreate, EvidenceResponse
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


@router.get(
    "/cases/{case_id}/evidence/export",
    response_model=Envelope[DefenseReport],
)
async def export_report(
    case_id: int,
    format: Literal["json", "pdf"] = "json",
    db: AsyncSession = Depends(get_db),
    service: EvidenceService = Depends(get_evidence_service),
) -> Envelope[DefenseReport]:
    """방어 리포트 Export(CM-13, B1) — `GET /cases/{id}/evidence/export`.

    `format=pdf`는 MVP 범위 밖(도비 브리프 — 억지 구현 금지, ponytail). FE는 `format=json`
    응답을 그대로 렌더할 수 있어 501로 명시적 미구현을 알린다(api-spec 에러표에 없는
    코드라 `NOT_IMPLEMENTED`로 표기 — 신설 코드 필요 시 헤르미온느 확인 대상).
    """
    if format == "pdf":
        raise HTTPException(
            501,
            detail={
                "code": "NOT_IMPLEMENTED",
                "message": "PDF 내보내기는 아직 지원하지 않습니다. format=json으로 조회하세요",
                "fields": None,
            },
        )
    try:
        report = await service.export_report(db, case_id)
    except NotFoundError as exc:
        raise HTTPException(
            404, detail={"code": "NOT_FOUND", "message": exc.message, "fields": None}
        ) from exc
    return Envelope(data=report)
