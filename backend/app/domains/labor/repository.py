"""labor 도메인 리포지토리 — `LaborPrecedent` 코퍼스 조회. 읽기 전용, stateless."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.labor.models import LaborCaseType, LaborPrecedent, LaborRequiredElement


class LaborRepository:
    """LaborPrecedent 코퍼스 접근. 케이스 비종속 참조 데이터라 조회 메서드만 있다."""

    async def find_by_element_and_categories(
        self,
        db: AsyncSession,
        element: LaborRequiredElement,
        categories: Sequence[LaborCaseType],
    ) -> list[LaborPrecedent]:
        """LB-04 코퍼스 필터(노무 §5-2) — `element`가 matched_elements에 포함되고

        `category`가 해고계열인 판정례만, seq 오름차순(실측 인용 재현성)으로 반환한다.
        """
        stmt = (
            select(LaborPrecedent)
            .where(
                LaborPrecedent.matched_elements.contains([element.value]),
                LaborPrecedent.category.in_(categories),
            )
            .order_by(LaborPrecedent.seq)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
