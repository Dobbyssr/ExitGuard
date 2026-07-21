"""pytest 공용 픽스처.

API 테스트는 실제 `exitguard_test` DB에 대해 돈다(mock 아님) — apply_profile·상태전이·
증적 해시체인처럼 실제 트랜잭션·락 동작을 검증해야 하는 구간이 많아서다. Unit 테스트는
service+Mock repo로 별도(테스트 DB 불필요).

backend/CLAUDE.md §14: 테스트 DB는 개발 DB와 분리(`DB_NAME.endswith("_test")` 가드) — 이
가드를 어기면(개발 DB를 가리키면) 테스트 세션 자체를 기동하지 않는다(assert, §0).
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db import Base, get_db

# 모든 도메인 모델을 import해야 Base.metadata에 테이블이 등록된다(alembic/env.py와 동일 이유).
from app.domains.case import models as _case_models  # noqa: F401
from app.domains.catalog.models import (
    Profile,
    RailTemplate,
    Standard,
    StandardTier,
    TemplateItem,
)
from app.domains.evidence import models as _evidence_models  # noqa: F401
from app.domains.labor import models as _labor_models  # noqa: F401
from app.domains.shared.enums import ItemKind, Rail
from app.domains.user.models import Role, User
from app.main import app


def _test_database_url() -> str:
    """dev DB URL에서 `_test` 접미 DB URL을 파생한다."""
    base = settings.database_url
    scheme_and_host, _, db_name = base.rpartition("/")
    if db_name.endswith("_test"):
        return base
    return f"{scheme_and_host}/{db_name}_test"


TEST_DATABASE_URL = _test_database_url()
# 개발 DB 오염 방지 가드(브리프 인계분) — `_test`로 끝나지 않으면 테스트 자체를 막는다.
assert TEST_DATABASE_URL.rsplit("/", 1)[-1].endswith("_test"), (
    "테스트 DB가 아닙니다 — DATABASE_URL이 `_test`로 끝나야 합니다(개발 DB 오염 방지 가드)"
)


# NullPool — 테스트마다 새 커넥션을 열고 닫는다. 풀링된 커넥션을 여러 테스트/세션이
# 돌려쓰면(특히 동시성 테스트의 asyncio.gather와 섞일 때) 드물게 stale 커넥션 재사용발
# 레이스가 나서(관찰됨: 산발적 MissingGreenlet), 디스포저블 테스트 DB에서는 안전을 우선한다.
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _schema() -> AsyncGenerator[None, None]:
    """세션당 1회 — 디스포저블 테스트 DB에 스키마를 만든다(Alembic 아닌 create_all).

    ponytail: 프로덕션 스키마 관리는 Alembic 전용(backend/CLAUDE.md NEVER: create_all).
    여기는 매 테스트런마다 버려지는 격리된 `_test` DB라 create_all이 더 빠르고 단순하다 —
    "테스트 DB 부트스트랩"과 "운영 스키마 관리"는 다른 문제.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _truncate_after_each() -> AsyncGenerator[None, None]:
    """테스트 간 격리 — 매 테스트 후 전 테이블 비우기."""
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """앱의 get_db와 동일한 커밋/롤백 규약으로 테스트 DB 세션을 제공."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """API 테스트용 httpx 클라이언트 — get_db만 테스트 DB로 override."""
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded() -> dict:
    """API 테스트 최소 픽스처 — admin/user 1명씩 + 노무 템플릿 2항목 + 프로파일 1개.

    ORM 인스턴스를 그대로 반환하면 세션 종료 후 DetachedInstanceError가 나므로 원시값만 dict로.
    """
    async with TestSessionLocal() as session:
        admin = User(name="관리자", email="admin@test.example", role=Role.admin)
        operator = User(name="담당자", email="operator@test.example", role=Role.user)
        session.add_all([admin, operator])
        await session.flush()

        standard = Standard(
            tier=StandardTier.L1,
            rail=Rail.labor,
            title="근로기준법 제36조",
            source_url="https://law.go.kr/x",
            version="v2026.06",
        )
        session.add(standard)
        await session.flush()

        rail_template = RailTemplate(
            rail=Rail.labor, name="테스트 노무 템플릿", is_base=True
        )
        session.add(rail_template)
        await session.flush()

        template_items = [
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-01",
                name="금품청산",
                kind=ItemKind.statutory,
                blocking=True,
                standard_ids=[standard.id],
            ),
            TemplateItem(
                rail_template_id=rail_template.id,
                code="L-08",
                name="이직확인서 발급",
                kind=ItemKind.recommended,
                blocking=False,
                standard_ids=None,
            ),
        ]
        session.add_all(template_items)
        await session.flush()

        profile = Profile(
            name="테스트 프로파일",
            job="개발",
            rank="사원",
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
            "rail_template_id": rail_template.id,
        }
        await session.commit()
        return result
