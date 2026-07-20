"""전역 예외 처리.

도메인 예외(404/409 등)는 각 router가 직접 HTTPException으로 변환한다(backend/CLAUDE.md §7).
여기서는 ① HTTPException을 api-spec §1-3 에러 envelope({"error":{...}})로 통일하는 것과
② 진짜로 예상 못한 예외를 500 표준 응답으로 감싸는 것, 두 가지만 한다.
"""

import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """앱 조립 시 1회 호출 — main.py에서 app 생성 직후 부른다."""

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """router가 던진 HTTPException(detail={code,message,fields})을 envelope로 감싼다."""
        raw_detail = exc.detail
        detail: dict[str, object] = (
            raw_detail
            if isinstance(raw_detail, dict)
            else {"code": "INTERNAL", "message": str(raw_detail), "fields": None}
        )
        return JSONResponse(status_code=exc.status_code, content={"error": detail})

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """미처리 예외 → 500. 스택트레이스는 클라이언트에 노출하지 않고 로그에만 남긴다."""
        request_id = str(uuid.uuid4())
        logger.error(
            "unhandled exception", exc_info=True, extra={"request_id": request_id}
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL",
                    "message": "서버 오류가 발생했습니다",
                    "fields": None,
                    "request_id": request_id,
                }
            },
        )
