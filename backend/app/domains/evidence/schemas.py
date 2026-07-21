"""evidence 도메인 Pydantic DTO. api-spec §2-5 · data-model §3-4·§10(DefenseReport)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.schemas import Badge
from app.domains.case.models import CaseStatus, ExitReason
from app.domains.compare.schemas import CompareRow
from app.domains.evidence.models import EvidenceEventType, EvidenceOrigin
from app.domains.shared.enums import Rail


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


# --- 방어 리포트(DefenseReport) — 파생 뷰, 저장 없음(data-model §10 · CM-13/B1) ---


class DefenseReportCase(BaseModel):
    """리포트용 케이스 요약 — Case 원본의 부분집합(§10)."""

    id: int
    subject_name: str
    subject_job: str
    subject_rank: str
    exit_reason: ExitReason
    exit_date: date
    status: CaseStatus


class DefenseReportKpi(BaseModel):
    """게이트 파생 KPI(§10) — 봉인된 `case_approved` 스냅샷 우선 인용, 없으면 §5 라이브 계산."""

    overall_completion: int
    rail_completion: dict[Rail, int]
    risk_count: int
    defensible: bool


class DefenseReportRailSummary(BaseModel):
    """3레일 요약 — 완료율·미충족건수·근거배지(§10)."""

    rail: Rail
    completion: int
    unmet_count: int
    badges: list[Badge]


class DefenseReportCompareFinding(BaseModel):
    """봉인된 `compare_recorded` 스냅샷 인용(§3-4-1) — 재계산·환각 없음(§10)."""

    rail: Rail
    subject: str
    rows: list[CompareRow]
    unmet_count: int
    badges: list[Badge]
    boundary_notice: str
    sealed_seq: int


class DefenseReportEvidenceEntry(BaseModel):
    """증적 체인 엔트리 요약(§10)."""

    seq: int
    occurred_at: datetime
    actor: str
    action: str
    event_type: EvidenceEventType
    integrity_hash: str


class DefenseReportEvidenceChain(BaseModel):
    """증적 체인 요약 — `head_hash`가 위변조 검증 앵커(§10)."""

    total_count: int
    seal_status: Literal["sealed", "accruing"]
    first_seq: int
    last_seq: int
    head_hash: str | None
    entries: list[DefenseReportEvidenceEntry]


class DefenseReport(BaseModel):
    """방어 리포트 뷰(CM-13, B1) — 봉인 증적·게이트·compare 스냅샷의 파생 뷰. 저장 없음(§10)."""

    case: DefenseReportCase
    generated_at: datetime
    kpi: DefenseReportKpi
    rails: list[DefenseReportRailSummary]
    compare_findings: list[DefenseReportCompareFinding]
    evidence_chain: DefenseReportEvidenceChain
    boundary_notice: str
