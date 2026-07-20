# Backend — ExitGuard API 규약

> `backend/` 코드 작업의 최상위 규칙. 기본 습관보다 우선하며, 어기려면 근거를 대고 합의한다.
> 제품·조직·커밋 규칙은 루트 `../CLAUDE.md`·`../ONBOARDING.md`.
> **철학: 가독성 > 영리함. 단순함 > 유연함. 지금 필요 없는 추상화는 안 만든다(YAGNI).** 위에서 아래로 읽어 무엇이 어디서 오는지 추적되게 — 마법 금지.

## 0. 스택 (확정)

| 항목 | 스택 |
|------|------|
| 언어 | Python 3.12 · `uv` |
| 웹 | FastAPI + uvicorn |
| DB | PostgreSQL (호스트 포트 5433, docker-compose) |
| 드라이버/ORM | **asyncpg** + **SQLAlchemy 2.0 async** (`Mapped[...]`) |
| 스키마 | **Pydantic v2** (ORM과 분리) |
| 마이그레이션 | **Alembic** autogenerate |
| 설정 | pydantic-settings |
| 캐시 | Redis (필요 시) |

### ⚠️ 스캐폴드 → 목표 이관 (안 됐으면 도메인 개발 전에 먼저)
현 `app/`는 동기 스택. 전환: `pg8000`→**asyncpg**(libpq 미사용 → Windows 로케일 UTF-8 버그 회피) · `sqlmodel`→**sqlalchemy[asyncio]+pydantic** · `create_engine/Session`→`create_async_engine/AsyncSession` · `on_event`→**lifespan** · `create_all`→**Alembic upgrade head**.
`DATABASE_URL = postgresql+asyncpg://exitguard:exitguard@localhost:5433/exitguard`.

## 1. 아키텍처: 3레이어 단방향

```
router → service → repository → DB
(I/O)   (비즈니스)  (DB 접근)
```
역방향·레이어 건너뛰기 금지.

| 레이어 | 하는 일 | 금지 |
|--------|---------|------|
| **router** | HTTP 요청/응답, 스키마 검증, 예외→상태코드 | 비즈니스 로직, SQLAlchemy 직접 |
| **service** | 비즈니스 규칙·검증·조합·트랜잭션 단위 | `sqlalchemy`/`fastapi` import, 타 도메인 **service** 직접 호출 |
| **repository** | SQLAlchemy 쿼리, ORM 반환 | 비즈니스 규칙, HTTP/외부 API |

**도메인 간 의존**: 타 도메인 데이터가 필요하면 그 도메인의 **repository**를 주입받는다. service→service 직접 호출 금지(순환·경계 붕괴). ✅ `CaseService→EvidenceRepository` / ❌ `CaseService→EvidenceService`.

## 2. 폴더 구조 — 레이어별 아니라 **도메인별**

```
app/
├── main.py        # 앱 조립(lifespan·라우터·미들웨어·예외핸들러)
├── config.py      # pydantic-settings Settings (단일 진실 원천)
├── db.py          # async 엔진·세션팩토리·get_db
├── core/          # dependencies(공통 Depends)·middleware(request_id·CORS)·exceptions(전역 핸들러)
└── domains/
    ├── shared/exceptions.py   # 도메인 공통 예외
    └── <domain>/              # case, compare, evidence, rails ...
        ├── models.py       # SQLAlchemy ORM
        ├── schemas.py      # Pydantic DTO
        ├── repository.py   # SQLAlchemy 쿼리
        ├── service.py      # 비즈니스 로직
        ├── router.py       # 라우터
        └── dependencies.py # 이 도메인 repo/service provider
```
> 이관: 평면 `app/services/{case,compare,evidence,rails}.py` → `domains/<x>/service.py`. `health` 등 인프라 엔드포인트는 도메인 밖에 남겨도 됨. 기존 docstring의 유비쿼터스 언어(레일=노무/영업비밀/보안) 정의는 계승.

## 3. 의존성 주입 — FastAPI `Depends()`만

도메인별 `dependencies.py`에 provider 함수를 둔다: `get_<x>_repository()`가 repository 반환, `get_<x>_service(repo=Depends(...))`가 조립. 라우터는 `Depends(get_x_service)`로 주입(데코레이터·`Provide[]` 없음). 테스트는 `app.dependency_overrides[...]`로 교체.
- **DB 세션은 요청마다 새로(Factory), 커넥션 풀·외부 클라이언트는 공유(Singleton)** — Redis 등 싱글턴은 모듈 레벨 + `@lru_cache(maxsize=1)` provider. service/repository는 stateless라 요청마다 새로 만들어도 싸다.

## 4. Repository — DB 접근 격리 (클래스 하나)

- repository는 SQLAlchemy 쿼리를 담는 클래스 하나. **MVP는 구현이 하나뿐 → `Protocol` 인터페이스를 만들지 않는다**(구현이 둘 이상 생기면 그때 도입). 테스트는 `dependency_overrides`로 fake repo를 갈아끼우면 되고, 덕타이핑이라 Protocol 없이 동작한다.
- **stateless** — 세션을 필드에 저장하지 말고 **메서드 인자로 받는다**.
- `flush()`까지만. `commit()` 금지(요청 단위로 `get_db`가 책임, §5).
- 쿼리는 `select()` (SQLAlchemy 2.0). 레거시 `session.query()` 금지.
- 반환은 ORM 객체/원시값. Pydantic 변환은 router.

## 5. DB 세션 — 요청 1개 = 트랜잭션 1개 (`app/db.py`)

- `create_async_engine(settings.database_url, pool_pre_ping=True, pool_recycle=300)` + `async_sessionmaker(expire_on_commit=False)`.
- `get_db()`: 요청별 `AsyncSession` 제공 — 성공 시 `commit`, 예외 시 `rollback` 후 re-raise.
- **`expire_on_commit=False`**: commit 후 ORM 속성 접근 가능(직렬화 시 lazy-load 500 방지).
- 세션은 항상 `Depends(get_db)`로 주입 → service 메서드 인자로 전달.
- 엔진 init/dispose는 `main.py` **lifespan**에서 (`on_event` 금지). 스키마는 Alembic — lifespan에서 `create_all` 하지 않는다.

## 6. Router — 얇게

입력 검증(Pydantic) → service 호출 → 도메인 예외를 HTTP로 번역 → 응답 스키마 변환. 그게 전부.
- 모든 엔드포인트에 `response_model` + 반환 타입힌트.
- service는 도메인 예외(§7)를 던지고 router가 `HTTPException`으로 변환. **service 안에서 `HTTPException` 금지.**
- `raise ... from e`로 원인 체인 보존. 경로/쿼리 파라미터는 타입힌트로 자동 검증.

## 7. 예외 — 도메인 예외 → 전역 핸들러

- `app/domains/shared/exceptions.py`: `DomainError`(기반) → `NotFoundError`(404)·`DuplicateError`(409)·`InvalidStateError`(409/422).
- service가 던지고 router가 상태코드 매핑.
- 미처리 예외는 `core/exceptions.py` 전역 핸들러가 표준 JSON(`error`·`message`·`request_id`) 500 + `exc_info=True` 로깅. **스택트레이스 클라이언트 노출 금지.** 조립 시 `register_exception_handlers(app)`로 형식 통일.

## 8. 설정 — pydantic-settings 단일 원천 (`app/config.py`)

- 모든 설정을 `Settings(BaseSettings)` 한 곳에. `os.getenv()` 산재 금지. 조합 값은 `@property`.
- `.env` 커밋 금지(`.gitignore`), `.env.example`만. **비밀키·크리덴셜 절대 커밋 금지.**
- 위험 설정은 **기동 시 validator로 차단**(런타임에 조용히 잘못 도느니 시작 시 크게 죽는다).

## 9. 모델 · 10. 스키마

- SQLAlchemy 2.0 `Mapped[...]` + `mapped_column`. `Base(DeclarativeBase)`에 `NAMING_CONVENTION` 적용. `TimestampMixin`(created/updated). 시간 컬럼 항상 `timezone=True`(UTC).
- 스키마 변경은 **Alembic autogenerate만** — `versions/` 손편집 금지.
- 스키마 명명 `<Model><용도>`(`CaseCreate`/`CaseResponse`). ORM→응답은 `ConfigDict(from_attributes=True)` + `model_validate`.
- **ORM 모델을 응답으로 직접 반환 금지** — 응답 스키마 경유로 노출 필드 통제(민감 필드 유출 방지). 부분 수정은 `model_dump(exclude_unset=True)`.

## 11. 신규 도메인 절차 (순서 고정)

`models → schemas → repository → service → dependencies → router → main.include_router → alembic --autogenerate`. router에서 provider 쓰기 전에 `dependencies.py`를 먼저 만든다.
> **DB 감수 게이트**: DB 산출물(`models`·Alembic 마이그레이션·비자명한 쿼리)은 도비 최종 승인 전 **스네이프 DB 감수**(정규화·인덱스·쿼리성능·무결성)를 거친다.

## 12. 네이밍

| 대상 | 규칙 · 예 |
|------|-----------|
| 도메인 폴더 | `snake_case` — `case` |
| ORM 모델 | `PascalCase` — `Case` |
| 스키마 | `<Model><용도>` — `CaseCreate` |
| Repository | `CaseRepository` |
| Service / provider | `CaseService` / `get_case_service` |

## 13~16. 로깅 · 비동기 · 테스트 · 도구

- **로깅**: `logging.getLogger(__name__)`, **`print()` 금지**. 구조화 `extra={...}`. 에러는 `exc_info=True`. 비밀/개인정보 로깅 금지. `request_id`를 미들웨어에서 부여·추적.
- **비동기**: I/O(DB·HTTP·Redis) 전부 `async`. 동기 블로킹 호출 금지(불가피하면 `anyio.to_thread.run_sync`). HTTP는 `httpx.AsyncClient`(`requests` 금지).
- **테스트**: `pytest`+`pytest-asyncio`+`httpx`. Unit=service+Mock repo / Integration=repository+실 테스트DB / API=router+`dependency_overrides`. **테스트 DB는 개발 DB와 분리**(`DB_NAME.endswith("_test")` 가드). 파일명 `test_<동작>_when_<조건>_<기대>`.
- **도구**: 포맷·린트·임포트 `ruff`(`ruff format` + `ruff check`), 타입 `mypy`. 모든 시그니처 타입힌트 + 한 줄 docstring(`"""동사+목적어."""`). **왜(why)만** 주석. 커밋 전 `ruff format --check . && ruff check . && mypy app && pytest`.

## 17. 제품 규율 (반드시)

ExitGuard는 법률·노무 **"판단"을 하지 않는다.** '진단'조차 안 쓴다 — 공개 기준과 회사 상태의 **대조·기한·기록**만. API 필드명·에러 메시지·enum·description에 판단/진단/조언 함의 표현 금지. 상세 `../dobby/PRODUCT.md §4`. 위반 = 직역법 위반 + 심사 즉사.

## NEVER / ALWAYS

**NEVER** — DI 컨테이너 라이브러리 · 동기 DB 드라이버 회귀 · 레이어 건너뛰기 · 도메인 간 service 직접 호출 · service/repository의 `commit()` · service 안 `HTTPException` · ORM 직접 반환 · `@app.on_event` · `create_all` 스키마 관리 · `print()`/비밀정보 로깅 · `os.getenv()` 산재 · `.env`/비밀키 커밋 · 판단·진단 함의 표현 · YAGNI 위반(선구현).

**ALWAYS** — router→service→repository 단방향 · 세션은 `Depends(get_db)`→인자 전달 · repository stateless·`flush`까지 · 도메인별 `dependencies.py` provider · 엔드포인트마다 `response_model`+반환 타입힌트 · 전역 예외 핸들러+`request_id` · 설정은 pydantic-settings 한 곳+기동 validator · 시그니처 타입힌트+docstring · 커밋 `<타입>(be): 요약`.
