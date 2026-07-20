"""catalog 도메인 리포지토리 — Profile·RailTemplate·TemplateItem·Standard 읽기 전용 접근.

이 도메인 자체는 케이스 접수 시점의 참조 데이터(레일 템플릿 라이브러리)라 쓰기 API가
없다(시드로만 채운다). case 도메인이 apply_profile·배지 조립에 이 리포지토리를 주입받아 쓴다.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalog.models import Profile, Standard, TemplateItem


class CatalogRepository:
    """Profile/RailTemplate/TemplateItem/Standard 조회. stateless."""

    async def get_profile(self, db: AsyncSession, profile_id: int) -> Profile | None:
        """프로파일 조회 — Case 접수 시 rail_map 적용원."""
        return await db.get(Profile, profile_id)

    async def list_template_items(
        self, db: AsyncSession, rail_template_id: int
    ) -> list[TemplateItem]:
        """레일 템플릿의 항목 정의 목록 — Case 접수 시 Item으로 복제된다."""
        result = await db.execute(
            select(TemplateItem).where(
                TemplateItem.rail_template_id == rail_template_id
            )
        )
        return list(result.scalars().all())

    async def get_standards_by_ids(
        self, db: AsyncSession, standard_ids: list[int]
    ) -> list[Standard]:
        """근거 배지 조립용 — Item.standard_ids가 가리키는 Standard 레코드 일괄 조회."""
        if not standard_ids:
            return []
        result = await db.execute(select(Standard).where(Standard.id.in_(standard_ids)))
        return list(result.scalars().all())
