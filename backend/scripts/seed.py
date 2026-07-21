"""데모 시드 — 김민준 케이스(개발·권고사직·D-3)를 재현 가능·멱등하게 채운다.

`uv run python scripts/seed.py`로 실행. 이미 시드돼 있으면(관리자 계정 존재) 그대로 종료한다.
노무 6항목은 노무 data-model.md §2-1 표 그대로(L-01~L-09, 결번 L-03·L-05·L-07은 회사 커스텀
예약). labor 완료율 40%(2/5 approved) 재현: L-01·L-02 approved, L-04 submitted(검토대기),
L-06·L-08 pending, L-09 not_applicable(권고사직 유형규칙 — apply_profile이 자동 처리).
reason_text에 "문자로 통보"를 심어 intake-compare가 written_notice 신호를 발화하게 한다(§5-2).
"""

import asyncio
import sys
from datetime import UTC, date, datetime, timedelta

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
from app.domains.labor.models import LaborCaseType, LaborPrecedent, LaborRequiredElement
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

        # --- 근거 시드(Standard, rail=labor) — 노무 §6 표 그대로 L1×3 + L2 + L3 ---
        standards = [
            Standard(
                tier=StandardTier.L1,
                rail=Rail.labor,
                title="근로기준법 제36조",
                article="금품청산(퇴직 후 14일 이내 지급)",
                body=(
                    "사용자는 근로자가 사망 또는 퇴직한 경우에는 그 지급 사유가 발생한 때부터 "
                    "14일 이내에 임금, 보상금, 그 밖의 일체의 금품을 지급하여야 한다."
                ),
                source_url="https://www.law.go.kr/법령/근로기준법/제36조",
                version="v2025.10",
            ),
            Standard(
                tier=StandardTier.L1,
                rail=Rail.labor,
                title="근로기준법 제27조",
                article="해고사유 등의 서면통지",
                body="사용자는 근로자를 해고하려면 해고사유와 해고시기를 서면으로 통지하여야 한다.",
                source_url="https://www.law.go.kr/법령/근로기준법/제27조",
                version="v2025.10",
            ),
            Standard(
                tier=StandardTier.L1,
                rail=Rail.labor,
                title="근로기준법 제26조",
                article="해고의 예고(30일 전)",
                body=(
                    "사용자는 근로자를 해고(경영상 이유에 의한 해고를 포함한다)하려면 "
                    "적어도 30일전에 예고를 하여야 하고, 30일 전에 예고를 하지 아니하였을 "
                    "때에는 30일분 이상의 통상임금을 지급하여야 한다."
                ),
                source_url="https://www.law.go.kr/법령/근로기준법/제26조",
                version="v2025.10",
            ),
            Standard(
                tier=StandardTier.L2,
                rail=Rail.labor,
                title="중앙노동위원회 주요 판정례 (서면통지 위반 계열)",
                article="해고 서면통지(§27) 요구 요소",
                body=(
                    "해고하면서 해고사유·시기를 서면으로 통지하지 않은 경우(구두·문자 통보 "
                    "포함) 부당해고로 판정된 공개 사례가 있다. (중노위 주요 판정사례 — "
                    "순번 51·388 등)"
                ),
                source_url="https://www.nlrc.go.kr",
                version="v2026.05",
            ),
            Standard(
                tier=StandardTier.L3,
                rail=Rail.labor,
                title="고용노동부 해고·금품청산 관련 안내",
                # [시드확인필요] 구체 문서명·URL은 개발 시드 단계 확정 대상(노무 §6 각주).
                # 실재하는 고용부 홈페이지로 연결하되 특정 문서까지는 창작하지 않는다.
                article="해고 절차·금품청산 운영 기준 안내 [시드확인필요: 구체 문서명 미정]",
                body="해고 서면통지 방법·금품청산 기한 운영 안내(표준서식·체크리스트).",
                source_url="https://www.moel.go.kr",
                version="v2026",
            ),
        ]
        db.add_all(standards)
        await db.flush()
        std_36, std_27, std_26, std_l2, std_l3 = (s.id for s in standards)

        # --- LaborPrecedent 코퍼스(§4) — 순번 51·388 실측 2건(§4-3 원문 그대로 하드코딩) ---
        db.add_all(
            [
                LaborPrecedent(
                    seq=51,
                    category=LaborCaseType.disciplinary_dismissal,
                    title=(
                        "징계사유 중 일부만 인정되어 해고는 양정이 과하고, 해고하면서 "
                        "휴대폰 문자로 통보한 것은 서면통지 의무를 위반하여 부당하다고 "
                        "판정한 사례(중노위, '15.4.27.판정)"
                    ),
                    committee="중앙",
                    decided_on=date(2015, 4, 27),
                    case_no=None,  # 사건번호 없음(§4-2) — 내부표기("'15.4.27.판정")는 정식
                    # 사건번호가 아니라 case_no에 넣지 않는다(창작 금지).
                    matched_elements=[LaborRequiredElement.written_notice.value],
                    is_seed=True,
                ),
                LaborPrecedent(
                    seq=388,
                    category=LaborCaseType.ordinary_dismissal,
                    title=(
                        "근로계약기간이 만료되지 않았음에도 해고에 해당하고 근로기준법 "
                        "제27조에 따라 해고의 사유와 시기를 명시한 서면을 교부하지 않아 "
                        "부당해고라고 판정한 사례"
                    ),
                    committee="중앙",
                    # decided_on 미상 — §4-3 표는 이 행의 작성일자를 주지 않는다(원본 CSV
                    # 미보유). 없는 값을 창작하지 않고 null로 둔다([결정필요] — 실측 CSV
                    # 확보 시 채울 것).
                    decided_on=None,
                    case_no=None,  # 제목 내 사건번호 없음(§4-3)
                    matched_elements=[LaborRequiredElement.written_notice.value],
                    is_seed=True,
                ),
            ]
        )
        await db.flush()

        # --- 레일 템플릿 — 노무 §2-1 표 정본(결번 L-03·L-05·L-07은 회사 커스텀 예약) ---
        rail_template = RailTemplate(
            rail=Rail.labor, name="기본 노무 템플릿", is_base=True
        )
        db.add(rail_template)
        await db.flush()

        template_items = [
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-01",
                name="사직 합의서 서면 확인",
                kind=ItemKind.internal,
                blocking=False,
                standard_ids=[std_l3],
                detail_schema={
                    "deadline_rule": "none",
                    "deadline_basis": None,
                    "timeline_group": None,
                },
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-02",
                name="연차 미사용 수당 정산",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_36],
                detail_schema={
                    "deadline_rule": "settlement_14d",
                    "deadline_basis": "근로기준법 제36조",
                    "timeline_group": "settlement",
                },
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-04",
                name="금품청산 (14일)",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_36],
                detail_schema={
                    "deadline_rule": "settlement_14d",
                    "deadline_basis": "근로기준법 제36조",
                    "timeline_group": "settlement",
                },
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-06",
                name="이직확인서 발급",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_36],
                detail_schema={
                    # [시드확인필요] 조문 기한 미실측(§2-2) — deadline_basis/deadline은 null.
                    "deadline_rule": "separation_cert",
                    "deadline_basis": None,
                    "timeline_group": "filing",
                },
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-08",
                name="4대보험 상실신고",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_36],
                detail_schema={
                    "deadline_rule": "insurance_loss",
                    "deadline_basis": None,
                    "timeline_group": "filing",
                },
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-09",
                name="해고예고 (30일)",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[std_26],
                detail_schema={
                    "deadline_rule": "dismissal_notice_30d",
                    "deadline_basis": "근로기준법 제26조",
                    "timeline_group": "notice",
                },
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
        # 세팅했다(권고사직 유형규칙). 나머지는 여기서 직접 지정(노무 §3-3 캘리브레이션).
        case_repo = CaseRepository()
        items = await case_repo.get_items_by_case(db, case.id)
        items_by_code = {i.code: i for i in items}
        now = datetime.now(UTC)

        for code in ("L-01", "L-02"):
            item = items_by_code[code]
            item.status = ItemStatus.approved
            if code == "L-02":
                item.deadline = case.exit_date + timedelta(days=14)
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
        l04.deadline = case.exit_date + timedelta(days=14)
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
            f"시드 완료 — case_id={case.id}, labor 완료율 재현(L-01·L-02 approved = 2/5), "
            "LaborPrecedent 순번 51·388 적재"
        )


if __name__ == "__main__":
    asyncio.run(seed())
