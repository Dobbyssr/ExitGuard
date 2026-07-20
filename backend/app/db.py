"""async DB 엔진·세션팩토리·get_db 의존성. 스키마는 Alembic이 관리(create_all 없음)."""

from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

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
