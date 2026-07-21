"""노무(labor) 레일 전용 모델 — 중노위 판정례 대조 코퍼스(`LaborPrecedent`).

코어 뼈대(Case/Item/Standard/enum)는 절대 재정의하지 않는다. 신설은 이 파일이 전부다:
`LaborPrecedent` + `LaborCaseType`·`LaborRequiredElement`·`LaborDeadlineRule` enum
(노무 data-model.md §4·§4-1·§5-1·§2-2). `LaborPrecedent`는 케이스 종속이 아닌 **참조 코퍼스**라
`case_id`가 없다(§4 주석 — TS의 TradeSecretAsset과 동일하게 "대조 대상 데이터"이지 검사항목이 아님).
"""

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class LaborCaseType(str, enum.Enum):
    """중노위 판정례 사건유형 18종 실측(CSV `자료구분`, §4-1)."""

    disciplinary_dismissal = "disciplinary_dismissal"
    unfair_labor_practice = "unfair_labor_practice"
    ordinary_dismissal = "ordinary_dismissal"
    term_expiry = "term_expiry"
    fair_representation = "fair_representation"
    other_discipline = "other_discipline"
    remedy_interest = "remedy_interest"
    managerial_dismissal = "managerial_dismissal"
    resignation = "resignation"
    party_standing = "party_standing"
    bargaining_rep = "bargaining_rep"
    bargaining_unit = "bargaining_unit"
    transfer = "transfer"
    bargaining_notice = "bargaining_notice"
    discrimination = "discrimination"
    ex_officio_dismissal = "ex_officio_dismissal"
    standby_order = "standby_order"
    suspension = "suspension"


# 해고계열(§4-1) — LB-04 코퍼스 필터 대상. 노조·교섭·전보 등은 퇴사 개인 케이스와 무관해 제외.
DISMISSAL_CASE_TYPES: tuple[LaborCaseType, ...] = (
    LaborCaseType.disciplinary_dismissal,
    LaborCaseType.ordinary_dismissal,
    LaborCaseType.managerial_dismissal,
    LaborCaseType.ex_officio_dismissal,
)


class LaborRequiredElement(str, enum.Enum):
    """판정 요구 요소(§5-1) — LLM 신호추출·compare 매핑의 폐집합 어휘.

    MVP는 `written_notice` 단일 요소만 실제 대조한다(§5-1). `just_cause`(정당한 이유)는
    "정당성 판단"에 근접해 직역법상 MVP 제외 — enum에는 올려 두되 화이트리스트에는 넣지 않는다.
    """

    written_notice = "written_notice"
    dismissal_notice = "dismissal_notice"
    just_cause = "just_cause"


class LaborDeadlineRule(str, enum.Enum):
    """법정 기한 규칙(§2-2) — `Item.detail.deadline_rule`(rail=labor)이 갖는 값."""

    settlement_14d = "settlement_14d"
    dismissal_notice_30d = "dismissal_notice_30d"
    written_notice = "written_notice"
    separation_cert = "separation_cert"
    insurance_loss = "insurance_loss"
    none = "none"


class LaborPrecedent(Base):
    """중노위 판정례 대조 코퍼스 1행 = CSV 1행(§4). 참조 코퍼스 — `case_id` 없음.

    상신-검토(Approval) 대상도 게이트 집계 대상도 아니다. LB-04 compare가 신호에 맞는
    판정례를 조회해 `risk` 행 사례 프레이밍에 인용할 뿐이다(근거 배지는 `Standard`가 별도 관리).
    """

    __tablename__ = "labor_precedents"
    __table_args__ = (
        # category는 LB-04 코퍼스 필터의 지배적 조회 경로라 인덱스를 둔다(backend/CLAUDE.md §0
        # 인덱스 원칙). matched_elements(JSONB 배열) GIN 인덱스는 코퍼스가 지금 2행뿐이라
        # ponytail: 스캔 비용이 무의미 — 399행 CSV 전체 적재 시(Post-MVP) 추가.
        Index("ix_labor_precedents_category", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="PK")
    # CSV `순번` — 실측 사례 인용 참조키(순번 51·388). 코퍼스 내 자연키라 유일해야 정상이다.
    seq: Mapped[int] = mapped_column(
        Integer, unique=True, comment="CSV 순번(실측 사례 인용 참조키)"
    )
    category: Mapped[LaborCaseType] = mapped_column(
        SAEnum(LaborCaseType, native_enum=False, create_constraint=True),
        comment="사건유형(CSV 자료구분)",
    )
    title: Mapped[str] = mapped_column(String, comment="제목(한 줄 요지)")
    committee: Mapped[str] = mapped_column(String, comment="위원회명")
    decided_on: Mapped[date | None] = mapped_column(Date, comment="작성일자")
    # ponytail: 실측 CSV가 레포에 없어 순번 51·388을 계약 §4-3 표에서 수기 하드코딩한다(시드).
    # §4-3 표는 seq/category/title/case_no/matched_elements만 제공하고 decided_on은 안 준다
    # (순번 51은 제목에 박힌 "'15.4.27.판정"으로 실측 유추 가능하나, 388은 근거 없음 — 없는
    # 값을 창작하지 않기 위해 nullable로 둔다. 원본 §4 필수(●) 표기와의 델타 — [결정필요]).
    views: Mapped[int | None] = mapped_column(Integer, comment="조회수")
    # 약 27%만 존재(§4-2) — 나머지 null. 정식 사건번호 아닌 내부표기는 넣지 않는다(창작 금지).
    case_no: Mapped[str | None] = mapped_column(
        String, comment="사건번호(제목에서 추출, 약 27%만 존재)"
    )
    # LaborRequiredElement 값의 문자열 배열(JSONB) — Item.standard_ids와 동일하게 조인테이블
    # 없이 MVP 단순화(ponytail). 화이트리스트 검증 대상 어휘와 동일 폐집합이라 값 오염 위험 낮음.
    matched_elements: Mapped[list[str]] = mapped_column(
        JSONB, comment="이 판정례가 커버하는 판정 요구 요소 목록(대조 매칭 대상)"
    )
    is_seed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="데모 직결 실측 사례 표시(순번 51·388=true)"
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="코퍼스 적재 시각"
    )
