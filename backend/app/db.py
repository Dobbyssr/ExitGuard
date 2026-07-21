"""async DB 엔진·세션팩토리·get_db 의존성. 스키마는 Alembic이 관리(create_all 없음)."""

from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings

# Alembic autogenerate가 제약조건 이름을 일관되게 뽑도록 강제(이름 충돌·drift 방지).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """모든 도메인 ORM 모델의 베이스."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """생성·수정 시각(UTC) 컬럼 믹스인. created_at·updated_at을 둘 다 요구하는 모델에만 쓴다."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="생성 시각(UTC)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="수정 시각(UTC)",
    )


# create_async_engine은 실제 커넥션을 즉시 열지 않는다(lazy) — DB가 꺼져 있어도 앱은 부팅된다.
engine = create_async_engine(
    settings.database_url, pool_pre_ping=True, pool_recycle=300
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """요청 1개 = 트랜잭션 1개. 성공 시 commit, 예외 시 rollback 후 재발생."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
