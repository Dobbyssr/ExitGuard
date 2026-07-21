# ExitGuard — API 명세 (Phase 0 척추 · 공통 규약 + 코어 엔드포인트)

> **문서 성격** — 공통 응답/에러/페이지네이션/근거배지 규약 + **공통 코어 엔드포인트**의 계약(경로·메서드·요청/응답 스키마)을 고정한다. 레일별 세부 엔드포인트(`/rails/labor` 등)는 **뼈대 경로만 예약**하고 내부는 대표2·3이 채운다.
> **근거 SSOT** — 필드·타입·enum·상태·compare shape는 전부 `docs/spec/data-model.md`를 참조(중복 정의하지 않고 **동일 식별자**를 쓴다). 용어는 `docs/spec/유비쿼터스.md` 정합.
> **경계** — OpenAPI 스타일 마크다운 계약까지만. 실제 라우터·미들웨어·인증구현·폴더구조는 론(백엔드) 몫. 스키마는 예시 필드로 shape를 보이되 완전 타입은 data-model 참조.
> **작성**: 헤르미온느 · **작성일**: 2026-07-15

---

## 1. 공통 규약

### 1-1. 기본
- Base path: `/api/v1`
- 요청/응답 `Content-Type: application/json` (Export만 `application/pdf`).
- 시각은 UTC ISO-8601. 날짜는 `YYYY-MM-DD`.
- 인증: `Authorization: Bearer <token>` (admin/user 2역할). **인증은 CP 밖**(데모는 관리자 로그인 상태 시작) — 엔드포인트는 인증 전제로 명세하되 세로절단 구동에 load-bearing 아님. 권한 표기는 §1-5.

### 1-2. 성공 응답 포맷 (envelope)
```json
{ "data": { ... }, "meta": { ... } }
```
- 단건: `data`=객체. 목록: `data`=배열 + `meta.pagination`.
- 부수 파생(게이트 등)은 해당 리소스 `data` 안에 포함.

### 1-3. 에러 포맷 (freeze)
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "대상자 이름을 입력하세요", "fields": { "subject_name": "required" } } }
```
| HTTP | code | 상황 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | 입력 검증 실패(`fields`에 필드별 사유) |
| 401 | `UNAUTHENTICATED` | 토큰 없음/무효 |
| 403 | `FORBIDDEN` | 권한 부족(예: user가 review 시도) |
| 404 | `NOT_FOUND` | 리소스 없음 |
| 409 | `INVALID_TRANSITION` | 상태머신 위반(예: pending 항목을 approve) |
| 422 | `COMPARE_FAILED` | 대조 엔진 처리 실패 |
| 500 | `INTERNAL` | 서버 오류 |
| 501 | `NOT_IMPLEMENTED` | 미구현 기능(예: 방어 리포트 PDF 렌더 — §2-5. MVP 범위 밖, `format=json`으로 대체) |

### 1-4. 페이지네이션·필터·정렬 (목록 공통)
- 쿼리: `?page=1&size=20&q=<검색>&sort=<키>&filter=<값>`
- 응답 `meta.pagination`: `{ "page":1, "size":20, "total":57, "total_pages":3 }`

### 1-5. 권한 표기
각 엔드포인트에 `[admin]` / `[user]` / `[both]` 표기. 상신=`[user]`(담당자 대리), 검토·승인=`[admin]`, 조회=`[both]`.

### 1-6. 근거 배지 표현 규약 (L1/L2/L3) ★
근거가 붙는 모든 응답 필드는 배열 `badges`로 통일:
```json
"badges": [
  { "tier": "L1", "title": "근로기준법 제27조", "url": "https://law.go.kr/...", "version": "v2026.06" },
  { "tier": "L2", "title": "중노위 판정례", "url": "https://...", "version": "v2026.05" }
]
```
- `tier` ∈ `L1|L2|L3` (data-model `StandardTier`). 프론트는 tier로 배지 색/라벨 렌더. ("GPT 래퍼 아님" 증명 = 모든 대조결과에 배지 필수)

### 1-7. 직역법 경계 (응답 문구 강제) ★
- 대조/알림 응답의 서술 필드는 "위법입니다/부당해고입니다/패소합니다" 금지. "미충족 N건 / 기한 D-day / …로 판정된 사례가 있습니다" 프레이밍만.
- compare 응답은 `boundary_notice` 필수 포함(data-model §6-3 고정 문구). 판단 분기 응답에는 전문가 연결 힌트 필드 `expert_referral: true` 노출 가능.

---

## 2. 코어 엔드포인트

> 스키마는 shape 예시. 완전 필드·타입·enum은 data-model 해당 엔티티(§표기) 참조.

### 2-1. 케이스

#### `POST /cases` — 케이스 접수 (CM-04) `[user]`
data-model `Case`(§3-1). 접수 3경로(`intake_route`) 공통.
요청:
```json
{ "subject_name":"김민준", "subject_job":"개발", "subject_rank":"시니어 책임",
  "subject_role_title":"백엔드 개발자", "exit_reason":"recommended_resignation",
  "reason_text":"...", "exit_date":"2026-07-19", "intake_route":"groupware",
  "profile_id":"dev" }
```
응답 201: `data` = 생성된 `Case`(+ `profile` 적용으로 자동생성된 `items` 요약, `gate` 초기 파생).
- 동작: `profile_id`의 `rail_map` → 각 RailTemplate의 TemplateItem을 `Item`으로 복제(상태 `pending`, 유형규칙에 따라 일부 `not_applicable`).
- 400 `VALIDATION_ERROR`(이름 누락 등).

#### `GET /cases` — 케이스 목록 (CM-03) `[both]`
`?filter=all|in_progress|review_waiting|completed&q=&sort=default|deadline|risk|completion|name&page=&size=`
응답: `data`=[Case 요약(+ gate.overall_completion, gate.risk_count, exit_date/dday)], `meta.pagination`.

#### `GET /cases/{id}` — 케이스 상세 (CM-07) `[both]`
응답 `data`:
```json
{ "case": { ...Case }, "gate": { ...Gate },
  "rails": { "labor":{...}, "trade_secret":{...}, "security":{...} },
  "items": [ { ...Item, "badges":[...] } ] }
```
- `gate` = data-model §5 결정론적 파생. `rails.<rail>` = 레일별 완료율·항목 그룹(레일 세부 내부는 §3 예약 엔드포인트로 확장).

#### `POST /cases/{id}/approve` — 퇴사 승인 확정 (CM-08, T3) `[admin]`
data-model §3-1-1. 게이트 통과 상태에서 케이스를 `completed`("방어 가능 상태로 승인됨")로 전이. 요청 `{}`(선택 `{ "memo": "..." }`).
- **승인 조건(서버 강제)**: `Gate.defensible == true`(risk_count 0) **AND** `submitted` 항목 0건(미검토 상신 없음). data-model §3-1-1 `approvable()`.
- 동작: 조건 만족 시 `Case.status → completed` + **자동 증적 봉인**(`event_type=case_approved`, data-model §3-4-1 — 게이트 스냅샷·승인자·시각 봉인).
- 응답 200: `data` = 갱신 `Case`(+ 봉인된 `evidence` 요약). `meta.toast`="✓ 방어 가능 상태로 승인되었습니다".
- **409 `INVALID_TRANSITION`**: `approvable==false`(미해소 리스크 또는 미검토 상신 존재)인데 승인 시도 → **거부**(게이트 우회 강제승인 없음). 응답에 미충족 사유(risk_count·submitted 수) 포함.
- 403(user 시도). 404(케이스 없음).

### 2-2. 게이트

#### `GET /cases/{id}/gate` — 통합 게이트 집계 (CM-08) `[both]`
응답 `data` = `Gate`(§5): `{ rail_completion:{labor,trade_secret,security}, overall_completion, risk_count, defensible }`.
- `defensible=true` → "방어 가능 상태". 순수 파생(계산식 freeze). **게이트 자체는 mutation 없음** — 승인 확정은 `POST /cases/{id}/approve`(위 §2-1, T3)로 분리(게이트는 조건 판정, approve는 상태 전이·봉인).

### 2-3. 대조 엔진 (compare) ★

#### `POST /compare` — 공용 대조 호출 (CM-05 / LB-04 / TS-05) `[both]`
data-model §6 `CompareInput` → `CompareResult`. 세 레일 공용 단일 엔드포인트.
요청 = `CompareInput`. 응답 200 `data` = `CompareResult`(5행 rows + unmet_count + badges + boundary_notice).
- 인테이크 대조(CM-05)는 접수 직후 `POST /cases/{id}/intake-compare`로도 노출(내부적으로 `compare` 호출, `case_facts` 자동 채움) — 편의 래퍼.
- **독립 `/compare`는 케이스 비연계 → `unmet_count=0`(data-model §6-1)**: `CompareInput`에 `case_id`가 없어 이 엔드포인트 단독 호출은 실제 케이스 미충족 건수를 낼 수 없다. `unmet_count=0` 반환 + `status` 행은 "케이스와 연계하면 미충족 건수·기한이 함께 제공됩니다" 안내로 채운다. **케이스 연계 실측 수치(`unmet_count`·D-day)는 `intake-compare`가 케이스 Item 롤업으로 채운다.** (창작 아님 — shape에 case 연계가 없다는 계약의 귀결.)
- **처리 파이프라인(T1, data-model §6-4)**: ① LLM 단계 = 비정형 `reason_text`→구조화 신호(`SignalExtraction`, 폐집합 라벨·`evidence_span`)만 추출(판단·문구 생성 금지). ② 결정론 단계(코드) = 신호 화이트리스트 검증 → 요구요소 매핑 → 코퍼스/기준 필터 → **5행 템플릿 조립**·`unmet_count`·`badges`·`boundary_notice`. `risk` 행은 결정론 템플릿에 값 치환("…판정된 사례가 있습니다"), LLM 자유서술 아님.
- **직역법 강제**: LLM 출력은 공개 기준 **인용·링크만**. 생성형 판단·개선방안·단정 금지(data-model §6-3·§6-4). 위반 신호는 결정론이 폐기.
- **Fallback**: LLM 실패·환각·타임아웃·유효신호 0건 → **결정론만으로 성립**(5행 shape·`boundary_notice` 항상 유지, `risk` 생략 가능). compare 응답은 어떤 경우에도 shape·경계문구를 깨지 않는다.
- **결과 봉인**: 확정된 `CompareResult`는 증적으로 봉인됨(`event_type=compare_recorded`, data-model §3-4-1) → 방어 리포트(§2-5)가 재계산 없이 인용.
- 422 `COMPARE_FAILED`(파이프라인 처리 실패 — 단, LLM 실패는 fallback으로 흡수하므로 422 아님).

#### `POST /cases/{id}/intake-compare` — 인테이크 대조 래퍼 (CM-05) `[both]`
요청: `{}`(케이스에서 facts 추출) 또는 override. 응답 = `CompareResult`(신호 스캔 결과, 다중 토픽 시 `data`=[CompareResult]).

### 2-4. 항목 · 상신-검토

#### `GET /items/{id}` — 검사항목 상세 드로어 (CM-09) `[both]`
응답 `data` = `Item` + `badges` + `approvals`(이력) + `basis`(확인요건·근거). 문구 "미충족 리스크"(§1-7).

#### `POST /items/{id}/submit` — 상신 (CM-10) `[user]`
data-model `Approval`(§3-3) 생성. 요청:
```json
{ "memo":"급여·퇴직금·연차 4일 수당 반영 정산", "attachments":[{"name":"정산내역서.pdf","size":"243 KB"}], "signed":true }
```
응답: `data`=생성된 `Approval`, Item `pending|rejected → submitted`.
- 409 `INVALID_TRANSITION`(이미 approved 등).

#### `POST /items/{id}/review` — 검토(확인/반려) (CM-10) `[admin]`
요청: `{ "decision":"confirmed" }` 또는 `{ "decision":"rejected", "memo":"..." }`.
응답: `data`=갱신 `Approval`, Item `submitted → approved|rejected`. 반려 시 재상신은 `POST /items/{id}/submit` 재호출.
- 403(user 시도), 409 `INVALID_TRANSITION`(submitted 아님).

### 2-5. 증적

**자동 봉인이 기본(T2, data-model §3-4-1)**: 증적은 처리 이벤트 발생 시 **서버가 자동 append**한다(별도 호출 불요). 아래 `POST /evidence`는 **수동 보충 봉인**(`origin=manual`)용.

**자동 봉인 트리거(서버 내부 · `origin=auto` · data-model §3-4-1)**:
| `event_type` | 트리거 엔드포인트/이벤트 | payload 스냅샷 |
|---|---|---|
| `item_submitted` | `POST /items/{id}/submit` | 항목·상신 memo·첨부메타·전자서명·상신자 |
| `item_confirmed` / `item_rejected` | `POST /items/{id}/review` | 항목·검토결과·검토자·basis_note |
| `compare_recorded` | `POST /compare` 결과 확정 | `CompareResult`(5행·badges·boundary_notice) |
| `recovery_confirmed` | 보안 회수 확인(review) | 회수 항목·확인 사실(실행 아님) |
| `case_approved` | `POST /cases/{id}/approve` | 게이트 스냅샷·승인자·시각 |

- 각 자동 봉인: `seq`=직전+1, `prev_hash`=직전 `integrity_hash`, `integrity_hash`=SHA-256(`canonical_json(payload)`+`prev_hash`), 해당 mutation과 **동일 트랜잭션**(누락 없는 append). 계약 상세 data-model §3-4-1.

#### `POST /cases/{id}/evidence` — 수동 보충 봉인 (CM-12) `[admin]`
자동 봉인으로 안 잡히는 처리를 수동 봉인(`origin=manual`). data-model `Evidence`(§3-4). 요청: `{ "action":"...", "actor":"...", "event_type":"...", "document_ref":"...", "payload":{...} }`.
응답 201: `data`=`Evidence`(+ `integrity_hash`, `prev_hash`, `sealed_at`). 서버가 SHA-256 계산·체인 연결(자동 봉인과 동일 체인에 append).

#### `GET /cases/{id}/evidence` — 증적 아카이브/봉인 뷰 (CM-12/CM-14) `[both]`
응답: `data`=[Evidence 이력(seq 순, `event_type`·`origin` 포함)], `meta.seal_status`=`sealed|accruing`, 항목수·봉인일시·`head_hash`(체인 헤드).

#### `GET /cases/{id}/evidence/export` — 방어 리포트 Export (CM-13, B1) `[both]`
봉인 증적·게이트·compare 스냅샷 → **`DefenseReport`(data-model §10)** 조립.
- `?format=json`(기본) → 응답 200 `data` = `DefenseReport`(KPI·3레일 배지·`compare_findings`(봉인 스냅샷 인용)·`evidence_chain`(체인 요약·`head_hash`)·**`boundary_notice` 필수**).
- `?format=pdf` → **현재 501 `NOT_IMPLEMENTED`**(§1-3). PDF 정식 렌더는 **Post-MVP**(도비 브리프 — 억지 구현 금지). FE는 `format=json` 응답을 그대로 렌더할 수 있어 미구현을 501로 명시적으로 알린다. PDF 렌더 착수 시 이 경로가 `200 application/pdf`(동일 `DefenseReport` 뷰)로 전환된다.
- **직역법 강제(B1)**: 응답에 `boundary_notice`(§6-3 고정문구) **필수 포함**. "방어 가능 상태"가 적법·승소 보증으로 읽히지 않게 경계 고지 승계(data-model §10·§3-1-1). 누락 시 리포트 무효.
- `compare_findings`는 실시간 재계산이 아니라 **봉인된 `compare_recorded` 스냅샷 인용**(재현성·환각 배제).

### 2-6. 근거 기준 DB (CM-16 — 코어 조회)

#### `GET /standards` — 3층 기준 스택 조회 `[both]`
`?rail=&tier=L1|L2|L3&q=&page=&size=`
응답: `data`=[Standard(§3-5): tier,title,article,source_url,version,updated_at], `meta.pagination`.
- 근거 배지의 원천. 버전카드·갱신이력은 이 데이터 파생.

### 2-7. 토스트 (CM-32)
- 서버 mutation 응답의 `meta.toast`(선택)로 피드백 메시지 전달(예: `"✓ 김민준 케이스가 등록되었습니다"`). 별도 엔드포인트 없음.

---

## 3. 레일별 엔드포인트 — 뼈대 경로 예약 (대표2·3이 내부를 채운다) ★

Phase 0은 **경로·소속만 예약**한다. 요청/응답 스키마 내부(레일 상세 필드·대조규칙)는 **Phase 1(레일별)** 에서 대표2·3이 채운다. 공용 부분(항목 상태·상신검토·compare·게이트·증적·배지)은 위 §2 코어를 그대로 재사용하므로 레일 전용 엔드포인트는 **레일 고유 데이터에만** 신설한다.

| 예약 경로 | 레일 | 용도(뼈대) | 채우는 사람 |
|---|---|---|---|
| `GET /cases/{id}/rails/labor` | 노무 | 노무 항목 그룹 + 기한 타임라인·D-day(LB-01·02) | 대표2 |
| `GET /cases/{id}/rails/trade_secret` | 영업비밀 | 접근 자산 인벤토리 + 3요소 대조 테이블(TS-01·02) | 대표3 |
| `GET /cases/{id}/rails/security` | 보안 | 회수 체크리스트 + 이상반출 이력(SEC-01·02) | 대표3 |
| `POST /cases/{id}/rails/{rail}/...` | 각 | 레일 고유 액션(재서약·자산회수·계정회수 등) | 대표2·3 |

- 위 레일 조회의 **공통 뼈대 응답**: `{ rail, completion, items:[Item...], compare:[CompareResult...], badges:[...] }`. 레일 고유 필드는 `Item.detail`(data-model §3-2 예약 슬롯)로 확장.
- 상신/검토/봉인/게이트/근거조회는 레일 불문 §2 코어 엔드포인트 사용(중복 신설 금지).

---

## 4. CP-23 ↔ 엔드포인트 커버 (요약 — 상세표는 유비쿼터스.md §CP커버)

| CP 기능 | 엔드포인트 |
|---|---|
| CM-04 접수 | `POST /cases` |
| CM-05 AI 대조 | `POST /cases/{id}/intake-compare` → `POST /compare` |
| CM-06 수집 로딩 | (프론트 연출 + 접수 응답, 시뮬) |
| CM-07 레일상세 | `GET /cases/{id}` |
| CM-08 게이트 | `GET /cases/{id}/gate` · `POST /cases/{id}/approve`(승인, T3) |
| CM-09 항목 드로어 | `GET /items/{id}` |
| CM-10 상신-검토 | `POST /items/{id}/submit` · `POST /items/{id}/review` |
| CM-12 증적 봉인 | `POST /cases/{id}/evidence` · `GET /cases/{id}/evidence` |
| CM-13 리포트 Export | `GET /cases/{id}/evidence/export`(→ `DefenseReport` json/pdf, B1) |
| CM-15 근거 배지 | 모든 응답 `badges`(§1-6) |
| CM-16 기준 DB | `GET /standards` |
| CM-22 레일 템플릿 | (접수 시 RailTemplate→Item 복제, `POST /cases`) |
| CM-32 토스트 | `meta.toast`(§2-7) |
| LB-01·02·03·04·08 | `GET /cases/{id}/rails/labor`(뼈대) + `POST /compare`(LB-04) + `badges` |
| TS-01·02·05 | `GET /cases/{id}/rails/trade_secret`(뼈대) + `POST /compare`(TS-05) |
| SEC-01·02 | `GET /cases/{id}/rails/security`(뼈대) |

---

## 5. Phase 1 코어 보강 기록 (2026-07-20 · T1·T2·T3·B1 · 대표님 승인)

gap 검토 승인분. **기존 엔드포인트·envelope·에러·배지 규약 재정의 0건 — 확장만.**
- **T1** compare 파이프라인 계약(§2-3): LLM(신호추출)/결정론(조립·문구·검증) 분리 + fallback + 결과 봉인. data-model §6-4.
- **T2** 증적 자동봉인(§2-5): 이벤트 6종 자동 append + SHA-256 체인. 수동 `POST /evidence`는 보충. data-model §3-4-1.
- **T3** 승인 엔드포인트 신설 `POST /cases/{id}/approve`(§2-1): `approvable`(defensible && submitted==0) 강제, 우회 승인 409. data-model §3-1-1.
- **B1** `evidence/export` → `DefenseReport`(§2-5, json/pdf): boundary 고지 필수, compare 봉인 스냅샷 인용. data-model §10.
- **[반영] C3**: 레일 상세 배너를 `rail_notice`로 리네임(보안 api-spec 4곳·보안 기능명세서 AC-3) → `CompareResult.boundary_notice`(§6-3)·`DefenseReport.boundary_notice`(§10)와 충돌 해소. `rail_notice`=레일 상세 선택적 배너 정식명. 노무·TS 레일 상세엔 배너 필드 없어 무영향. compare/report의 boundary_notice는 이름 유지.

### 5-1. 구현 정합 (2026-07-21 · 구현정합 5건 · 도비 위임)

노무 세로절단 구현 중 드러난 계약↔구현 불일치 정합. **엔드포인트·envelope·배지 규약 재정의 0건 — 명시·등재만.** api-spec 파급분:
- **독립 `/compare` `unmet_count=0` 명문화(§2-3)**: `CompareInput` 케이스 비연계 → 독립 호출은 `unmet_count=0`, 실측 롤업은 `intake-compare`. (data-model §6-1 동시 갱신.)
- **`501 NOT_IMPLEMENTED` 에러코드 등재(§1-3)** + `evidence/export?format=pdf`가 현재 501임을 §2-5에 명시(PDF 정식 렌더=Post-MVP). 신설 코드는 에러표에만 추가, 기존 코드 불변.
- (나머지 정합 3건 — `decided_on` ●→○·`na` 유형규칙·`basis_note` 이중용도 — 은 data-model §9-S·노무 data-model.)

---

*본 문서는 Phase 0 freeze 대상이다. 코어 규약/엔드포인트 변경 시 data-model.md·유비쿼터스.md와 동시 갱신. 레일 세부는 대표2·3 Phase 1. (Phase 1 코어 보강 T1·T2·T3·B1 = §5, 2026-07-20.)*
