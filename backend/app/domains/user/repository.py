"""user 도메인 리포지토리 — 순수 SQLAlchemy 쿼리만(비즈니스 규칙 없음)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user.models import Role, User


class UserRepository:
    """User 테이블 접근. stateless — 세션은 항상 인자로 받는다."""

    async def get_first_by_role(self, db: AsyncSession, role: Role) -> User | None:
        """해당 역할의 첫 사용자를 반환한다(인증 미구현 구간의 기본 액터 조회용)."""
        result = await db.execute(
            select(User).where(User.role == role).order_by(User.id).limit(1)
        )
        return result.scalar_one_or_none()

    async def get(self, db: AsyncSession, user_id: int) -> User | None:
        """id로 사용자 조회."""
        return await db.get(User, user_id)
