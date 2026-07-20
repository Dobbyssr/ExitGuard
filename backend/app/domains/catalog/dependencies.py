"""catalog 도메인 repository provider(FastAPI Depends)."""

from app.domains.catalog.repository import CatalogRepository


def get_catalog_repository() -> CatalogRepository:
    """CatalogRepository provider — stateless라 매 요청 새로 만들어도 싸다."""
    return CatalogRepository()
