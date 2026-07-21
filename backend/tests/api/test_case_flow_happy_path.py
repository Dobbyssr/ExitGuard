"""API happy path — 접수→상신→검토→승인(+증적봉인 조회). 실제 exitguard_test DB에 대해 돈다.

get_current_admin/get_current_user는 DB의 첫 admin/user 레코드를 쓰므로(app/core/dependencies.py),
`seeded` 픽스처가 만든 admin/operator 1명씩이 그대로 액터가 된다 — 별도 인증 override 불필요.
"""

from datetime import date, timedelta

from httpx import AsyncClient


async def _create_case(client: AsyncClient, seeded: dict) -> dict:
    payload = {
        "subject_name": "김민준",
        "subject_job": "개발",
        "subject_rank": "시니어 책임",
        "subject_role_title": "백엔드 개발자",
        "exit_reason": "recommended_resignation",
        "reason_text": "권고사직 처리",
        "exit_date": str(date.today() + timedelta(days=3)),
        "intake_route": "groupware",
        "profile_id": seeded["profile_id"],
    }
    res = await client.post("/api/v1/cases", json=payload)
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def test_case_lifecycle_happy_path(client: AsyncClient, seeded: dict) -> None:
    """접수(profile 적용) → L-01 상신 → 검토 확인 → 승인 → 증적 아카이브 확인."""
    # 1) 접수 — profile.rail_map(labor)의 TemplateItem 2개(L-01 blocking, L-08 비blocking)가 복제된다.
    detail = await _create_case(client, seeded)
    case_id = detail["case"]["id"]
    assert detail["case"]["status"] == "in_progress"
    assert len(detail["items"]) == 2
    l01 = next(i for i in detail["items"] if i["code"] == "L-01")
    assert l01["status"] == "pending"
    assert l01["badges"][0]["tier"] == "L1"  # 근거 배지 조립 확인(api-spec §1-6)

    gate = (await client.get(f"/api/v1/cases/{case_id}/gate")).json()["data"]
    assert gate["overall_completion"] == 0
    assert gate["risk_count"] == 1  # L-01 blocking·pending → 미해소 리스크 1건
    assert gate["defensible"] is False

    # 2) 상신(CM-10) — pending → submitted, Approval 생성 + item_submitted 자동봉인.
    submit_res = await client.post(
        f"/api/v1/items/{l01['id']}/submit",
        json={"memo": "금품청산 정산 완료", "signed": True},
    )
    assert submit_res.status_code == 200, submit_res.text
    assert submit_res.json()["data"]["memo"] == "금품청산 정산 완료"

    case_after_submit = (await client.get(f"/api/v1/cases/{case_id}")).json()["data"]
    assert case_after_submit["case"]["status"] == "review_waiting"

    # 3) 검토(CM-10) — submitted → approved + item_confirmed 자동봉인.
    review_res = await client.post(
        f"/api/v1/items/{l01['id']}/review", json={"decision": "confirmed"}
    )
    assert review_res.status_code == 200, review_res.text
    assert review_res.json()["data"]["decision"] == "confirmed"

    gate_after_review = (await client.get(f"/api/v1/cases/{case_id}/gate")).json()[
        "data"
    ]
    assert gate_after_review["defensible"] is True
    assert gate_after_review["risk_count"] == 0

    # 4) 승인(T3) — defensible && submitted==0 → completed + case_approved 자동봉인.
    approve_res = await client.post(f"/api/v1/cases/{case_id}/approve", json={})
    assert approve_res.status_code == 200, approve_res.text
    approve_data = approve_res.json()["data"]
    assert approve_data["case"]["status"] == "completed"
    assert approve_data["evidence"]["event_type"] == "case_approved"

    # 5) 증적 아카이브 — item_submitted·item_confirmed·case_approved 3건, 해시체인 연결.
    archive = (await client.get(f"/api/v1/cases/{case_id}/evidence")).json()
    entries = archive["data"]
    assert [e["event_type"] for e in entries] == [
        "item_submitted",
        "item_confirmed",
        "case_approved",
    ]
    assert entries[0]["prev_hash"] is None
    assert entries[1]["prev_hash"] == entries[0]["integrity_hash"]
    assert entries[2]["prev_hash"] == entries[1]["integrity_hash"]
    assert archive["meta"]["seal_status"] == "sealed"
    assert archive["meta"]["head_hash"] == entries[2]["integrity_hash"]


async def test_approve_case_when_risk_unresolved_returns_409(
    client: AsyncClient, seeded: dict
) -> None:
    """강제승인 방어 — L-01이 pending인 채로 승인 시도하면 409(우회 승인 없음, T3)."""
    detail = await _create_case(client, seeded)
    case_id = detail["case"]["id"]

    res = await client.post(f"/api/v1/cases/{case_id}/approve", json={})

    assert res.status_code == 409
    body = res.json()
    assert body["error"]["code"] == "INVALID_TRANSITION"
    assert body["error"]["fields"]["risk_count"] == 1


async def test_review_item_when_not_submitted_returns_409(
    client: AsyncClient, seeded: dict
) -> None:
    """pending 항목을 바로 검토하려 하면 409(api-spec §2-4)."""
    detail = await _create_case(client, seeded)
    l01 = next(i for i in detail["items"] if i["code"] == "L-01")

    res = await client.post(
        f"/api/v1/items/{l01['id']}/review", json={"decision": "confirmed"}
    )

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_get_case_when_not_found_returns_404(client: AsyncClient) -> None:
    res = await client.get("/api/v1/cases/999999")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


async def test_get_item_when_reviewed_returns_detail_with_approvals_and_basis(
    client: AsyncClient, seeded: dict
) -> None:
    """항목 드로어 상세(CM-09) — 상신+검토 이후 approvals 이력·badges·basis가 함께 온다."""
    detail = await _create_case(client, seeded)
    l01 = next(i for i in detail["items"] if i["code"] == "L-01")

    await client.post(
        f"/api/v1/items/{l01['id']}/submit",
        json={"memo": "금품청산 정산 완료", "signed": True},
    )
    await client.post(
        f"/api/v1/items/{l01['id']}/review", json={"decision": "confirmed"}
    )

    res = await client.get(f"/api/v1/items/{l01['id']}")

    assert res.status_code == 200, res.text
    item = res.json()["data"]
    assert item["code"] == "L-01"
    assert item["status"] == "approved"
    assert item["badges"][0]["tier"] == "L1"
    assert len(item["approvals"]) == 1
    assert item["approvals"][0]["decision"] == "confirmed"
    assert item["approvals"][0]["memo"] == "금품청산 정산 완료"
    assert item["basis"][0]["title"] == "근로기준법 제36조"


async def test_get_item_when_not_found_returns_404(client: AsyncClient) -> None:
    res = await client.get("/api/v1/items/999999")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"
