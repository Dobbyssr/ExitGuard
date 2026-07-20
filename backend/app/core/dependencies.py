"""도메인을 넘나드는 공용 Depends — 현재는 '현재 액터' 조회뿐이다.

인증은 스코프 밖(PRODUCT §6-4·api-spec §1-1) — 데모는 관리자 로그인 상태로 시작한다.
전체 인증이 구현되기 전까지, 시드된 첫 admin/user 레코드를 각각 "현재 관리자"·
"현재 담당자"로 취급해 Case.created_by·Approval.submitter_id/reviewer_id·
Evidence.actor 같은 FK/필수 필드를 채운다. 이 임시 대체는 세로절단 시나리오 구동에
load-bearing 아니므로(§6-4) 나중에 진짜 인증으로 교체될 지점이다.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.domains.user.dependencies import get_user_repository
from app.domains.user.models import Role, User
from app.domains.user.repository import UserRepository


async def get_current_admin(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """현재 관리자 액터(검토·승인 엔드포인트의 [admin] 주체)."""
    user = await user_repo.get_first_by_role(db, Role.admin)
    if user is None:
        raise HTTPException(
            500,
            detail={
                "code": "INTERNAL",
                "message": "관리자 계정이 시드되지 않았습니다",
                "fields": None,
            },
        )
    return user


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """현재 담당자 액터(접수·상신 엔드포인트의 [user] 주체)."""
    user = await user_repo.get_first_by_role(db, Role.user)
    if user is None:
        raise HTTPException(
            500,
            detail={
                "code": "INTERNAL",
                "message": "담당자 계정이 시드되지 않았습니다",
                "fields": None,
            },
        )
    return user
