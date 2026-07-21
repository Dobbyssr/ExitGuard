# 스네이프 DB 감수 리포트 — Round 4 (compare 엔진 · LaborPrecedent 코퍼스)

- **감수 일자:** 2026-07-21 (게이트 라벨 2026-07-20)
- **감수자:** 스네이프 (DB 공학 감수·자문)
- **감수 대상 (론 구현, 커밋 전):**
  - `backend/app/domains/labor/models.py` — `LaborPrecedent` + enum `LaborCaseType`(18)·`LaborRequiredElement`(3)·`LaborDeadlineRule`(6) · `DISMISSAL_CASE_TYPES`
  - `backend/alembic/versions/cdc2ffe29606_labor_precedent_corpus.py` — `labor_precedents` 신규 리비전
  - `backend/app/domains/labor/repository.py` — `find_by_element_and_categories`(JSONB `@>` + category IN)
  - `backend/app/domains/catalog/repository.py` — `list_standards(rail, titles)` 추가
  - `backend/scripts/seed.py` — Standard L1×3/L2/L3 · LaborPrecedent 51·388 · 노무 6항목 §2-1 정정 · detail_schema
- **계약 SSOT:** `docs/spec/노무/data-model.md` §4·§4-1·§4-2·§4-3·§5 · 코어 §0/§7 · round1~3 리포트
- **실물 대조:** docker `exitguard-postgres-1`(5433), 리비전 `cdc2ffe29606`(head) 적용 상태. `psql`로 스키마·CHECK·인덱스·`EXPLAIN ANALYZE` 직접 확인 · `alembic check`(드리프트 0) · `pytest`(44 passed) · 시드 멱등성.
- **종합 판정:** **OK (재설계 불요)** — 🔴 0 · 🟡 0 · 🔵 3(전부 Post-MVP) · **[결정필요] 1(`decided_on` 계약 델타).** 무결성 치명 이슈 없음. 도비가 판정 요청한 4개 지점 전부 **DB 공학 관점에서 현행 구현이 옳다**(계약 델타 1건만 헤르미온느 조율 필요).

---

## A. 도비 판정 요청 4건 (직접 답변)

### A-1. `decided_on` nullable — 계약 §4 ●필수 ↔ 구현 nullable · **[결정필요] · DB 관점: nullable이 옳다**

- **판정: nullable 유지가 DB 무결성 관점에서 정답이다. 계약(§4 표 ●)을 ○(또는 "CSV상 필수·미보유 시 null")로 완화하는 쪽을 권고한다.**
- **근거(NOT NULL의 의미론):** `NOT NULL`은 "이 값이 **항상 실재한다**"는 불변식을 DB가 강제하는 제약이다. 순번 388은 원본 CSV 미보유로 작성일자가 **실재하지 않는다**(§4-3 표가 이 행에 작성일자를 주지 않음). 여기에 NOT NULL을 걸면 결과는 둘 중 하나다 — (a) 정당한 코퍼스 행의 적재가 제약 위반으로 **차단**되거나, (b) `1900-01-01` 같은 **가짜 센티널 날짜를 창작**해 넣게 된다. (b)는 null보다 **더 나쁜 무결성 훼손**이다: null은 정직한 "미상(unknown)"이지만, 가짜 날짜는 **데이터가 거짓말을 하는 것**이고 이후 정렬·필터·표기에서 조용히 오염을 퍼뜨린다. 이건 관계형 이론의 교과서적 "NULL = unknown" 사례다.
- **정합 근거(이미 선례 있음):** 같은 테이블의 `case_no`가 **정확히 같은 논리로 nullable**이다 — 약 73%에 사건번호가 없어(§4-2), 없는 값을 창작하지 않고 null로 둔다. `decided_on`도 동일 원칙의 적용일 뿐이다. **두 컬럼을 다르게 취급할 DB 근거가 없다.**
- **하방 리스크 점검:** `decided_on` null이 깨뜨리는 것은 없다. LaborPrecedent는 게이트 집계·증적 봉인 대상이 아니고(§4 주석), compare `risk` 행은 "…판정된 사례가 있습니다" 프레이밍이라 날짜 없이도 성립한다(§5-3). 유일한 앱단 주의점: 날짜를 렌더하는 코드가 있다면 null 가드 필요 — 그러나 이는 제약 문제가 아니라 표현 계층 문제다.
- **도비 의견(창작금지 우선 → nullable 수용)에 DB 관점에서 동의한다.** 이건 "구현이 계약을 못 지킨" 델타가 아니라 "계약의 ● 표기가 데이터 현실과 어긋난" 델타다. **헤르미온느가 §4 표의 `decided_on ●`를 `○`(또는 각주로 "미보유 시 null 허용")로 정정**하면 계약↔구현이 일치한다. → **[결정필요]로 도비에게 올림.**

### A-2. `matched_elements` JSONB 배열 — round2 `standard_ids` 판정 동일 적용 · **MVP 수용 [지금 필요 유지]**

- **판정: round2 B-2(`standard_ids` JSONB 배열 MVP 수용)와 **동일 판정 적용이 맞다.** 폐집합 어휘라는 론 주장 타당.**
- **근거:** 배열 원소 값이 `LaborRequiredElement.written_notice.value` 등 **enum에서 나오는 폐집합**(3종)이고, 시드 경로에서만 쓰기가 일어나 쓰기 시점에 앱 코드가 어휘를 보증한다. `category`(스칼라 enum)에는 CHECK가 걸렸지만 **JSONB 배열 원소에는 DB 레벨 도메인 제약이 없다**(값오염을 DB가 못 막음) — 이는 round2에서 `standard_ids` int 배열을 수용할 때 이미 받아들인 트레이드오프와 동일하다. M2M 조인테이블(`precedent_element`)을 지금 만들 이유가 없다(역조회 수요 0·읽기 전용 코퍼스·YAGNI).
- **주의(팀 인지 조건):** DB가 배열 원소 도메인을 강제하지 않으므로, **399행 CSV 벌크 적재(Post-MVP) 시 적재 스크립트가 원소를 `LaborRequiredElement` enum에 대조 검증**해야 한다(DB가 안 잡아줌). 시드 2행은 enum 상수로 하드코딩돼 안전. → A-3의 🔵-2 참조.

### A-3. JSONB `.contains()` 코퍼스 필터 쿼리 — **GIN 없이 정상 · 현행 유지 [지금 필요 없음]**

- **판정: GIN 인덱스 유보가 정확하다. 현행 seq scan이 최적.** 성능·정합 문제 없음.
- **실물 근거(`EXPLAIN ANALYZE`):**
  ```
  Seq Scan on labor_precedents (cost=0.00..15.78 rows=2)
    Filter: (matched_elements @> '["written_notice"]'::jsonb
             AND category = ANY('{disciplinary_dismissal,ordinary_dismissal,
                                  managerial_dismissal,ex_officio_dismissal}'))
    Buffers: shared hit=1   Execution Time: 0.037 ms
  ```
  코퍼스 2행에서 GIN 인덱스는 **절대 선택되지 않고**(플래너가 tiny table엔 seq scan이 싸다고 정확히 판단), 인덱스를 만들면 쓰기 비용·용량만 늘 뿐 이득 0. 론의 ponytail 유보가 정확.
- **정합 검증:** `.contains([element.value])`가 JSONB `@>` 연산자로 번역됨을 확인 — `["written_notice"] @> ["written_notice"]` = true, 다원소 배열도 부분포함 판정 정확. EXPLAIN에서 2행 정확 반환. `category.in_(DISMISSAL_CASE_TYPES)`도 해고계열 4종으로 정확히 필터(§4-1 해고계열 정의 일치). `order_by(seq)`로 인용 재현성 보장.
- **Post-MVP 태그(약하게):** 399행 전량 적재 시에도 seq scan은 여전히 1ms 미만이라 **GIN은 그때도 사실상 YAGNI**다. GIN이 실익을 갖는 건 코퍼스가 **수만 행**에 도달하고 이 쿼리가 hot path가 될 때뿐 — 중노위 CSV는 399행 상한이라 그 시나리오는 오지 않는다. → **GIN [Post-MVP · 사실상 불요]**로 태그하되 강권하지 않음.

### A-4. `case_id` 없는 참조 코퍼스 · `category` 인덱스 · `seq` UNIQUE — **규약 위배 아님 · 전부 적절**

- **case_id 부재 = 규약 위배 아님(정당한 예외 확인).** FK/증적 규약은 **케이스 종속 운영 데이터**(Item·Approval·Evidence)에 적용되는 것이다. `LaborPrecedent`는 봉인(sealed) 대상도, 게이트 집계 대상도, Approval 대상도 아닌 **참조 코퍼스(lookup/reference table)**다(§4 주석). 운영 테이블로의 FK가 없는 참조 테이블은 관계형 설계에서 완전히 표준(국가코드·법령 코퍼스 등과 동형). TS `TradeSecretAsset` 선례와 동일 개념. **증적 규약(seq 단조·prev_hash 체인)은 `Evidence` 엔티티의 것**이지 코퍼스와 무관 — 적용 대상 자체가 아니다.
- **`seq` UNIQUE = 정확.** `seq`는 CSV `순번`(외부 자연키)라 코퍼스 내 유일해야 정상. PK는 대리키 `id`(autoincrement)로 두고 `seq`에 UNIQUE를 별도로 건 것이 **정석**이다 — 외부에서 재번호될 수 있는 자연키를 PK로 삼지 않고 대리키와 분리한 것은 모범.
- **`category` 인덱스(`ix_labor_precedents_category`) = 무해, 유지.** 2행에선 무의미하고, 399행에서도 해고계열 IN이 ~37% 선택도(148/399)라 플래너가 seq scan을 고를 가능성이 높아 **선택도상 이득은 경계선**이다. 다만 코퍼스는 쓰기가 극히 드문 append-rare 테이블이라 인덱스 유지비가 사실상 0이고, "category가 지배적 필터 경로"라는 **설계 의도를 문서화**하는 값이 있다. 드롭할 실익이 없어 **현행 유지**(churn 불요).

---

## B. 6렌즈 추가 감수

### B-1. 스키마 위생 — ✅ 실물 전수 확인
- CHECK `ck_labor_precedents_laborcasetype` = **LaborCaseType 18종 전수** VARCHAR+CHECK IN(...)로 생성(`native_enum=False` 원칙 계승, round2 C-1 일관). `category` = `varchar(22)` = 최장 enum값(`disciplinary_dismissal`=22자)에 정확히 사이징.
- PK(`id`)·UNIQUE(`seq`)·index(`category`) 실물 확인. `ingested_at` `server_default=now()` + `timezone=True`(UTC, backend §9 준수).
- **드리프트 0:** `alembic check` → "No new upgrade operations detected". 모델↔DB 일치.
- **리비전 위생:** 체인 `base → af86fe666b76 → cdc2ffe29606(head)` 단일 head. `down_revision=af86fe666b76`(round2 코어 스키마) **정확**. `downgrade()`가 index drop → table drop 역순 **완결**. autogenerate 깨끗(손편집 흔적 없음).

### B-2. 🔵 `is_seed` server_default 부재 — [Post-MVP] (round2 C-4b와 동일 성격)
- `is_seed`는 Python-side `default=False`만 있고 `server_default` 없음(migration `nullable=False`). ORM INSERT엔 항상 값이 들어가 문제없고, 시드 2행은 `is_seed=True` 명시. **단 399행 벌크 적재를 COPY/raw로 하면** `is_seed` 미지정 시 NOT NULL 위반. `ingested_at`은 `server_default`가 있는데 `is_seed`는 없어 비대칭. → **[Post-MVP]** 벌크 적재 파이프라인 도입 시 `server_default=false` 추가(지금은 ORM 경유라 실害 없음, 🔵).

### B-3. 🔵 배열 원소 도메인 미강제 — [Post-MVP] (A-2 재확인)
- `matched_elements`(list[str])·round2 `standard_ids`(list[int]) 공통 — DB가 배열 원소 값을 검증 못 함. MVP 시드 경로는 enum 상수라 안전. **[Post-MVP]** 벌크 적재 시 적재 스크립트가 enum 대조 검증 책임(DB 아닌 앱이 보증). GIN+CHECK나 trigger로 DB 강제는 이 규모에 과함(오버엔지니어링, 불요).

### B-4. 🔵 `standards` 인덱스 부재 — `list_standards` 쿼리 [Post-MVP · 사실상 불요]
- `catalog.list_standards(rail, titles)`가 `standards`를 `rail=? AND title IN(...)`로 필터 → `EXPLAIN` seq scan(인덱스 없음). **standards는 5행 읽기 전용 시드**라 seq scan이 정답(인덱스 만들면 손해). 회사 커스텀 Standard로 테이블이 커지면(Post-MVP) `(rail)` 인덱스 고려 — 지금은 **불요**.

### B-5. 타입·nullable 계약 일치 — ✅
- `seq`(int NOT NULL·UNIQUE)·`category`(enum NOT NULL·CHECK)·`title`/`committee`(str NOT NULL)·`matched_elements`(jsonb NOT NULL)·`is_seed`(bool NOT NULL) = 계약 §4 ● 일치. `views`(int null)·`case_no`(str null) = ○ 일치. `decided_on`만 델타(A-1).
- `views` int32 = 조회수 범위 안전(BIGINT 불요). `title` 무제한 varchar = PG에서 정상(길이 제한 불필요).

---

## 의도적 비정규화 인정 (정당)
1. **`matched_elements` JSONB 배열(폐집합 어휘)** — 조인테이블 없이 읽기 전용 코퍼스 참조. 값오염 위험은 시드 경로 enum 상수로 통제. round2 `standard_ids` 판정 계승 — MVP 정당(벌크 적재 시 앱단 검증 조건).
2. **`case_id` 부재 참조 코퍼스** — 케이스 비종속 lookup 테이블. FK/증적 규약 적용 대상 아님(§4 주석). 정당한 예외 확인.

## [결정필요] — 도비 → 헤르미온느 조율
- **`decided_on` 계약 델타 1건.** DB 무결성 관점 결론: **nullable이 옳다**(NOT NULL은 순번 388에서 날짜 창작을 강요 → null보다 나쁜 오염). `case_no` nullable과 동일 논리. **헤르미온느가 §4 표의 `decided_on ●`를 `○`(또는 "미보유 시 null 허용" 각주)로 정정**하여 계약↔구현 일치 권고. (구현 수정 불요 — 계약 문구 정정만.)

---

## 다음 라운드 예약 / 인계
- round2 A-1 인계(증적 seq `FOR UPDATE` 직렬화)·C-3(목록 게이트 N+1)는 **이번 대상(코퍼스·compare 조회)과 무관** — LaborPrecedent는 쓰기 없는 읽기 전용 코퍼스라 동시성·채번 이슈 없음. 해당 인계는 case/evidence 서비스 라운드에서 계속 유효.
- compare 서비스 계층(신호추출→매핑→5행 조립)의 트랜잭션·조회 조합 감수는 서비스 감수 라운드 대상(이번은 DB 산출물 한정).
