"""compare 파이프라인 API 테스트 — LB-04 written_notice 세로절단(김민준 시나리오).

`seeded`(tests/conftest.py) 픽스처는 case happy-path 전용 뼈대(L-01 1항목)라 재사용하지
않는다 — compare는 노무 §2-1 정본 6항목(L-01~L-09) + LaborPrecedent 코퍼스가 필요해
이 파일 전용 픽스처(`labor_seeded`)로 scripts/seed.py와 동일하게 직접 조립한다.
"""

from datetime import UTC, date, datetime, timedelta

import pytest_asyncio
from httpx import AsyncClient

from app.domains.case.models import Approval, ItemStatus
from app.domains.case.repository import CaseRepository
from app.domains.catalog.models import (
    Profile,
    RailTemplate,
    Standard,
    StandardTier,
    TemplateItem,
)
from app.domains.labor.models import LaborCaseType, LaborPrecedent, LaborRequiredElement
from app.domains.shared.enums import ItemKind, Rail
from app.domains.user.models import Role, User
from tests.conftest import TestSessionLocal


@pytest_asyncio.fixture
async def labor_seeded() -> dict:
    """노무 §2-1 정본 6항목 + Standard(L1×3/L2/L3) + LaborPrecedent(순번 51·388)."""
    async with TestSessionLocal() as session:
        admin = User(name="관리자", email="admin@compare.test", role=Role.admin)
        operator = User(name="담당자", email="operator@compare.test", role=Role.user)
        session.add_all([admin, operator])
        await session.flush()

        std_36 = Standard(
            tier=StandardTier.L1,
            rail=Rail.labor,
            title="근로기준법 제36조",
            source_url="https://law.go.kr/36",
            version="v1",
        )
        std_27 = Standard(
            tier=StandardTier.L1,
            rail=Rail.labor,
            title="근로기준법 제27조",
            source_url="https://law.go.kr/27",
            version="v1",
        )
        std_26 = Standard(
            tier=StandardTier.L1,
            rail=Rail.labor,
            title="근로기준법 제26조",
            source_url="https://law.go.kr/26",
            version="v1",
        )
        std_l2 = Standard(
            tier=StandardTier.L2,
            rail=Rail.labor,
            title="중앙노동위원회 주요 판정례 (서면통지 위반 계열)",
            source_url="https://nlrc.go.kr",
            version="v1",
        )
        std_l3 = Standard(
            tier=StandardTier.L3,
            rail=Rail.labor,
            title="고용노동부 해고·금품청산 관련 안내",
            source_url="https://moel.go.kr",
            version="v1",
        )
        session.add_all([std_36, std_27, std_26, std_l2, std_l3])
        await session.flush()

        session.add_all(
            [
                LaborPrecedent(
                    seq=51,
                    category=LaborCaseType.disciplinary_dismissal,
                    title="문자로 통보하여 서면통지 의무를 위반했다고 판정한 사례",
                    committee="중앙",
                    decided_on=date(2015, 4, 27),
                    matched_elements=[LaborRequiredElement.written_notice.value],
                    is_seed=True,
                ),
                LaborPrecedent(
                    seq=388,
                    category=LaborCaseType.ordinary_dismissal,
                    title="제27조에 따른 서면을 교부하지 않아 부당해고라고 판정한 사례",
                    committee="중앙",
                    decided_on=None,
                    matched_elements=[LaborRequiredElement.written_notice.value],
                    is_seed=True,
                ),
            ]
        )

        rail_template = RailTemplate(
            rail=Rail.labor, name="테스트 노무 템플릿", is_base=True
        )
        session.add(rail_template)
        await session.flush()

        items_def = [
            ("L-01", "사직 합의서 서면 확인", ItemKind.internal, False, [std_l3.id]),
            ("L-02", "연차 미사용 수당 정산", ItemKind.statutory, True, [std_36.id]),
            ("L-04", "금품청산 (14일)", ItemKind.statutory, True, [std_36.id]),
            ("L-06", "이직확인서 발급", ItemKind.statutory, True, [std_36.id]),
            ("L-08", "4대보험 상실신고", ItemKind.statutory, True, [std_36.id]),
            ("L-09", "해고예고 (30일)", ItemKind.statutory, True, [std_26.id]),
        ]
        session.add_all(
            [
                TemplateItem(
                    rail_template_id=rail_template.id,
                    code=code,
                    name=name,
                    kind=kind,
                    blocking=blocking,
                    standard_ids=std_ids,
                )
                for code, name, kind, blocking, std_ids in items_def
            ]
        )
        await session.flush()

        profile = Profile(
            name="테스트 개발직",
            job="개발",
            rank="시니어",
            rail_map={
                "labor": rail_template.id,
                "trade_secret": None,
                "security": None,
            },
        )
        session.add(profile)
        await session.flush()

        result = {
            "admin_id": admin.id,
            "operator_id": operator.id,
            "profile_id": profile.id,
        }
        await session.commit()
        return result


async def _create_case(
    client: AsyncClient, profile_id: int, *, reason_text: str
) -> dict:
    payload = {
        "subject_name": "김민준",
        "subject_job": "개발",
        "subject_rank": "시니어 책임",
        "subject_role_title": "백엔드 개발자",
        "exit_reason": "recommended_resignation",
        "reason_text": reason_text,
        "exit_date": str(date.today() + timedelta(days=14)),
        "intake_route": "groupware",
        "profile_id": profile_id,
    }
    res = await client.post("/api/v1/cases", json=payload)
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def _apply_demo_rollup(case_id: int, operator_id: int) -> None:
    """노무 §3-3 캘리브레이션 — L-01·L-02 approved, L-04 submitted(나머지는 apply_profile 기본)."""
    async with TestSessionLocal() as session:
        repo = CaseRepository()
        items = await repo.get_items_by_case(session, case_id)
        by_code = {i.code: i for i in items}
        for code in ("L-01", "L-02"):
            by_code[code].status = ItemStatus.approved
        by_code["L-04"].status = ItemStatus.submitted
        session.add(
            Approval(
                item_id=by_code["L-04"].id,
                submitter_id=operator_id,
                memo="상신",
                signed=True,
                submitted_at=datetime.now(UTC),
            )
        )
        await session.commit()


async def test_intake_compare_when_written_notice_signal_cites_precedents_and_seals(
    client: AsyncClient, labor_seeded: dict
) -> None:
    """김민준 세로절단 — written_notice 발화→순번51/388 인용·unmet_count=3·badges L1/L2·봉인."""
    detail = await _create_case(
        client,
        labor_seeded["profile_id"],
        reason_text="팀 개편에 따라 권고사직으로 처리하며, 통화가 어려워 문자로 통보함.",
    )
    case_id = detail["case"]["id"]
    assert len(detail["items"]) == 6  # 노무 §2-1 6항목 전부 복제
    await _apply_demo_rollup(case_id, labor_seeded["operator_id"])

    res = await client.post(f"/api/v1/cases/{case_id}/intake-compare")

    assert res.status_code == 200, res.text
    result = res.json()["data"]
    assert [row["kind"] for row in result["rows"]] == [
        "procedure",
        "standard",
        "risk",
        "status",
        "source",
    ]
    assert result["unmet_count"] == 3  # L-04·L-06·L-08 미충족(§3-3 정합)
    risk_text = result["rows"][2]["text"]
    assert "51" in risk_text
    assert "388" in risk_text
    assert "사례가 있습니다" in risk_text
    tiers = {b["tier"] for b in result["badges"]}
    assert {"L1", "L2"} <= tiers
    assert result["boundary_notice"].startswith(
        "본 결과는 위법 여부를 판정하지 않습니다"
    )

    # compare_recorded 봉인(§3-4-1) — 5행 스냅샷이 그대로 증적에 편입됐는지.
    archive = (await client.get(f"/api/v1/cases/{case_id}/evidence")).json()["data"]
    compare_events = [e for e in archive if e["event_type"] == "compare_recorded"]
    assert len(compare_events) == 1
    assert len(compare_events[0]["payload"]["rows"]) == 5
    assert compare_events[0]["payload"]["unmet_count"] == 3


async def test_intake_compare_when_no_signal_falls_back_without_case_citation(
    client: AsyncClient, labor_seeded: dict
) -> None:
    """무신호 fallback(§6-4) — 5행+boundary 항상 성립, risk 행에 51/388 인용 없음."""
    detail = await _create_case(
        client,
        labor_seeded["profile_id"],
        reason_text="정상적인 절차에 따라 서면으로 해고를 통지함.",
    )
    case_id = detail["case"]["id"]

    res = await client.post(f"/api/v1/cases/{case_id}/intake-compare")

    assert res.status_code == 200, res.text
    result = res.json()["data"]
    assert [row["kind"] for row in result["rows"]] == [
        "procedure",
        "standard",
        "risk",
        "status",
        "source",
    ]
    assert result["rows"][0]["text"] == "추가 신호가 확인되지 않았습니다."
    risk_text = result["rows"][2]["text"]
    assert "51" not in risk_text
    assert "388" not in risk_text
    assert (
        "사례가 있습니다" not in risk_text
    )  # §36처럼 코퍼스 인용 없는 risk는 단정하지 않는다
    assert result["boundary_notice"]


async def test_intake_compare_when_case_not_found_returns_404(
    client: AsyncClient, labor_seeded: dict
) -> None:
    """존재하는 담당자 계정은 있으나(get_current_user 통과) 케이스 자체가 없는 경우."""
    res = await client.post("/api/v1/cases/999999/intake-compare")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


async def test_compare_when_rail_not_labor_returns_422(client: AsyncClient) -> None:
    """MVP는 노무 레일만 지원 — 다른 레일 요청은 COMPARE_FAILED(422)."""
    payload = {
        "rail": "security",
        "subject": "x",
        "case_facts": {
            "exit_reason": "voluntary",
            "exit_date": str(date.today()),
            "job": "x",
            "rank": "x",
        },
    }

    res = await client.post("/api/v1/compare", json=payload)

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "COMPARE_FAILED"
