"""case 도메인 provider(FastAPI Depends).

CaseService는 증적 자동봉인을 위해 EvidenceRepository가 필요하다(도메인 간 repository
의존은 허용, service→service 금지 — backend/CLAUDE.md §1). evidence.dependencies를
import하면 순환참조가 생기므로(evidence.dependencies도 case.repository를 가져다 쓴다),
여기서는 evidence.repository의 클래스만 직접 가져와 조립한다(stateless라 Depends 불필요).
"""

from app.domains.case.repository import CaseRepository
from app.domains.case.service import CaseService
from app.domains.catalog.repository import CatalogRepository
from app.domains.evidence.repository import EvidenceRepository


def get_case_repository() -> CaseRepository:
    """CaseRepository provider."""
    return CaseRepository()


def get_case_service() -> CaseService:
    """CaseService provider — 세 리포지토리 모두 stateless라 직접 조립한다."""
    return CaseService(CaseRepository(), CatalogRepository(), EvidenceRepository())
