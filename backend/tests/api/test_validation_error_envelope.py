"""A1 — FastAPI 기본 검증 실패({"detail":[...]})가 api-spec §1-3 envelope로 통일되는지.

RequestValidationError는 전역 HTTPException 핸들러를 안 타므로(HTTPException 아님) 별도
핸들러가 필요했다(app/core/exceptions.py `_validation_exception_handler`).
"""

from datetime import date, timedelta

from httpx import AsyncClient


async def test_create_case_when_required_field_missing_returns_400_envelope(
    client: AsyncClient, seeded: dict
) -> None:
    """subject_name 누락 — 400 VALIDATION_ERROR + fields에 subject_name 사유 포함.

    `seeded`가 필요한 이유: `POST /cases`는 `Depends(get_current_user)`가 body 검증보다
    먼저 해석돼(FastAPI dependency solving 순서) 담당자 계정이 없으면 그쪽에서 먼저
    500(관리자 미시드)이 나 버린다 — 이 테스트가 보려는 건 검증 실패 경로라 계정은 시드해둔다.
    """
    payload = {
        "subject_job": "개발",
        "subject_rank": "시니어 책임",
        "exit_reason": "recommended_resignation",
        "exit_date": str(date.today() + timedelta(days=3)),
        "intake_route": "groupware",
    }

    res = await client.post("/api/v1/cases", json=payload)

    assert res.status_code == 400
    body = res.json()
    assert "detail" not in body  # FastAPI 기본 형태가 새 나가지 않았는지
    error = body["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "subject_name" in error["fields"]


async def test_create_case_when_exit_reason_invalid_enum_returns_400_envelope(
    client: AsyncClient, seeded: dict
) -> None:
    """enum 폐집합 밖 값 — 역시 400 envelope(§1-3)로 통일."""
    payload = {
        "subject_name": "김민준",
        "subject_job": "개발",
        "subject_rank": "시니어 책임",
        "exit_reason": "존재하지_않는_사유",
        "exit_date": str(date.today() + timedelta(days=3)),
        "intake_route": "groupware",
    }

    res = await client.post("/api/v1/cases", json=payload)

    assert res.status_code == 400
    error = res.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "exit_reason" in error["fields"]
