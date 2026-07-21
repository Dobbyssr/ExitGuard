from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions import register_exception_handlers
from app.db import engine
from app.domains.case.router import router as case_router
from app.domains.compare.router import router as compare_router
from app.domains.evidence.router import router as evidence_router
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 시작/종료 훅. DB 엔진은 db.py에서 lazy 생성되므로 종료 시 dispose만 책임진다."""
    yield
    await engine.dispose()


app = FastAPI(title="ExitGuard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(case_router, prefix="/api/v1")
app.include_router(compare_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
