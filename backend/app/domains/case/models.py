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

    id: Mapped[int] = mapped_column(primary_key=True, comment="PK")
    subject_name: Mapped[str] = mapped_column(String, comment="대상자(퇴사자) 이름")
    subject_job: Mapped[str] = mapped_column(String, comment="직무/직종")
    subject_rank: Mapped[str] = mapped_column(String, comment="직급")
    subject_role_title: Mapped[str | None] = mapped_column(
        String, comment="직책/역할명"
    )
    exit_reason: Mapped[ExitReason] = mapped_column(
        SAEnum(ExitReason, native_enum=False, create_constraint=True),
        comment="퇴사 사유유형(voluntary/recommended_resignation/dismissal/contract_expiry)",
    )
    reason_text: Mapped[str | None] = mapped_column(
        String, comment="회사사유 입력 텍스트(대조 엔진 입력원)"
    )
    exit_date: Mapped[date] = mapped_column(Date, comment="퇴직 예정일(기한 계산 기준)")
    intake_route: Mapped[IntakeRoute] = mapped_column(
        SAEnum(IntakeRoute, native_enum=False, create_constraint=True),
        comment="케이스 접수경로(groupware/dismissal/resignation)",
    )
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id"),
        index=True,
        comment="적용 프로파일 FK(직무·직급→항목 자동배정)",
    )
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus, native_enum=False, create_constraint=True),
        default=CaseStatus.in_progress,
        comment="케이스 진행상태(in_progress/review_waiting/completed)",
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, comment="접수 담당자 FK(User)"
    )

    items: Mapped[list["Item"]] = relationship(back_populates="case")


class Item(Base, TimestampMixin):
    """검사항목 — Case가 3레일에 걸쳐 관리하는 개별 대조 대상. §3-2."""

    __tablename__ = "items"
    __table_args__ = (Index("ix_items_case_id_status", "case_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True, comment="PK")
    # case_id 단독 인덱스는 두지 않는다 — 아래 복합 (case_id, status)의 리딩 컬럼이
    # case_id 단독 조회를 이미 커버하므로 별도 단일 인덱스는 순수 중복(스네이프 round2).
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id"), comment="소속 케이스 FK"
    )
    rail: Mapped[Rail] = mapped_column(
        SAEnum(Rail, native_enum=False, create_constraint=True),
        comment="소속 레일(labor/trade_secret/security)",
    )
    code: Mapped[str] = mapped_column(String, comment="항목코드(레일 접두어 L-/S-/C-)")
    name: Mapped[str] = mapped_column(String, comment="항목명")
    kind: Mapped[ItemKind] = mapped_column(
        SAEnum(ItemKind, native_enum=False, create_constraint=True),
        comment="항목 구분(statutory/internal/recommended)",
    )
    status: Mapped[ItemStatus] = mapped_column(
        SAEnum(ItemStatus, native_enum=False, create_constraint=True),
        default=ItemStatus.pending,
        comment="검사항목 상태(pending/submitted/approved/rejected/not_applicable)",
    )
    blocking: Mapped[bool] = mapped_column(Boolean, comment="게이트 차단 여부")
    sub: Mapped[str | None] = mapped_column(String, comment="진행 요약 한 줄")
    deadline: Mapped[date | None] = mapped_column(
        Date, comment="법정 기한일(있는 경우)"
    )
    # ponytail: standard_ids는 JSONB int 배열(조인테이블 없이 MVP 단순화).
    # M2M 정규화 여부는 스네이프 DB감수에서 판정.
    standard_ids: Mapped[list[int] | None] = mapped_column(
        JSONB, comment="근거 배지(Standard.id 목록)"
    )
    detail: Mapped[dict | None] = mapped_column(
        JSONB,
        comment="레일별 상세 필드(노무 기한요소/영업비밀 자산요소/보안 회수대상)",
    )

    case: Mapped["Case"] = relationship(back_populates="items")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="item")


class Approval(Base):
    """상신-검토 레코드. 항목별 재상신 시 N개 누적. §3-3."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, comment="PK")
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id"), index=True, comment="대상 항목 FK"
    )
    submitter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, comment="상신자(담당자) FK"
    )
    memo: Mapped[str | None] = mapped_column(String, comment="상신 메모")
    attachments: Mapped[list[dict] | None] = mapped_column(
        JSONB, comment="첨부 문서 목록({name,size})"
    )
    signed: Mapped[bool] = mapped_column(Boolean, comment="전자서명 여부")
    basis_note: Mapped[str | None] = mapped_column(String, comment="기준 근거 문구")
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, comment="검토자(관리자) FK"
    )
    decision: Mapped[ApprovalDecision | None] = mapped_column(
        SAEnum(ApprovalDecision, native_enum=False, create_constraint=True),
        comment="검토 결과(confirmed/rejected, 미검토 시 null)",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="검토 일시"
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="상신 일시"
    )

    item: Mapped["Item"] = relationship(back_populates="approvals")
