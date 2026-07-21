"""evidence 도메인 provider(FastAPI Depends).

EvidenceService는 case 존재 확인·상태 조회를 위해 CaseRepository가, 방어 리포트(export)의
레일 배지 조립을 위해 CatalogRepository가 필요하다(도메인 간 repository 의존은 허용,
backend/CLAUDE.md §1). case.dependencies를 import하면 case.dependencies↔evidence.dependencies
상호 import로 순환참조가 생기므로, 여기서는 각 도메인 repository 클래스만 직접 가져와
조립한다(전부 stateless라 Depends 불필요).
"""

from app.domains.case.repository import CaseRepository
from app.domains.catalog.repository import CatalogRepository
from app.domains.evidence.repository import EvidenceRepository
from app.domains.evidence.service import EvidenceService


def get_evidence_repository() -> EvidenceRepository:
    """EvidenceRepository provider."""
    return EvidenceRepository()


def get_evidence_service() -> EvidenceService:
    """EvidenceService provider — 세 리포지토리 모두 stateless라 직접 조립한다."""
    return EvidenceService(EvidenceRepository(), CaseRepository(), CatalogRepository())
