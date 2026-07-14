from fastapi import APIRouter
from sqlalchemy import text
from sqlmodel import Session

from app.db import engine

router = APIRouter()


@router.get("/health")
def health() -> dict:
    db_status = "ok"
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
    except Exception:
        db_status = "degraded"

    return {"status": "ok", "db": db_status}
