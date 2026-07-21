"""case 도메인 리포지토리 — Case/Item/Approval 접근. stateless·flush까지(commit 금지)."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import Row, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.case.models import Approval, Case, CaseStatus, ExitReason, Item


class CaseRepository:
    """Case/Item/Approval 테이블 접근."""

    async def create_case(
        self,
        db: AsyncSession,
        *,
        subject_name: str,
        subject_job: str,
        subject_rank: str,
        subject_role_title: str | None,
        exit_reason: ExitReason,
        reason_text: str | None,
        exit_date: date,
        intake_route: str,
        profile_id: int | None,
        created_by: int,
    ) -> Case:
        """케이스 1건 생성(§3-1). status 기본값은 모델 default(in_progress)."""
        case = Case(
            subject_name=subject_name,
            subject_job=subject_job,
            subject_rank=subject_rank,
            subject_role_title=subject_role_title,
            exit_reason=exit_reason,
            reason_text=reason_text,
            exit_date=exit_date,
            intake_route=intake_route,
            profile_id=profile_id,
            created_by=created_by,
        )
        db.add(case)
        await db.flush()
        return case

    async def get_case(
        self, db: AsyncSession, case_id: int, *, with_items: bool = False
    ) -> Case | None:
        """케이스 단건 조회. with_items=True면 Item을 함께 eager load(§3-2)."""
        stmt = select(Case).where(Case.id == case_id)
        if with_items:
            stmt = stmt.options(selectinload(Case.items))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_cases(
        self, db: AsyncSession, *, status_filter: CaseStatus | None, q: str | None
    ) -> list[Case]:
        """목록 조회(CM-03) — 정렬·페이지는 게이트(파생값) 계산 후 서비스가 처리한다."""
        stmt = select(Case)
        if status_filter is not None:
            stmt = stmt.where(Case.status == status_filter)
        if q:
            stmt = stmt.where(Case.subject_name.ilike(f"%{q}%"))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_item_counts(
        self, db: AsyncSession, case_ids: Sequence[int]
    ) -> Sequence[Row]:
        """케이스별 (rail,status,blocking) 조합 개수 — 게이트 목록 집계용 단일 쿼리.

        케이스마다 Item을 따로 불러오는 N+1을 피하고 GROUP BY 1쿼리로 대체한다
        (data-model §0 Post-MVP 권고 (o) 반영 — 스네이프 round1).
        """
        if not case_ids:
            return []
        stmt = (
            select(
                Item.case_id,
                Item.rail,
                Item.status,
                Item.blocking,
                func.count().label("cnt"),
            )
            .where(Item.case_id.in_(case_ids))
            .group_by(Item.case_id, Item.rail, Item.status, Item.blocking)
        )
        result = await db.execute(stmt)
        return result.all()

    async def get_item(self, db: AsyncSession, item_id: int) -> Item | None:
        """항목 단건 조회(상신·검토 전이의 대상)."""
        return await db.get(Item, item_id)

    async def get_items_by_case(self, db: AsyncSession, case_id: int) -> list[Item]:
        """케이스의 전 항목(레일 불문) — 게이트 계산·상세 응답용."""
        result = await db.execute(select(Item).where(Item.case_id == case_id))
        return list(result.scalars().all())

    async def add_item(self, db: AsyncSession, item: Item) -> Item:
        """항목 1건 추가(apply_profile이 TemplateItem을 복제할 때 사용)."""
        db.add(item)
        return item

    async def add_approval(self, db: AsyncSession, approval: Approval) -> Approval:
        """상신/검토 레코드 추가."""
        db.add(approval)
        await db.flush()
        return approval

    async def get_pending_approval(
        self, db: AsyncSession, item_id: int
    ) -> Approval | None:
        """해당 항목의 미검토(decision=null) 상신 — 항목당 최대 1건(상태머신 불변식)."""
        result = await db.execute(
            select(Approval)
            .where(Approval.item_id == item_id, Approval.decision.is_(None))
            .order_by(Approval.submitted_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_approvals_by_item(
        self, db: AsyncSession, item_id: int
    ) -> list[Approval]:
        """항목의 상신-검토 전체 이력 — 최신순(항목 드로어 상세 CM-09, api-spec §2-4)."""
        result = await db.execute(
            select(Approval)
            .where(Approval.item_id == item_id)
            .order_by(Approval.submitted_at.desc())
        )
        return list(result.scalars().all())
