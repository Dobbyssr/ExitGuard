"""compare 도메인 provider(FastAPI Depends).

CompareService는 노무 코퍼스(LaborRepository)·근거(CatalogRepository)·케이스(CaseRepository)·
증적(EvidenceRepository) 네 리포지토리가 필요하다(도메인 간 repository 의존은 허용,
service→service 금지 — backend/CLAUDE.md §1). 전부 stateless라 직접 조립한다.
"""

from app.domains.case.repository import CaseRepository
from app.domains.catalog.repository import CatalogRepository
from app.domains.compare.service import CompareService
from app.domains.evidence.repository import EvidenceRepository
from app.domains.labor.repository import LaborRepository


def get_compare_service() -> CompareService:
    """CompareService provider."""
    return CompareService(
        CatalogRepository(), LaborRepository(), CaseRepository(), EvidenceRepository()
    )
