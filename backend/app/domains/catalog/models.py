"""catalog 도메인 — 근거 기준(Standard)·레일 템플릿(RailTemplate/TemplateItem)·프로파일(Profile).

직무·직급 프로파일(Profile)이 레일별 템플릿(RailTemplate)을 매핑하고, 템플릿 항목(TemplateItem)이
Case 접수 시 Item으로 복제된다(Fork & Customize, data-model.md §3-6·§3-7).
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.domains.shared.enums import ItemKind, Rail


class StandardTier(str, enum.Enum):
    """근거 층위 — 법령(L1)/판례·판정례(L2)/정부가이드(L3)(§2-5)."""

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Standard(Base):
    """근거(3층 기준 스택) 레코드 — 근거 배지(L1/L2/L3)의 원천. data-model.md §3-5."""

    __tablename__ = "standards"

    id: Mapped[int] = mapped_column(primary_key=True)
    tier: Mapped[StandardTier] = mapped_column(
        SAEnum(StandardTier, native_enum=False, create_constraint=True)
    )
    rail: Mapped[Rail] = mapped_column(
        SAEnum(Rail, native_enum=False, create_constraint=True)
    )
    title: Mapped[str] = mapped_column(String)
    article: Mapped[str | None] = mapped_column(String)
    body: Mapped[str | None] = mapped_column(String)
    source_url: Mapped[str | None] = mapped_column(String)
    version: Mapped[str] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RailTemplate(Base):
    """레일별 기본 항목 묶음 — 케이스 체크리스트의 기준("빈 종이 빌더 금지"). §3-6."""

    __tablename__ = "rail_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    rail: Mapped[Rail] = mapped_column(
        SAEnum(Rail, native_enum=False, create_constraint=True)
    )
    name: Mapped[str] = mapped_column(String)
    is_base: Mapped[bool] = mapped_column(Boolean)

    template_items: Mapped[list["TemplateItem"]] = relationship(
        back_populates="rail_template"
    )


class TemplateItem(Base):
    """템플릿에 담긴 항목 정의. Case 접수 시 Item으로 복제된다. §3-6."""

    __tablename__ = "template_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    rail_template_id: Mapped[int] = mapped_column(
        ForeignKey("rail_templates.id"), index=True
    )
    code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    kind: Mapped[ItemKind] = mapped_column(
        SAEnum(ItemKind, native_enum=False, create_constraint=True)
    )
    blocking: Mapped[bool] = mapped_column(Boolean)
    # ponytail: standard_ids는 JSONB int 배열(조인테이블 없이 MVP 단순화).
    # M2M 정규화 여부는 스네이프 DB감수에서 판정.
    standard_ids: Mapped[list[int] | None] = mapped_column(JSONB)
    detail_schema: Mapped[dict | None] = mapped_column(JSONB)

    rail_template: Mapped["RailTemplate"] = relationship(
        back_populates="template_items"
    )


class Profile(Base):
    """직종·직급 프로파일 — 레일별 적용 RailTemplate 매핑(2계층 템플릿의 상위). §3-7."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    job: Mapped[str | None] = mapped_column(String)
    rank: Mapped[str | None] = mapped_column(String)
    rail_map: Mapped[dict] = mapped_column(JSONB)
