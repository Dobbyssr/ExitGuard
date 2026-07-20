"""데모 시드 — 김민준 케이스(개발·권고사직·D-3)를 재현 가능·멱등하게 채운다.

`uv run python scripts/seed.py`로 실행. 이미 시드돼 있으면(관리자 계정 존재) 그대로 종료한다.
labor 완료율 40%(2/5 approved) 재현: L-01·L-02 approved, L-04 submitted(검토대기),
L-06·L-08 pending, L-09 not_applicable(권고사직 유형규칙 — apply_profile이 자동 처리).
"""

import asyncio
import sys
from datetime import UTC, date, datetime

from sqlalchemy import select

# Windows 콘솔 기본 코드페이지(cp949)가 한글 print 중 특수문자(em dash 등)를 못 씀 —
# 스크립트 실행 환경(Windows 로케일)에서만 나는 문제라 앱 코드는 그대로 두고 여기만 강제.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from app.db import AsyncSessionLocal
from app.domains.case.dependencies import get_case_service
from app.domains.case.models import (
    Approval,
    ApprovalDecision,
    ExitReason,
    IntakeRoute,
    ItemStatus,
)
from app.domains.case.repository import CaseRepository
from app.domains.case.schemas import CaseCreate
from app.domains.case.service import recompute_status
from app.domains.catalog.models import (
    Profile,
    RailTemplate,
    Standard,
    StandardTier,
    TemplateItem,
)
from app.domains.shared.enums import ItemKind, Rail
from app.domains.user.models import Role, User

_ADMIN_EMAIL = "hanjisoo@exitguard.example"
_OPERATOR_EMAIL = "leesuhyun@exitguard.example"


async def seed() -> None:
    """멱등 시드 — 이미 admin 계정이 있으면 아무것도 하지 않는다."""
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == _ADMIN_EMAIL))
        if existing.scalar_one_or_none() is not None:
            print("이미 시드됨 — 건너뜀")
            return

        admin = User(name="한지수", email=_ADMIN_EMAIL, role=Role.admin)
        operator = User(name="이수현", email=_OPERATOR_EMAIL, role=Role.user)
        db.add_all([admin, operator])
        await db.flush()

        standards = [
            Standard(
                tier=StandardTier.L1,
                rail=Rail.labor,
                title="근로기준법 제36조",
                article="금품청산(퇴직 후 14일 이내 지급)",
                body=(
                    "사용자는 근로자가 퇴직한 경우에는 그 지급 사유가 발생한 때부터 "
                    "14일 이내에 임금, 보상금, 그 밖에 일체의 금품을 지급하여야 한다."
                ),
                source_url="https://www.law.go.kr/법령/근로기준법/제36조",
                version="v2026.06",
            ),
            Standard(
                tier=StandardTier.L1,
                rail=Rail.labor,
                title="근로기준법 제27조",
                article="해고사유 등의 서면통지",
                body="사용자는 근로자를 해고하려면 해고사유와 해고시기를 서면으로 통지하여야 한다.",
                source_url="https://www.law.go.kr/법령/근로기준법/제27조",
                version="v2026.06",
            ),
            Standard(
                tier=StandardTier.L1,
                rail=Rail.labor,
                title="근로기준법 제26조",
                article="해고의 예고(30일 전)",
                body=(
                    "사용자는 근로자를 해고(경영상 이유에 의한 해고를 포함한다)하려면 "
                    "적어도 30일전에 예고를 하여야 한다."
                ),
                source_url="https://www.law.go.kr/법령/근로기준법/제26조",
                version="v2026.06",
            ),
        ]
        db.add_all(standards)
        await db.flush()
        std_36, std_27, std_26 = (s.id for s in standards)

        rail_template = RailTemplate(
            rail=Rail.labor, name="기본 노무 템플릿", is_base=True
        )
        db.add(rail_template)
        await db.flush()

        template_items = [
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-01",
                name="금품청산(14일 이내)",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_36],
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-02",
                name="퇴직금 정산",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_36],
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-04",
                name="해고사유 등 서면통지",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_27],
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-06",
                name="연차수당 정산 확인",
                kind=ItemKind.internal,
                blocking=False,
                standard_ids=None,
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-08",
                name="이직확인서 발급",
                kind=ItemKind.recommended,
                blocking=False,
                standard_ids=None,
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-09",
                name="해고예고(30일)",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_26],
            ),
        ]
        db.add_all(template_items)
        await db.flush()

        profile = Profile(
            name="개발직 · 시니어 이상",
            job="개발",
            rank="시니어 이상",
            rail_map={
                "labor": rail_template.id,
                "trade_secret": None,
                "security": None,
            },
        )
        db.add(profile)
        await db.flush()

        case_service = get_case_service()
        payload = CaseCreate(
            subject_name="김민준",
            subject_job="개발",
            subject_rank="시니어 책임",
            subject_role_title="백엔드 개발자",
            exit_reason=ExitReason.recommended_resignation,
            reason_text="팀 개편에 따라 권고사직으로 처리하며, 통화가 어려워 문자로 통보함.",
            exit_date=date(2026, 7, 23),
            intake_route=IntakeRoute.groupware,
            profile_id=profile.id,
        )
        case = await case_service.create_case(db, payload, operator)

        # 데모 재현 상태로 맞춘다 — L-09는 apply_profile이 이미 not_applicable로
        # 세팅했다(권고사직 유형규칙). 나머지는 여기서 직접 지정.
        case_repo = CaseRepository()
        items = await case_repo.get_items_by_case(db, case.id)
        items_by_code = {i.code: i for i in items}
        now = datetime.now(UTC)

        for code in ("L-01", "L-02"):
            item = items_by_code[code]
            item.status = ItemStatus.approved
            db.add(
                Approval(
                    item_id=item.id,
                    submitter_id=operator.id,
                    memo=f"{item.name} 정산 완료",
                    signed=True,
                    reviewer_id=admin.id,
                    decision=ApprovalDecision.confirmed,
                    reviewed_at=now,
                    submitted_at=now,
                )
            )

        l04 = items_by_code["L-04"]
        l04.status = ItemStatus.submitted
        db.add(
            Approval(
                item_id=l04.id,
                submitter_id=operator.id,
                memo="문자 통보 내역 첨부",
                signed=True,
                submitted_at=now,
            )
        )
        await db.flush()

        case_row = await case_repo.get_case(db, case.id)
        assert case_row is not None
        refreshed_items = await case_repo.get_items_by_case(db, case.id)
        case_row.status = recompute_status(case_row.status, refreshed_items)

        await db.commit()
        print(
            f"시드 완료 — case_id={case.id}, labor 완료율 재현(L-01·L-02 approved = 2/5)"
        )


if __name__ == "__main__":
    asyncio.run(seed())
