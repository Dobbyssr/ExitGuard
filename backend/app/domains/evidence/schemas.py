"""evidence 도메인 Pydantic DTO. api-spec §2-5 · data-model §3-4."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domains.evidence.models import EvidenceEventType, EvidenceOrigin


class EvidenceCreate(BaseModel):
    """수동 보충 봉인 요청(CM-12, `origin=manual`)."""

    action: str
    actor: str
    event_type: EvidenceEventType
    document_ref: str | None = None
    payload: dict


class EvidenceResponse(BaseModel):
    """봉인된 증적 1건 — ORM에서 그대로 매핑(가공 없음)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    seq: int
    occurred_at: datetime
    actor: str
    action: str
    event_type: EvidenceEventType
    origin: EvidenceOrigin
    document_ref: str | None
    payload: dict
    integrity_hash: str
    prev_hash: str | None
    sealed_at: datetime
