"""evidence 도메인 — 증적(Evidence).

변경불가·append-only 봉인 레코드(data-model.md §3-4·§3-4-1). Case가 삭제되거나 어떤 삭제
경로를 거치더라도 봉인 증적은 소실되지 않는다(§0 삭제·보존 정책) — 그래서 UPDATE 대상인
created_at/updated_at을 두지 않고, FK는 CASCADE 없이 기본 NO ACTION(삭제 차단)으로 둔다.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EvidenceEventType(str, enum.Enum):
    """자동 봉인 트리거 이벤트 6종(§3-4-1)."""

    item_submitted = "item_submitted"
    item_confirmed = "item_confirmed"
    item_rejected = "item_rejected"
    compare_recorded = "compare_recorded"
    recovery_confirmed = "recovery_confirmed"
    case_approved = "case_approved"


class EvidenceOrigin(str, enum.Enum):
    """봉인 출처 — 이벤트 자동 봉인(auto)/수동 보충 봉인(manual)."""

    auto = "auto"
    manual = "manual"


class Evidence(Base):
    """증적 — 변경불가 봉인 레코드. UPDATE/DELETE 없이 append만 한다. §3-4."""

    __tablename__ = "evidence"
    __table_args__ = (
        # UNIQUE(case_id, seq) — 동시 append의 seq 중복·체인 분기를 IntegrityError로 드러낸다(§3-4-1).
        # 이 유니크 제약이 곧 (case_id, seq) 조회를 커버하는 복합 인덱스이므로 별도 인덱스는 두지 않는다.
        UniqueConstraint("case_id", "seq", name="uq_evidence_case_id_seq"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="PK")
    # 별도 index=True를 달지 않는다 — 위 UNIQUE(case_id, seq)가 case_id 단독 조회도
    # 리딩 컬럼으로 이미 커버하는 복합 인덱스라 중복 인덱스가 된다.
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id"), comment="소속 케이스 FK"
    )
    seq: Mapped[int] = mapped_column(
        Integer, comment="처리 순번(case 내 단조증가, 체인 순서 조회 키)"
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="처리 일시"
    )
    actor: Mapped[str] = mapped_column(String, comment="수행자")
    action: Mapped[str] = mapped_column(String, comment="처리 내용")
    event_type: Mapped[EvidenceEventType] = mapped_column(
        SAEnum(EvidenceEventType, native_enum=False, create_constraint=True),
        comment="봉인 트리거 이벤트 종류",
    )
    origin: Mapped[EvidenceOrigin] = mapped_column(
        SAEnum(EvidenceOrigin, native_enum=False, create_constraint=True),
        comment="봉인 출처(auto=이벤트 자동 봉인/manual=수동 보충 봉인)",
    )
    document_ref: Mapped[str | None] = mapped_column(String, comment="관련 문서명")
    payload: Mapped[dict] = mapped_column(JSONB, comment="봉인 대상 스냅샷")
    integrity_hash: Mapped[str] = mapped_column(
        String, comment="SHA-256 해시(payload 무결성)"
    )
    prev_hash: Mapped[str | None] = mapped_column(
        String, comment="직전 레코드 해시(체인 — 변경 탐지)"
    )
    sealed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="봉인 시각"
    )
