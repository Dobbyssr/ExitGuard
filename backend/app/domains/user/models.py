"""user 도메인 — 사용자(User).

인증은 스코프 밖(PRODUCT §6-4) — admin/user 2역할만 구분한다.
퇴사자 본인은 로그인하지 않는다 — 액터가 아니라 Case의 데이터다(data-model.md §2-6).
"""

import enum

from sqlalchemy import String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Role(str, enum.Enum):
    """사용자 역할 — 관리자(검토·승인·권한부여)/일반사용자(레일 수행·상신)."""

    admin = "admin"
    user = "user"


class User(Base):
    """사용자 — 담당자(user)·관리자(admin). data-model.md §3-8."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, native_enum=False, create_constraint=True)
    )
    # list[str] 그대로 — 중첩 구조가 없어 JSONB보다 네이티브 배열이 단순하다.
    granted_scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String))
