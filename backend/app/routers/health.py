from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """앱 부팅 여부와 DB 연결 상태를 함께 보고한다. DB가 죽어 있어도 앱 자체는 ok."""
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"

    return {"status": "ok", "db": db_status}
