"""compare 도메인 Pydantic DTO. data-model §6(shape)·§6-4(seam 계약) · api-spec §2-3·§1-6·§1-7.

shape는 코어 계약 그대로 — 레일 규칙(노무)만 이 값들을 채운다(compare/service.py).
"""

import enum
from datetime import date

from pydantic import BaseModel, Field

from app.core.schemas import Badge
from app.domains.case.models import ExitReason
from app.domains.shared.enums import Rail

# --- ① LLM 단계(seam) 출력 계약 — signal_extractor.py가 이 shape로 낸다(§6-4 ①) ---


class Signal(BaseModel):
    """폐집합 라벨 신호 1건. `evidence_span`은 반드시 reason_text의 부분문자열이어야 한다."""

    label: str
    evidence_span: str
    confidence: float


class QuotedSnippet(BaseModel):
    """공개 기준 "인용"만(생성 아님) — 지금 구현은 규칙기반이라 항상 빈 배열."""

    text: str
    source_ref: int | None = None


class SignalExtraction(BaseModel):
    """LLM(지금은 규칙기반 스텁) 단계 출력. 결정론 단계가 화이트리스트 검증 후 소비한다."""

    signals: list[Signal] = Field(default_factory=list)
    quoted_snippets: list[QuotedSnippet] = Field(default_factory=list)


# --- ② 결정론 단계 입출력 — CompareInput/CompareResult(§6-1·§6-2, 3레일 공용 shape) ---


class CaseFacts(BaseModel):
    """대조 대상 케이스 사실(§6-1) — 신호 추출 원천."""

    reason_text: str | None = None
    exit_reason: ExitReason
    exit_date: date
    job: str
    rank: str


class ItemContext(BaseModel):
    """대조 대상 항목/기준(선택 — 인테이크는 없이 신호 스캔, §6-1)."""

    code: str | None = None
    name: str | None = None
    standard_refs: list[int] = Field(default_factory=list)


class CompareInput(BaseModel):
    """`POST /compare` 요청 shape(§6-1)."""

    rail: Rail
    subject: str
    case_facts: CaseFacts
    item_context: ItemContext | None = None


class CompareRowKind(str, enum.Enum):
    """대조결과 행 종류(§2-7) — 5행 고정 순서."""

    procedure = "procedure"
    standard = "standard"
    risk = "risk"
    status = "status"
    source = "source"


#: rows 배열의 고정 순서(§6-2 "정확히 5행, kind 순서 고정"). 조립 코드가 이 순서를 어기면
#: 계약 위반이라 테스트가 이 상수와 나란히 검증한다.
COMPARE_ROW_KIND_ORDER: tuple[CompareRowKind, ...] = (
    CompareRowKind.procedure,
    CompareRowKind.standard,
    CompareRowKind.risk,
    CompareRowKind.status,
    CompareRowKind.source,
)


class CompareRow(BaseModel):
    """대조결과 행 1개 — kind별 text(+source 행만 url)."""

    kind: CompareRowKind
    text: str
    url: str | None = None


class CompareResult(BaseModel):
    """`POST /compare` 응답 shape(§6-2) — 5행 고정 + unmet_count + badges + boundary_notice."""

    rail: Rail
    subject: str
    rows: list[CompareRow]
    unmet_count: int
    badges: list[Badge]
    boundary_notice: str
    expert_referral: bool | None = None
