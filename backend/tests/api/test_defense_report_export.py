"""B — DefenseReport export(CM-13, B1) — `GET /cases/{id}/evidence/export`(data-model §10).

intake-compare로 `compare_recorded`를 봉인한 뒤 export가 그 스냅샷을 재계산 없이 인용하는지,
kpi가 §5 라이브 게이트와 일치하는지(케이스가 아직 미승인이라 봉인 스냅샷 없음), evidence_chain
head_hash가 마지막 증적 해시와 같은지, boundary_notice가 반드시 포함되는지를 검증한다.
"""

from datetime import date, timedelta

from httpx import AsyncClient


async def _create_case(client: AsyncClient, profile_id: int) -> dict:
    payload = {
        "subject_name": "김민준",
        "subject_job": "개발",
        "subject_rank": "시니어 책임",
        "subject_role_title": "백엔드 개발자",
        "exit_reason": "recommended_resignation",
        "reason_text": "팀 개편에 따라 권고사직으로 처리함.",
        "exit_date": str(date.today() + timedelta(days=14)),
        "intake_route": "groupware",
        "profile_id": profile_id,
    }
    res = await client.post("/api/v1/cases", json=payload)
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def test_export_report_after_intake_compare_cites_sealed_snapshot(
    client: AsyncClient, seeded: dict
) -> None:
    """봉인 전 evidence 0건(브리프 전제) → intake-compare 1회 → export가 스냅샷을 인용."""
    detail = await _create_case(client, seeded["profile_id"])
    case_id = detail["case"]["id"]

    archive_before = (await client.get(f"/api/v1/cases/{case_id}/evidence")).json()
    assert archive_before["data"] == []  # 시드 시작상태는 증적 0(브리프 전제)

    compare_res = await client.post(f"/api/v1/cases/{case_id}/intake-compare")
    assert compare_res.status_code == 200, compare_res.text

    gate = (await client.get(f"/api/v1/cases/{case_id}/gate")).json()["data"]
    archive = (await client.get(f"/api/v1/cases/{case_id}/evidence")).json()
    entries = archive["data"]
    assert [e["event_type"] for e in entries] == ["compare_recorded"]

    res = await client.get(f"/api/v1/cases/{case_id}/evidence/export?format=json")

    assert res.status_code == 200, res.text
    report = res.json()["data"]

    assert report["case"]["id"] == case_id
    assert report["case"]["subject_name"] == "김민준"

    # kpi — case_approved 봉인 없음 → §5 라이브 게이트와 일치(L-01 blocking pending → risk 1).
    assert report["kpi"]["overall_completion"] == gate["overall_completion"]
    assert report["kpi"]["risk_count"] == gate["risk_count"] == 1
    assert report["kpi"]["defensible"] is False

    # compare_findings — 재계산 아니라 봉인 스냅샷 그대로 인용(§3-4-1).
    assert len(report["compare_findings"]) == 1
    finding = report["compare_findings"][0]
    assert finding["rail"] == "labor"
    assert len(finding["rows"]) == 5
    assert finding["sealed_seq"] == entries[0]["seq"]
    assert finding["boundary_notice"].startswith(
        "본 결과는 위법 여부를 판정하지 않습니다"
    )

    # evidence_chain — head_hash는 마지막(유일한) 증적의 해시.
    chain = report["evidence_chain"]
    assert chain["total_count"] == 1
    assert chain["seal_status"] == "accruing"
    assert chain["head_hash"] == entries[0]["integrity_hash"]
    assert chain["last_seq"] == entries[0]["seq"]

    # 직역법 — 리포트 최상위 boundary_notice 필수(§10, 누락 시 리포트 무효).
    assert report["boundary_notice"].startswith(
        "본 결과는 위법 여부를 판정하지 않습니다"
    )


async def test_export_report_when_case_not_found_returns_404(
    client: AsyncClient,
) -> None:
    res = await client.get("/api/v1/cases/999999/evidence/export")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


async def test_export_report_when_format_pdf_returns_501_not_implemented(
    client: AsyncClient, seeded: dict
) -> None:
    """format=pdf는 MVP 범위 밖 — 억지 구현 대신 명시적 501(ponytail)."""
    detail = await _create_case(client, seeded["profile_id"])
    case_id = detail["case"]["id"]

    res = await client.get(f"/api/v1/cases/{case_id}/evidence/export?format=pdf")

    assert res.status_code == 501
    assert res.json()["error"]["code"] == "NOT_IMPLEMENTED"
