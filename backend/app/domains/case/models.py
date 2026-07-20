"""case 도메인 — 퇴사 케이스(Case)·검사항목(Item)·상신-검토 레코드(Approval).

유비쿼터스 언어: '케이스' = 퇴사 1건이 3레일(노무/영업비밀/보안)을 관통하는 단위.
계약 SSOT: docs/spec/data-model.md §3-1~§3-3(엔티티) · §4(Item 상태머신) · §3-1-1(Case 상태전이).
이번 단계는 코어 모델만 — 상태전이·게이트 집계 등은 다음 단계 서비스 로직(§8 도메인 메서드 위치).
"""

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin
from app.domains.shared.enums import ItemKind, Rail


class ExitReason(str, enum.Enum):
    """퇴사 사유유형 4종(§2-2)."""

    voluntary = "voluntary"
    recommended_resignation = "recommended_resignation"
    dismissal = "dismissal"
    contract_expiry = "contract_expiry"


class IntakeRoute(str, enum.Enum):
    """케이스 접수 경로 3종(CM-04)."""

    groupware = "groupware"
    dismissal = "dismissal"
    resignation = "resignation"


class CaseStatus(str, enum.Enum):
    """케이스 진행 상태(§3-1-1 상태전이)."""

    in_progress = "in_progress"
    review_waiting = "review_waiting"
    completed = "completed"


class ItemStatus(str, enum.Enum):
    """검사항목 상태머신(§4)."""

    pending = "pending"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    not_applicable = "not_applicable"


class ApprovalDecision(str, enum.Enum):
    """검토 결과 — 미검토는 null(§3-3)."""

    confirmed = "confirmed"
    rejected = "rejected"


class Case(Base, TimestampMixin):
    """퇴사 케이스 1건. 3레일 Item을 자식으로 가진다. Gate(§5)는 저장 없이 파생. §3-1."""

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_name: Mapped[str] = mapped_column(String)
    subject_job: Mapped[str] = mapped_column(String)
    subject_rank: Mapped[str] = mapped_column(String)
    subject_role_title: Mapped[str | None] = mapped_column(String)
    exit_reason: Mapped[ExitReason] = mapped_column(
        SAEnum(ExitReason, native_enum=False, create_constraint=True)
    )
    reason_text: Mapped[str | None] = mapped_column(String)
    exit_date: Mapped[date] = mapped_column(Date)
    intake_route: Mapped[IntakeRoute] = mapped_column(
        SAEnum(IntakeRoute, native_enum=False, create_constraint=True)
    )
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id"), index=True
    )
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus, native_enum=False, create_constraint=True),
        default=CaseStatus.in_progress,
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    items: Mapped[list["Item"]] = relationship(back_populates="case")


class Item(Base, TimestampMixin):
    """검사항목 — Case가 3레일에 걸쳐 관리하는 개별 대조 대상. §3-2."""

    __tablename__ = "items"
    __table_args__ = (Index("ix_items_case_id_status", "case_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # case_id 단독 인덱스는 두지 않는다 — 아래 복합 (case_id, status)의 리딩 컬럼이
    # case_id 단독 조회를 이미 커버하므로 별도 단일 인덱스는 순수 중복(스네이프 round2).
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    rail: Mapped[Rail] = mapped_column(
        SAEnum(Rail, native_enum=False, create_constraint=True)
    )
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    kind: Mapped[ItemKind] = mapped_column(
        SAEnum(ItemKind, native_enum=False, create_constraint=True)
    )
    status: Mapped[ItemStatus] = mapped_column(
        SAEnum(ItemStatus, native_enum=False, create_constraint=True),
        default=ItemStatus.pending,
    )
    blocking: Mapped[bool] = mapped_column(Boolean)
    sub: Mapped[str | None] = mapped_column(String)
    deadline: Mapped[date | None] = mapped_column(Date)
    # ponytail: standard_ids는 JSONB int 배열(조인테이블 없이 MVP 단순화).
    # M2M 정규화 여부는 스네이프 DB감수에서 판정.
    standard_ids: Mapped[list[int] | None] = mapped_column(JSONB)
    detail: Mapped[dict | None] = mapped_column(JSONB)

    case: Mapped["Case"] = relationship(back_populates="items")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="item")


class Approval(Base):
    """상신-검토 레코드. 항목별 재상신 시 N개 누적. §3-3."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    submitter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    memo: Mapped[str | None] = mapped_column(String)
    attachments: Mapped[list[dict] | None] = mapped_column(JSONB)
    signed: Mapped[bool] = mapped_column(Boolean)
    basis_note: Mapped[str | None] = mapped_column(String)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    decision: Mapped[ApprovalDecision | None] = mapped_column(
        SAEnum(ApprovalDecision, native_enum=False, create_constraint=True)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    item: Mapped["Item"] = relationship(back_populates="approvals")
