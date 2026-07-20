# 스네이프 DB 감수 리포트 — Round 2 (코어 ORM 9엔티티 + Alembic 리비전)

- **감수 일자:** 2026-07-20
- **감수자:** 스네이프 (DB 공학 감수·자문)
- **감수 대상 (론 구현):**
  - `backend/app/db.py`(`TimestampMixin`)
  - `backend/app/domains/shared/enums.py`(`Rail`·`ItemKind`)
  - `backend/app/domains/user/models.py`(`User`·`Role`)
  - `backend/app/domains/catalog/models.py`(`Standard`·`RailTemplate`·`TemplateItem`·`Profile`)
  - `backend/app/domains/case/models.py`(`Case`·`Item`·`Approval` + 로컬 enum 5종)
  - `backend/app/domains/evidence/models.py`(`Evidence` + enum 2종)
  - `backend/alembic/versions/a3084daccbfd_core_schema_*.py`(리비전) · `backend/alembic/env.py`(모델 배선)
- **계약 SSOT:** `docs/spec/data-model.md`(§0·§2·§3·§3-1-1·§3-4-1·§5·§9-R)
- **실물 대조:** docker `exitguard-postgres-1`(5433), 리비전 `a3084daccbfd` 적용 상태에서 `psql`로 인덱스·CHECK·FK 삭제규칙 직접 확인.
- **종합 판정:** **OK (Warning 경미)** — 🔴 0건(무결성 치명 이슈 없음) · 🟡 2건 · 🔵 3건 · **HANDOFF 1건(다음 task 게이트).** round1 무결성 계약 3건이 코드에 **정확히 착지**했다. 남은 것은 (1) 중복 인덱스 1개 정리와 (2) seq 채번 직렬화가 **모델이 아닌 서비스 계층 사안**이라 다음 task에서 반드시 구현돼야 한다는 인계뿐이다.

---

## A. round1 반영분 코드 착지 확인 (도비 지시 필수 항목)

### A-1. 🔴-1 증적 seq 채번 동시성 — **절반 착지 (모델은 완료, 직렬화는 서비스 미구현) · HANDOFF**
- **✅ 착지:** `UNIQUE(case_id, seq)` — `evidence/models.py:44` `UniqueConstraint("case_id","seq", name="uq_evidence_case_id_seq")` + 마이그레이션 `:260` + **실물 확인**(`uq_evidence_case_id_seq` 인덱스 존재). 동시 append의 "조용한 체인 분기"가 IntegrityError로 드러나는 방어가 DB 레벨에 걸렸다.
- **⚠️ 미착지 (설계상 정상 — 모델 소관 아님):** 계약 §3-4-1(2)·§9-R(l)이 요구하는 **채번 직렬화(`SELECT … FOR UPDATE`로 Case 행 잠금 후 `max(seq)+1`)** 는 트랜잭션·쿼리 로직이라 ORM 모델에 존재할 수 없다. 이번 감수 대상엔 없는 게 **맞다.**
- **근거(왜 UNIQUE만으로 부족한가):** UNIQUE 제약은 seq 중복을 *거부*하지만, 동시 두 트랜잭션이 같은 `max(seq)`를 읽으면 **한 쪽은 IntegrityError로 실패(요청 자체가 500/재시도 필요)** 한다. 즉 UNIQUE는 "무결성 붕괴"를 "요청 실패"로 바꿀 뿐, **정상 동작을 보장하지 않는다.** 정상 채번은 `FOR UPDATE` 직렬화가 있어야 성립한다.
- **[지금 필요 · 다음 task 게이트] 인계:** **case/evidence 서비스(증적 자동 봉인 경로)를 구현하는 다음 task에서, 봉인 트랜잭션 시작 시 해당 Case 행을 `SELECT … FOR UPDATE`로 잠그고 그 안에서 `max(seq)+1` 채번 + 같은 트랜잭션에서 append**하는 것을 반드시 구현해야 한다. 이 코드가 없으면 seq 채번은 **레이스에 열려 있고, UNIQUE 위반으로 봉인 요청이 산발 실패**할 수 있다. 서비스 감수(다음 라운드)에서 이 직렬화 존재 여부를 게이트로 확인할 것.
  - repository는 `flush()`까지만·`commit()` 금지(backend §4·§5)이므로, 봉인 append는 mutation과 **동일 `get_db` 트랜잭션** 안에서 일어나야 원자성이 성립한다. 봉인에 별도 커밋을 끼우지 말 것.

### A-2. 🔴-3 인덱스 원칙 — **✅ 완전 착지 (단 items에 중복 1개 · B-1 참조)**
FK·지배적 조회 경로 인덱스를 실물에서 전수 대조:

| FK / 조회경로 | 인덱스 | 상태 |
|---|---|---|
| `cases.created_by` | `ix_cases_created_by` | ✅ |
| `cases.profile_id` | `ix_cases_profile_id` | ✅ |
| `template_items.rail_template_id` | `ix_template_items_rail_template_id` | ✅ |
| `items.case_id` | `ix_items_case_id` (단일) | ✅ 존재하나 **중복** → B-1 |
| `items.(case_id, status)` | `ix_items_case_id_status` (복합) | ✅ 게이트 집계 §5·§3-1-1 커버 |
| `approvals.item_id` | `ix_approvals_item_id` | ✅ |
| `approvals.submitter_id` | `ix_approvals_submitter_id` | ✅ |
| `approvals.reviewer_id` | `ix_approvals_reviewer_id` | ✅ |
| `evidence.(case_id, seq)` | `uq_evidence_case_id_seq` (UNIQUE 겸 조회) | ✅ **별도 case_id 인덱스 안 만든 것이 정답** |

- **`evidence.case_id` 단독 인덱스를 일부러 안 만든 판단이 정확하다.** UNIQUE(case_id, seq)의 리딩 컬럼이 case_id라 `WHERE case_id=? ORDER BY seq`(증적 아카이브 조회 §10)를 이 복합 인덱스가 그대로 커버한다. 중복 회피 정확.

### A-3. 삭제·보존 정책 — **✅ 완전 착지**
- **실물 확인:** 8개 FK 전부 `confdeltype='a'`(**NO ACTION**). CASCADE **0건.**
- `evidence.case_id → cases`·`approvals.item_id → items` 모두 NO ACTION → Case/Item에 봉인 증적·승인 이력이 매달려 있으면 **삭제가 FK 위반으로 차단**된다. 계약 §0(증적 물리 소실 금지·CASCADE 금지)·§9-R(n)과 정확히 일치.
- `Evidence`가 `TimestampMixin`을 **일부러 상속하지 않은 것**도 정확(append-only라 `updated_at` 무의미 — round1 🔵-2 권고 반영). `created_at`류 대신 `sealed_at`·`occurred_at`만 둔 것이 봉인 레코드 성격에 맞다.

---

## B. 도비 판정 요청 3건

### B-1. 🟡 `Item.case_id` 단일 인덱스 + 복합 `(case_id, status)` — **중복. 단일 인덱스 제거 권고 [지금 필요]**
- **판정: 중복이 맞다. `ix_items_case_id`(단일) 제거 권고.**
- **근거(B-tree 리딩 프리픽스):** 복합 인덱스 `(case_id, status)`는 정렬키 순서상 **리딩 컬럼 case_id만으로 하는 조회(`WHERE case_id=?`)를 그대로 커버**한다. 즉 `GET /cases/{id}` 상세의 items 로드, `case.items` 관계 로드 등 case_id 단독 조회는 전부 복합 인덱스가 처리한다. 단일 `ix_items_case_id`가 커버하는 쿼리 집합은 복합 인덱스 커버 집합의 **완전 부분집합** → 순수 중복.
- **비용:** 중복 인덱스는 (1) 매 INSERT/UPDATE마다 유지비용 2배, (2) 저장공간 낭비, (3) 플래너 선택지 혼란. 이득은 0.
- **권고 [지금 필요]:** `case/models.py:99`의 `case_id` 컬럼에서 `index=True` 제거(복합 인덱스 `__table_args__`는 유지) → autogenerate로 `ix_items_case_id` DROP 마이그레이션 생성. **데이터·시드 적재 전인 지금이 가장 싼 시점**이라 [지금 필요]로 분류(단, 무결성 이슈는 아니므로 심각도 🟡). 미룬다고 데이터가 깨지진 않으나, 시드 후엔 정리 명분이 약해진다.
- ※ `Evidence`는 이 함정을 정확히 피했는데(A-2) `Item`만 단일+복합을 둘 다 걸어 일관성이 어긋난 것 — Evidence 방식이 정답이다.

### B-2. 🔵 `standard_ids` JSONB int 배열 (Item·TemplateItem) vs M2M 조인테이블 — **MVP는 JSONB 유지 [지금 필요 유지] / 정규화 [Post-MVP]**
- **판정: MVP는 현행 JSONB int 배열 유지가 맞다.** (round1 🟡-3 판단 계승·확정)
- **근거(트레이드오프):**
  - **참조무결성 부재는 실재하는 비용:** `Standard`가 삭제/교체되면 배열 안 id는 dangling으로 남고, DB가 이를 막지 못한다. 역조회("이 Standard를 참조하는 Item")도 조인으로 못 한다.
  - **그러나 MVP 조회패턴에 정확히 맞다:** `Standard`는 **읽기 전용 시드**(삭제 유스케이스 없음), 배지 렌더는 "Item이 가진 id 목록으로 Standard를 조회"(정방향)뿐이고 역조회 수요가 없다. M2M 조인테이블(`item_standard`)을 지금 만들면 조인 1단 추가·복제 로직 복잡화만 낳고 이득이 없다(YAGNI).
- **권고:** JSONB 유지. 단 **"Standard의 참조무결성을 DB가 아니라 시드 관리로 보증한다"** 는 사실을 팀이 명시적으로 인지할 것(모르고 Standard를 지우면 dangling 배지). **[Post-MVP]** 회사 커스텀 템플릿·Standard 편집 UI가 생기면 조인테이블로 정규화.
- ※ `Profile.rail_map`(JSONB{rail→template_id})도 동일 성격(시드 참조) — 같은 판단 적용.

### B-3. ✅ `User.granted_scopes`를 PG native `ARRAY(String)`으로 — **적절하다. 이견 없음**
- **판정: 적절.** 중첩 구조 없는 평면 문자열 목록이고, 스코프 부여/조회는 "이 유저의 스코프 전체를 읽는다"(행 단위 로드)뿐이라 native array가 JSONB보다 단순·정확하다.
- 컨테인먼트 조회("스코프 X를 가진 유저 전체")가 생기면 GIN 인덱스(`@>`)가 필요하나, MVP에 그런 조회 경로 없음 → **인덱스 불필요(YAGNI).** 현행 유지.

---

## C. 6렌즈 추가 감수 (실물 대조 포함)

### C-1. enum CHECK 제약 — **✅ 14개 컬럼 전부 생성 확인 (실물)**
`native_enum=False, create_constraint=True`로 매핑 → PG 네이티브 ENUM 타입 대신 **VARCHAR + CHECK IN(...)** 로 착지(round1 🟡-2·§9-R(o) 권고 반영). `psql pg_constraint contype='c'`로 앱 CHECK 14개 전수 확인:

```
ck_rail_templates_rail, ck_standards_standardtier, ck_standards_rail,
ck_users_role, ck_cases_exitreason, ck_cases_casestatus, ck_cases_intakeroute,
ck_template_items_itemkind, ck_evidence_evidenceeventtype, ck_evidence_evidenceorigin,
ck_items_rail, ck_items_itemkind, ck_items_itemstatus, ck_approvals_approvaldecision
```
= **정확히 14개.** 무결성을 앱이 아니라 DB CHECK로 강제(backend §9 원칙 부합). 값 추가 시 CHECK 재생성만으로 끝나 확장 예약(`ItemKind.external`·레일 추가)에 유리. **부수 이득:** native ENUM이 아니라 downgrade 시 남는 PG 타입이 없어 마이그레이션 위생도 더 깨끗하다(C-5).

### C-2. 지배적 조회 경로 커버 — **✅ 핵심 경로 전부 인덱스 커버**
- `GET /cases/{id}` 게이트 집계(§5 = Item을 `case_id,status`로 GROUP BY): `ix_items_case_id_status`가 **커버**. status별 count·`submitted==0` 판정(§3-1-1)도 이 복합 인덱스로 인덱스-온리 근접 스캔 가능.
- `GET /cases` 목록(status 필터·정렬): **⚠️ 아래 C-3 참조** — 정렬키(deadline/risk/completion/name)는 Case 컬럼이 아니라 대부분 파생값이라 인덱스로 못 덮는다(설계상 정상, 애플리케이션 정렬).
- 증적 아카이브(case_id, seq 순 §10): `uq_evidence_case_id_seq`가 **커버**(정렬 포함).

### C-3. 🔵 목록 정렬·게이트 N+1 — **모델 사안 아님, 서비스 인계 (round1 🟡-1 계승)**
- `GET /cases` 목록에서 케이스별 완료율/리스크/정렬은 **Gate 파생값**(비저장 §5)이라 케이스마다 items 집계하면 N+1이 된다. 이건 모델의 결함이 아니라 **repository/service 구현 사안** — 다음 라운드 감수 대상.
- **인계 [지금 필요 · 다음 task]:** 목록 게이트는 `Item`을 `GROUP BY case_id, status` **1쿼리 집계**로(§9-R 노트 ③, `ix_items_case_id_status`가 커버). 케이스별 반복 로드·ORM lazy-load(`case.items`) 금지. 현재 `Case.items` 관계가 기본 lazy라 서비스가 무심코 순회하면 함정 — selectinload/집계쿼리로 회피.

### C-4. 타입·제약·nullable 계약 일치 — **✅ 일치 (경미 1건 C-4b)**
- **nullable:** Case(`subject_role_title`·`reason_text`·`profile_id` nullable), Item(`sub`·`deadline`·`standard_ids`·`detail` nullable), Approval(`memo`·`attachments`·`basis_note`·`reviewer_id`·`decision`·`reviewed_at` nullable), Evidence(`document_ref`·`prev_hash` nullable), Standard(`article`·`body`·`source_url` nullable), Profile(`job`·`rank` nullable) — **전부 계약 §3 ●/○ 표기와 일치.**
- **timezone=True:** 모든 `DateTime` 컬럼(created/updated, occurred_at, sealed_at, reviewed_at, submitted_at, standards.updated_at)이 `timezone=True` — backend §9(UTC) 준수. ✅
- **바이트 BIGINT(round1 🔴-2):** 이번 코어 테이블엔 바이트 정수 컬럼이 **없다**(`Approval.attachments`는 JSONB라 size가 JSON 숫자 = 임의정밀도, int32 위험 없음). `AnomalyExportLog.size_bytes`는 SEC 레일 테이블이라 이번 범위 밖 → **해당 없음 확인.**
- **(C-4b) 🔵 `status` 기본값이 Python-side `default=`뿐, `server_default` 없음:** `Case.status`(`default=in_progress`)·`Item.status`(`default=pending`)는 SQLAlchemy Python 기본값이라 **ORM INSERT엔 항상 값이 들어가 문제없다.** 단 raw SQL/bulk 시드로 status를 빼면 NOT NULL 위반. MVP는 ORM 경유가 원칙이라 실害 낮음 → **[Post-MVP/선택]** 안정성 원하면 `server_default` 추가. 심각도 🔵.

### C-5. 마이그레이션 위생 — **✅ 깨끗**
- `down_revision = None`(최초 리비전) 정상. `downgrade()`가 생성 역순으로 전 테이블·인덱스 DROP — **완결.**
- **native_enum=False의 위생 이득:** enum이 인라인 CHECK라 downgrade 시 dangling PG ENUM 타입이 안 남는다(native ENUM이었으면 `sa.Enum().drop()` 수동 추가 필요했을 것). 자동생성이 그대로 완결됨.
- 손편집 흔적 없음(autogenerate 주석 `please adjust!` 잔존은 무해). `env.py`가 4개 도메인 모델을 전부 import(side-effect 등록)해 autogenerate가 9엔티티를 빠짐없이 잡았다 — 실물 테이블 수와 일치 확인. ✅

---

## 의도적 비정규화 인정 (정당 — 유지)
1. **`Evidence.payload` 스냅샷 봉인(JSONB)** — 처리 시점 사실 중복 저장, 재현성·위변조 탐지 목적. 정당.
2. **`standard_ids`·`rail_map` JSONB(참조 비정규화)** — 읽기 전용 시드 참조라 MVP 허용(B-2). 시드 무결성 책임 문서화 조건부 인정.
3. **`Item.detail`·`TemplateItem.detail_schema` JSONB 확장 슬롯(§7)** — 레일별 표시·파생용 예약, 조회 필터 대상 아님. 스키마 유연성 목적 허용.
4. **Gate 비저장 파생(§5)** — 계산이 진실. 파생값 저장 이상 회피. 모범.

## [결정필요] — 도비 판단 대상
- **없음.** 이번 라운드는 계약을 바꿔야 하는 권고가 없다. round1의 삭제정책·seq 동시성·인덱스 원칙이 이미 계약(§9-R)에 반영됐고, 이번 코드가 그 계약을 따랐다. B-1(중복 인덱스)·C-3·A-1(FOR UPDATE)은 전부 **론 구현 재량/다음 task 게이트**이지 계약 변경이 아니다.

---

## 다음 라운드(서비스/repository) 감수 게이트 예약
1. **[필수] seq 채번 `SELECT … FOR UPDATE` 직렬화 + 동일 트랜잭션 append**(A-1) — 이게 없으면 증적 무결성 계약이 미완.
2. **[필수] 목록 게이트 집계 N+1 회피**(C-3) — `GROUP BY case_id, status` 1쿼리.
3. `Case.recompute_status()`(review_waiting 파생)가 항목 전이와 동일 트랜잭션에서 호출되는지(desync 방지, round1 🟡-4).
