from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import health

app = FastAPI(title="ExitGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)


@app.on_event("startup")
def on_startup() -> None:
    # DB가 아직 안 떠 있어도 앱은 부팅되어야 한다 (/health가 degraded로 보고).
    try:
        init_db()
    except Exception:
        pass
