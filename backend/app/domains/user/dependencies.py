"""user 도메인 repository provider(FastAPI Depends)."""

from app.domains.user.repository import UserRepository


def get_user_repository() -> UserRepository:
    """UserRepository provider — stateless라 매 요청 새로 만들어도 싸다."""
    return UserRepository()
