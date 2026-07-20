"""도메인 전체가 공유하는 응답 shape — envelope·페이지네이션·근거배지(api-spec §1)."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from app.domains.catalog.models import StandardTier

T = TypeVar("T")


class Pagination(BaseModel):
    """목록 응답 페이지네이션(api-spec §1-4)."""

    page: int
    size: int
    total: int
    total_pages: int


class Meta(BaseModel):
    """envelope의 meta — 엔드포인트마다 쓰는 필드만 채우고 나머지는 None.

    페이지네이션(목록)·toast(mutation)·seal_status 등 증적 아카이브 메타(§2-5)를
    한 스키마로 겸용한다. 엔드포인트별 Meta 서브클래스를 늘리지 않기 위한 선택(YAGNI).
    """

    pagination: Pagination | None = None
    toast: str | None = None
    seal_status: str | None = None
    total_count: int | None = None
    last_sealed_at: datetime | None = None
    head_hash: str | None = None


class Envelope(BaseModel, Generic[T]):
    """성공 응답 공통 포맷 — {"data":..., "meta":...}(api-spec §1-2)."""

    data: T
    meta: Meta | None = None


class Badge(BaseModel):
    """근거 배지 — tier(L1/L2/L3)·출처(api-spec §1-6)."""

    model_config = ConfigDict(from_attributes=True)

    tier: StandardTier
    title: str
    url: str | None = None
    version: str
