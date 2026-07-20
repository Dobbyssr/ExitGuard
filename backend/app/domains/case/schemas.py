"""case 도메인 Pydantic DTO. api-spec §2-1·§2-2·§2-4 · data-model §3-1~§3-3·§5."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.schemas import Badge
from app.domains.case.models import (
    ApprovalDecision,
    CaseStatus,
    ExitReason,
    IntakeRoute,
    ItemKind,
    ItemStatus,
)
from app.domains.evidence.schemas import EvidenceResponse
from app.domains.shared.enums import Rail


class CaseCreate(BaseModel):
    """케이스 접수 요청(CM-04) — `POST /cases`."""

    subject_name: str
    subject_job: str
    subject_rank: str
    subject_role_title: str | None = None
    exit_reason: ExitReason
    reason_text: str | None = None
    exit_date: date
    intake_route: IntakeRoute
    profile_id: int | None = None


class CaseResponse(BaseModel):
    """케이스 원본 필드 — Case ORM에서 그대로 매핑."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_name: str
    subject_job: str
    subject_rank: str
    subject_role_title: str | None
    exit_reason: ExitReason
    reason_text: str | None
    exit_date: date
    intake_route: IntakeRoute
    profile_id: int | None
    status: CaseStatus
    created_by: int
    created_at: datetime
    updated_at: datetime


class GateResponse(BaseModel):
    """통합 게이트 집계 — 결정론적 파생, 저장 아님(data-model §5)."""

    case_id: int
    rail_completion: dict[Rail, int]
    overall_completion: int
    risk_count: int
    defensible: bool


class ItemResponse(BaseModel):
    """검사항목 + 근거 배지(§3-2). badges는 standard_ids를 조회해 조립하므로 수동 구성."""

    id: int
    case_id: int
    rail: Rail
    code: str
    name: str
    kind: ItemKind
    status: ItemStatus
    blocking: bool
    sub: str | None
    deadline: date | None
    detail: dict | None
    badges: list[Badge]


class RailSummary(BaseModel):
    """케이스 상세의 `rails.<rail>` 뼈대 응답(§3 Phase 0 — completion+items만)."""

    rail: Rail
    completion: int
    items: list[ItemResponse]


class CaseDetailResponse(BaseModel):
    """케이스 상세(CM-07) — `GET /cases/{id}` · `POST /cases` 201 응답 공용."""

    case: CaseResponse
    gate: GateResponse
    rails: dict[str, RailSummary]
    items: list[ItemResponse]


class CaseSummaryResponse(BaseModel):
    """케이스 목록(CM-03) 1건 — gate 요약 + D-day."""

    id: int
    subject_name: str
    subject_job: str
    subject_rank: str
    exit_reason: ExitReason
    exit_date: date
    status: CaseStatus
    overall_completion: int
    risk_count: int
    dday: int


class AttachmentSchema(BaseModel):
    """상신 첨부 메타 — api-spec §2-4 예시대로 size는 표시용 문자열."""

    name: str
    size: str


class ApprovalCreate(BaseModel):
    """상신 요청(CM-10) — `POST /items/{id}/submit`."""

    memo: str | None = None
    attachments: list[AttachmentSchema] | None = None
    signed: bool = False


class ApprovalResponse(BaseModel):
    """상신-검토 레코드 — ORM에서 그대로 매핑."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    submitter_id: int
    memo: str | None
    attachments: list[dict] | None
    signed: bool
    basis_note: str | None
    reviewer_id: int | None
    decision: ApprovalDecision | None
    reviewed_at: datetime | None
    submitted_at: datetime


class ReviewRequest(BaseModel):
    """검토 요청(CM-10) — `POST /items/{id}/review`."""

    decision: Literal["confirmed", "rejected"]
    memo: str | None = None


class ApproveRequest(BaseModel):
    """승인 확정 요청(T3) — `POST /cases/{id}/approve`."""

    memo: str | None = None


class ApproveResponseData(BaseModel):
    """승인 확정 응답 — 갱신된 케이스 + 봉인된 증적."""

    case: CaseResponse
    evidence: EvidenceResponse
