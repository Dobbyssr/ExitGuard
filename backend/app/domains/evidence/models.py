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

    id: Mapped[int] = mapped_column(primary_key=True)
    # 별도 index=True를 달지 않는다 — 위 UNIQUE(case_id, seq)가 case_id 단독 조회도
    # 리딩 컬럼으로 이미 커버하는 복합 인덱스라 중복 인덱스가 된다.
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    seq: Mapped[int] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    event_type: Mapped[EvidenceEventType] = mapped_column(
        SAEnum(EvidenceEventType, native_enum=False, create_constraint=True)
    )
    origin: Mapped[EvidenceOrigin] = mapped_column(
        SAEnum(EvidenceOrigin, native_enum=False, create_constraint=True)
    )
    document_ref: Mapped[str | None] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSONB)
    integrity_hash: Mapped[str] = mapped_column(String)
    prev_hash: Mapped[str | None] = mapped_column(String)
    sealed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
