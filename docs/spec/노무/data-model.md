# ExitGuard — 노무(LB) 레일 데이터 모델 (Phase 1 · 레일 보강)

> **문서 성격** — 공유 코어(`../data-model.md`)를 **import만** 하고, 노무 레일 고유 데이터(유형별 법정 기한요소·6개 검사항목 충족판정·중노위 판정례 대조 구조)만 보강한다.
> **뼈대 재정의 금지** — `Case`·`Item`·`Approval`·`Evidence`·`Standard`·`Gate`·enum(`Rail`,`ExitReason`,`ItemStatus`,`ItemKind`,`StandardTier`)·`CompareInput`/`CompareResult` shape는 코어에서 그대로 가져온다. 여기서 다시 정의하지 않는다.
> **근거 SSOT** — 데모(`pitch/데모/ExitGuard-나모업로드-단일본.html`)가 1차 진실. 실측 데이터 소스: **L1 국가법령정보 OpenAPI**(근기법 현행 MST=265959, 시행2025-10-23, §26·§27·§36 원문 실추출) + **L2 중앙노동위 주요 판정사례 CSV**(399행, 상업이용 허용). 창작 금지.
> **레일 코드** — `labor` (접두어 LB · 항목코드 `L-`).
> **작성**: 헤르미온느 · **작성일**: 2026-07-20

---

## 0. ⚠️ 주인공·시나리오 정합 결정 (데모 서사 ↔ 코어 freeze)

브리프의 LB 데모 서사("김민수 부당해고 케이스 · 구두(문자) 해고 통보 → 서면통지 §27 누락")와 코어 freeze(`../data-model.md §9-b`: 주인공 = **김민준 · 권고사직 · D-3**, `§4`: L-09 해고예고 = `not_applicable`)가 표면상 충돌한다. 본 문서는 **코어를 재정의하지 않는 방향**으로 다음과 같이 착지한다 — 상세는 §6 [결정필요].

- **주인공은 김민준 · `exit_reason=recommended_resignation`(권고사직) 유지.** ("김민수"는 stale 표기 — 코어 §9-b.)
- **LB-04(판정례 대조 = 해자)는 `reason_text`의 "구두/문자 통보" 신호로 발화한다.** 권고사직으로 접수됐으나 회사사유 텍스트에 구두·약식 통보 정황이 있으면, compare 엔진이 이를 신호로 추출 → **"해고로 다퉈질 경우 근기법 §27(서면통지) 요소와 대조"** → 순번 51·388 사례 프레이밍. 이는 실제 최빈 노무분쟁(권고사직 형식 ↔ 실질 해고 주장)과 정확히 일치하며, **"이건 해고다/위법이다"라는 판단을 하지 않고** 신호·대조·사례 프레이밍만 한다(직역법 §4 안전).
- 이 설계로 **김민준=권고사직(코어 정합) + LB-04 서면통지 킬러 데모(브리프 요구)** 를 동시에 만족한다.

---

## 1. 레일 확장 지점 (코어 §7 예약 슬롯 중 LB가 채우는 것)

| 코어 예약 지점 | LB가 채우는 내용 | 위치 |
|---|---|---|
| `Item.detail`(rail=labor) — "노무 기한요소·정산 필드" | 항목별 법정 기한 규칙·근거 조문·D-day (LB-01·02) | §3 |
| 별도 레일 테이블(코어 §7 "레일 고유 데이터에만 신설") | **`LaborPrecedent`** — 중노위 판정례 대조 코퍼스(CSV 기반) | §4 (신설) |
| `compare.py` LB 규칙(shape 고정) | 구두통보 등 신호 → §27 서면통지 요구 요소 매핑 (LB-04) | §5 |
| `Standard`(rail=labor) L1/L2/L3 | 근기법 §26·§27·§36 · 중노위 판정례 대표배지 · 고용부 가이드 | §6 |

> **왜 `LaborPrecedent` 별도 테이블인가**: 코어 `Standard`는 "큐레이션된 기준 배지 1건"(예: 근로기준법 제27조)이다. 중노위 판정례 **399행 코퍼스**(사건유형·요지·작성일자별 검색·매칭 대상)는 배지가 아니라 **대조 대상 데이터**다(TS의 `TradeSecretAsset`이 검사항목이 아니라 대조 대상이었던 것과 동일 개념). 개념이 다르므로 코어 §7이 허용한 별도 레일 테이블로 신설한다. 코어 FK 규약·증적 규약은 준수하되, 판정례는 케이스 종속이 아닌 **참조 코퍼스**라 `case_id`를 갖지 않는다(§4 주석).

---

## 2. 노무 검사항목(`Item`, rail=labor) — 데모 6항목 정합

노무 레일의 검사항목은 **코어 `Item`(§3-2) 그대로** 생성된다. 신규 엔티티 아님. 데모 6항목 = 케이스 접수 시 `RailTemplate`(기본 노무 템플릿)의 `TemplateItem`에서 복제.

### 2-1. 데모 6항목 정본 (항목코드 `L-`)

| code | name | kind | blocking | detail.deadline_rule | 근거(§6) |
|---|---|---|---|---|---|
| `L-01` | 사직 합의서 서면 확인 | `internal` | false | `none` | L3 |
| `L-02` | 연차 미사용 수당 정산 | `statutory` | true | `settlement_14d` | L1 §36 |
| `L-04` | 금품청산 (14일) | `statutory` | true | `settlement_14d` | L1 §36 |
| `L-06` | 이직확인서 발급 | `statutory` | true | `separation_cert` | L1 §36 |
| `L-08` | 4대보험 상실신고 | `statutory` | true | `insurance_loss` | L1 §36 |
| `L-09` | 해고예고 (30일) | `statutory` | true | `dismissal_notice_30d` | L1 §26 |

> **kind/blocking 근거**: `L-01`(사직 합의서)은 권고사직 문서 확인 = 내규(`internal`, blocking=false). 나머지 5개는 법정(`statutory`, blocking=true, 기본값 코어 §2-4). 게이트 risk는 코어 §5식 그대로 — 레일에서 재계산·재정의 금지.
> **`L-03`·`L-05`·`L-07` 결번**: 데모 항목 코드 정합(데모는 6항목만 노출). 결번은 회사 커스텀/Post-MVP 항목 예약(빈 종이 빌더 금지 원칙 — 기본 라이브러리 위 확장).

### 2-2. `Item.detail` — LB 검사항목 상세 슬롯 (rail=labor · 코어 §7 예약 채움)

```
Item.detail (rail=labor) {
  deadline_rule: enum LaborDeadlineRule           # 이 항목의 법정 기한 규칙 종류(LB-01 결정론적 배치)
  deadline_basis: str | null                      # 기한 계산 근거 조문 — 예: "근로기준법 제36조"
  dday: int | null                                # LB-02 잔여일(파생: deadline - reference_date). 저장 아님(계산)
  timeline_group: enum { settlement | notice | filing } | null   # 타임라인 뷰 그룹핑
}
```

`Item.deadline`(코어 date 필드)에 실제 기한일이 들어가고, `Item.detail`은 그 **규칙·근거·파생 D-day**를 담는다.

#### `LaborDeadlineRule` — 법정 기한 규칙 (enum)

| 코드 | 규칙 | 계산식(결정론적) | 근거 실측 | timeline_group |
|---|---|---|---|---|
| `settlement_14d` | 금품청산 14일 | `deadline = exit_date + 14d` | ✅ **L1 §36 실추출**(지급사유 발생부터 14일 이내) | `settlement` |
| `dismissal_notice_30d` | 해고예고 30일 | `deadline = 해고예정일 − 30d`(해고 시) | ✅ **L1 §26 실추출**(적어도 30일 전 예고, 미이행 시 30일분 통상임금) | `notice` |
| `written_notice` | 서면통지 | 기한(일수) 아님 — **사전 서면 이행 이벤트**(해고 시). LB-04 대조 요소 | ✅ **L1 §27 실추출**(해고사유·시기 서면통지) | `notice` |
| `separation_cert` | 이직확인서 발급 | `[시드확인필요]` — 조문 기한 미실측 | ⚠️ 미실측(창작 금지) | `filing` |
| `insurance_loss` | 4대보험 상실신고 | `[시드확인필요]` — 조문 기한 미실측 | ⚠️ 미실측(창작 금지) | `filing` |
| `none` | 기한 없음 | — (문서 확인 항목) | — | — |

> ⚠️ **근거 규율(창작 금지)**: `settlement_14d`(§36)·`dismissal_notice_30d`(§26)·`written_notice`(§27)만 국가법령정보 OpenAPI로 **원문 실추출 확인**됐다. 연차 미사용 수당(`L-02`)은 §36 금품청산 대상(임금·수당·퇴직금 일체)이므로 `settlement_14d` 적용 근거 확실. `separation_cert`·`insurance_loss`의 구체 기한(일수)은 **실측 안 됨 → `[시드확인필요]`**로 두고 임의 일수 창작 금지. LB-01 타임라인에서 이 두 항목은 "발급/신고 필요"로만 배치하고 D-day는 조문 확정 후 채운다.

---

## 3. LB-03 — 6개 검사항목 충족판정 파생 (명시적 count · 자기검증) ★

LB-03은 6개 항목의 코어 `Item.status`를 **3-상태 대조 표시**(충족/미충족/해당없음)로 롤업한다. **집합(set) 아님, 명시적 개수(count)** — 영업비밀 `protection_status` set 오독 버그 전례 회피(코어 델타·TS §2-3).

### 3-1. 항목별 3-상태 매핑 (결정론적)

```
def three_state(item.status):
    if status == approved:                          return "충족"       # met
    if status == not_applicable:                    return "해당없음"    # na
    if status in {pending, submitted, rejected}:    return "미충족"      # unmet (하위상태 표기)
```

- `미충족` 하위상태 표기(직역법 안전 어휘): `pending`→"대기", `submitted`→"상신검토필요", `rejected`→"반려". (데모 표기 정합)
- **경계**: "미충족"은 *공개 기준 대비 항목이 아직 충족되지 않은 상태*를 뜻하며, 위법·부당의 판단이 아니다(§6 boundary).

### 3-2. 요약 카운트 파생 (명시적 count — freeze)

```
met_count   = count(items[labor] where status == approved)
na_count    = count(items[labor] where status == not_applicable)
unmet_count = count(items[labor] where status in {pending, submitted, rejected})
total_count = count(items[labor])                       # = met + na + unmet (불변식)
```

- **불변식 자기검증**: `met_count + na_count + unmet_count == total_count`. (set 아님 — 상태는 상호배타 5종이므로 개수 합이 항상 총계와 일치)
- `unmet_count`는 LB-04 compare `status` 행 "미충족 N건"과 **동일 값**을 쓴다(정합).
- 레일 완료율은 **코어 `Gate.rail_completion["labor"]`(§5식) 그대로** 파생 — LB에서 재계산 금지.

### 3-3. 데모 6행 전수 대조 (캘리브레이션 knob — 시드가 이 표를 재현해야 함) ★

주인공 **김민준 · 권고사직**:

| code | name | kind | blocking | status | 3-상태(§3-1) | blocking risk? |
|---|---|---|---|---|---|---|
| `L-01` | 사직 합의서 서면 확인 | internal | false | `approved` | 충족 | no |
| `L-02` | 연차 미사용 수당 정산 | statutory | true | `approved` | 충족 | no |
| `L-04` | 금품청산 (14일) | statutory | true | `submitted` | 미충족(상신검토필요) | **yes** |
| `L-06` | 이직확인서 발급 | statutory | true | `pending` | 미충족(대기) | **yes** |
| `L-08` | 4대보험 상실신고 | statutory | true | `pending` | 미충족(대기) | **yes** |
| `L-09` | 해고예고 (30일) | statutory | true | `not_applicable` | 해당없음 | no |

**자기검증(파생식 §3-2 적용)**:
```
met_count   = 2   # L-01, L-02
na_count    = 1   # L-09 (권고사직 → 해고예고 대상 아님)
unmet_count = 3   # L-04, L-06, L-08
total_count = 6   # 2+1+3 == 6 ✓ (불변식 통과)
```
**코어 게이트 파생(§5식 그대로)**:
```
applicable(labor) = count(status != na) = 5           # L-09 제외
approved(labor)   = count(status == approved) = 2
rail_completion[labor] = round(100 * 2 / 5) = 40%     # 노무 레일 완료율
risk_count(labor 기여) = count(blocking & status ∉ {approved,na}) = 3   # L-04, L-06, L-08
```

> **시드 정합 규약**: 코어 §4가 freeze한 상태는 `L-01=approved · L-04=submitted · L-06=pending · L-09=not_applicable` 4건. 본 표의 **`L-02=approved`·`L-08=pending`은 시드 튜닝 knob**(코어 미지정 → 데모 수치 재현용으로 설정). 이 조합이 `unmet_count=3`·`완료율 40%`를 결정론적으로 산출한다. 자산명처럼 load-bearing 아닌 값은 개발 시드에서 조정 가능하되, 위 4건 freeze 상태와 파생 카운트(2/1/3)는 데모 정본.

---

## 4. `LaborPrecedent` — 중노위 판정례 대조 코퍼스 (신설 · 레일 전용) ★

중노위 주요 판정사례 CSV(399행) 1행 = 1레코드. **케이스 종속 아님 — 참조 코퍼스**(∴ `case_id` 없음). LB-04(판정례 대조)의 매칭 대상.

| 필드 | 타입 | 필수 | 설명 · CSV 매핑 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `seq` | int | ● | CSV `순번`(예: 51, 388) — 데모 인용 참조키 |
| `category` | enum LaborCaseType | ● | CSV `자료구분`(사건유형, §4-1) |
| `title` | str | ● | CSV `제목`(한 줄 요지) |
| `committee` | str | ● | CSV `위원회명`(예: "중앙") |
| `decided_on` | date | ● | CSV `작성일자` |
| `views` | int | ○ | CSV `조회수` |
| `case_no` | str | ○ | 사건번호 — 제목에서 추출(`중앙YYYY부해NNN` 형식). **약 27%(107/399)만 존재, 나머지 null**(§4-2 한계) |
| `matched_elements` | list[enum LaborRequiredElement] | ● | 이 판정례가 커버하는 판정 요구 요소(§5-1). 큐레이션/키워드 매핑 산출 |
| `is_seed` | bool | ● | 데모 직결 실측 사례 표시(순번 51·388 = true) |
| `ingested_at` | datetime | ● | 코퍼스 적재 시각 |

> ★ `LaborPrecedent`는 **상신-검토(Approval) 대상도 게이트 집계 대상도 아니다.** LB-04 compare 엔진이 신호(§5)에 맞는 판정례를 조회해 `risk` 행 사례 프레이밍에 인용할 뿐이다. 근거 배지(`badges`)의 대표 L2 항목은 코어 `Standard`(§6)로 별도 관리한다(코퍼스 ≠ 배지).
> **론(ron-lb-datasource) 적재 정합**: 본 스키마는 CSV 실측 필드에 1:1 대응한다. 실제 적재는 론이 구현하되 필드·타입은 본 계약을 따른다.

### 4-1. `LaborCaseType` — 사건유형 (enum, CSV 자료구분 18종 실측)

CSV `자료구분` 전수(개수). 코드는 식별자용 로마자, 라벨은 한글:

| 코드 | 한글(CSV) | 실측 건수 | LB-04 대조대상? |
|---|---|---|---|
| `disciplinary_dismissal` | 징계해고 | 87 | ✅ 해고계열 |
| `unfair_labor_practice` | 부당노동행위 | 74 | ✗ 노조(퇴사 개인 케이스 무관) |
| `ordinary_dismissal` | 통상해고 | 43 | ✅ 해고계열 |
| `term_expiry` | 기간만료 | 43 | △ 계약만료(갱신기대권) |
| `fair_representation` | 공정대표 | 24 | ✗ 노조 |
| `other_discipline` | 기타징계 | 22 | △ 징계계열 |
| `remedy_interest` | 기타구제이익 | 12 | ✗ |
| `managerial_dismissal` | 경영상해고 | 12 | ✅ 해고계열 |
| `resignation` | 사직 | 11 | △ (해고 다툼 포함 사례 有) |
| `party_standing` | 당사자적격 | 11 | ✗ |
| `bargaining_rep` | 교섭대표결정 | 11 | ✗ 노조 |
| `bargaining_unit` | 교섭단위분리 | 11 | ✗ 노조 |
| `transfer` | 전보 | 10 | ✗ |
| `bargaining_notice` | 교섭요구공고 | 10 | ✗ 노조 |
| `discrimination` | 차별시정 | 9 | ✗ |
| `ex_officio_dismissal` | 직권면직 | 6 | ✅ 해고계열 |
| `standby_order` | 대기발령 | 2 | ✗ |
| `suspension` | 정직 | 1 | △ 징계계열 |

- **해고계열 = 148건**(징계해고87+통상해고43+경영상해고12+직권면직6). LB-04는 **해고계열 + 서면통지 커버 사례**만 대조 대상으로 필터(§5-2). 노조·교섭 계열은 퇴사 개인 케이스와 무관 → 대조 제외.

### 4-2. 데이터 소스 구조적 한계 (설계에 강제 반영) ⚠️

| 한계 | 실측 | LB-04 설계 반영 |
|---|---|---|
| **사건번호 결여** | 약 73%(292/399)에 사건번호 없음. 27%(107)만 제목 내 `[중앙YYYY부해NNN]` | `case_no` nullable. risk 행은 **사건번호 없이도** "…판정된 사례가 있습니다" 프레이밍으로 안전. 있으면 표기, 없으면 생략(창작 금지) |
| **요지 = 한 줄** | 제목 텍스트만, 요구요소 세분 매핑 얕음 | `matched_elements`는 **키워드/큐레이션 매핑**으로 산출(서면통지·해고예고 등 명시적 키워드 위주). 과대 매핑 금지 |
| **인용조문 구조화 없음** | CSV에 조문 필드 없음 | L1 조문 연결은 `Standard`(§6)에서 별도 관리. 판정례↔조문 매핑은 `matched_elements`로 간접 |
| **§36 금품청산 판정례 0건** | 임금체불은 중노위 부당해고 대상 아님(구조적 공백) | **LB-04는 §36 판정례 risk 행을 만들지 않는다.** §36(금품청산 지연)은 **L1 조문 기준 + D-day 관제(LB-01/02)로만** 다룸. L2 대조는 §27 서면통지 등 실제 커버 항목 한정 |

### 4-3. 데모 직결 실측 사례 (창작 금지 · CSV 실물)

| seq | category | title(요지) | case_no | matched_elements | 용도 |
|---|---|---|---|---|---|
| **51** | `disciplinary_dismissal`(징계해고) | "징계사유 중 일부만 인정되어 해고는 양정이 과하고, 해고하면서 **휴대폰 문자로 통보**한 것은 **서면통지 의무를 위반**하여 부당하다고 판정한 사례(중노위, '15.4.27.판정)" | (사건번호 없음 · 내부표기 "'15.4.27.판정") | `[written_notice]` | LB-04 **구두/문자 통보 시나리오 최적**(데모 핵심 인용) |
| **388** | `ordinary_dismissal`(통상해고) | "근로계약기간이 만료되지 않았음에도…해고에 해당하고 **근로기준법 제27조**에 따라 해고의 사유와 시기를 명시한 **서면을 교부하지 않아 부당해고**라고 판정한 사례" | (제목 내 사건번호 없음) | `[written_notice]` | LB-04 **§27 직접 인용 보강 사례** |

> 두 사례 모두 `is_seed=true`. 순번 51은 사건번호가 없고 내부표기("'15.4.27.판정")만 있으므로 `case_no`에 그 내부표기를 넣지 않고 **null 유지**(정식 사건번호 아님 — 창작 금지). risk 행은 "중앙노동위 판정례(휴대폰 문자 통보→서면통지 위반)" 식 서술로 인용.

---

## 5. compare 규칙 — 판정례 대조 (LB-04) ★

**shape는 코어 §6 `CompareInput`/`CompareResult` 그대로. 여기서는 LB 레일의 *규칙 내용*만 채운다.**

### 5-1. `LaborRequiredElement` — 판정 요구 요소 (enum)

판정례가 요구하는 절차 요소. `LaborPrecedent.matched_elements`·compare 매핑의 공통 어휘.

| 코드 | 요소 | 근거 | LB-04 MVP 대조? |
|---|---|---|---|
| `written_notice` | 서면통지(해고사유·시기) | L1 §27 · L2 판정례(순번 51·388) | ✅ **MVP 핵심** |
| `dismissal_notice` | 해고예고 30일 | L1 §26 | △ 예약(해고 케이스 확장 시) |
| `just_cause` | 정당한 이유 | L2(범용) | ✗ MVP 제외(과대 판단 위험 — 범위 밖) |

> MVP LB-04는 **`written_notice` 단일 요소**만 실제 대조한다(데모 세로절단). `dismissal_notice`는 exit_reason=`dismissal` 케이스 확장 예약. `just_cause`는 "정당성 판단"에 근접 → 직역법상 MVP 제외.

### 5-2. 신호 → 요구 요소 매핑 규칙 (구두통보 패턴)

`case_facts.reason_text`에서 **서면통지 결여 신호**를 스캔한다(신호 추출 = 코어 §6 `procedure` 행의 역할).

| 신호(패턴, reason_text) | → 매핑 요구 요소 | → 매칭 코퍼스 필터 |
|---|---|---|
| "구두" · "문자" · "전화" · "카톡" · "말로" 등 **비서면 통보** 표현 | `written_notice` | `LaborPrecedent where 'written_notice' ∈ matched_elements AND category ∈ 해고계열` |
| (권고사직 + 구두통보 복합) | `written_notice` | 상동 — "해고로 다퉈질 경우" 조건 프레이밍(§0 결정) |

- **판단 금지**: 엔진은 "이건 해고다/위법이다"라고 결론짓지 않는다. 신호 존재 → **해당 요소가 다퉈질 경우의 대조 기준·공개 사례**만 제시.
- **§36 금품청산 지연**: 판정례 0건(§4-2) → **compare `risk` 행 생성 안 함.** 대신 `status` 행에서 D-day(LB-02)로만 관제.

### 5-3. 출력 5행(코어 §6-2 고정 kind 순서) — LB-04 규칙이 채우는 텍스트

주인공 김민준(권고사직 + reason_text에 구두/문자 통보 신호) 기준:

| kind | LB-04가 채우는 내용 |
|---|---|
| `procedure` | 신호 요약 — "회사사유 텍스트에서 **구두·문자 통보 정황** 신호가 확인됩니다." |
| `standard` | L1 인용 — "**근로기준법 제27조** — 해고 시 해고사유와 시기를 **서면으로 통지**해야 합니다." |
| `risk` | **사례 프레이밍(단정 금지)** — "구두·약식으로 통보하고 서면통지가 누락된 경우, 공개 판정례에서 **부당해고로 판정된 사례가 있습니다**. (중앙노동위 판정례: 휴대폰 문자로 통보→서면통지 의무 위반)" |
| `status` | 대조 결과 — "노무 검사 항목 6건 중 **미충족 3건** · 금품청산(§36) 지급기한 **D-[n]**" (§3 unmet_count=3, LB-02 D-day) |
| `source` | 출처 링크 — "근로기준법 제27조(국가법령정보) · 중앙노동위원회 주요 판정례" |

- `unmet_count` = §3-2 `unmet_count`(=3).
- `badges` = §6 `Standard` L1/L2/L3 레코드에서 생성.
- `boundary_notice` = **코어 §6-3 고정 문구 그대로(재작성 금지)**:
  > "본 결과는 위법 여부를 판정하지 않습니다. 공개된 법령·판례 기준과 회사 입력 상태의 대조 결과·기한만 제공하며, 구체 사건의 판단은 전문가의 몫입니다."
- 판단 분기 노출 시 응답에 `expert_referral: true`(코어 §1-7) 가능.

---

## 6. 근거 시드 — `Standard` (rail=labor)

코어 `Standard`(§3-5) 레코드. 근거 배지(L1/L2/L3)의 원천. LB-08(근거 카드)이 렌더.

| tier | title | article | body(요지) | source_url | version |
|---|---|---|---|---|---|
| **L1** | 근로기준법 제36조 | 금품 청산 | "사용자는 근로자가 사망 또는 퇴직한 경우에는 그 지급 사유가 발생한 때부터 **14일 이내**에 임금, 보상금, 그 밖의 일체의 금품을 지급하여야 한다." (실추출) | https://law.go.kr/법령/근로기준법/제36조 | v2025.10 (MST=265959, 시행2025-10-23) |
| **L1** | 근로기준법 제27조 | 해고사유 등의 서면통지 | "사용자는 근로자를 해고하려면 해고사유와 해고시기를 **서면으로 통지**하여야 한다." (실추출) | https://law.go.kr/법령/근로기준법/제27조 | v2025.10 |
| **L1** | 근로기준법 제26조 | 해고의 예고 | "사용자는 근로자를 해고하려면 **적어도 30일 전에 예고**를 하여야 하고, 30일 전에 예고를 하지 아니하였을 때에는 30일분 이상의 통상임금을 지급하여야 한다." (실추출) | https://law.go.kr/법령/근로기준법/제26조 | v2025.10 |
| **L2** | 중앙노동위원회 주요 판정례 (서면통지 위반 계열) | 해고 서면통지(§27) 요구 요소 | "해고하면서 해고사유·시기를 서면으로 통지하지 않은 경우(구두·문자 통보 포함) 부당해고로 판정된 공개 사례가 있다. (중노위 주요 판정사례 — 순번 51·388 등)" | https://www.nlrc.go.kr (중앙노동위 주요 판정사례) | v2026.05 (CSV 399행, 최신 2026-05-06) |
| **L3** | 고용노동부 해고·금품청산 관련 안내 | 해고 절차·금품청산 운영 기준 | 해고 서면통지 방법·금품청산 기한 운영 안내(표준서식·체크리스트). | https://www.moel.go.kr `[시드확인필요: 구체 문서/URL 개발 시드 단계 확정]` | v2026 |

> **[결정필요/시드] L3 구체 문서**: 고용부 가이드의 **구체 문서명·URL**은 개발 시드 단계에서 공개 자료로 확정한다(창작 금지). 계약(배지 shape·tier=L3 존재)은 확정, 문서 특정만 시드 채움. risk/근거 카드는 L3 특정 없이도 L1·L2로 성립.
> **L2 배지 vs 코퍼스**: 배지의 L2는 "중앙노동위 주요 판정례"라는 **대표 1건**(source_url = 중노위)으로 표기. 구체 인용 사례(순번 51·388)는 `LaborPrecedent`(§4)에서 compare `risk` 행이 끌어온다. 배지는 원천 표기, 코퍼스는 대조 데이터 — 역할 분리.

---

## 7. 정합성 규약 (코어와 100% 일치 확인)

- `Case`·`Item`·`Approval`·`Evidence`·`Standard`·`Gate` = 코어 정의 그대로. **재정의 0건.**
- enum `ExitReason`(recommended_resignation 등)·`ItemStatus`(pending/submitted/approved/rejected/not_applicable)·`ItemKind`(statutory/internal/recommended)·`StandardTier`(L1/L2/L3)·`Rail`(labor)·`CompareRowKind`(5행) = 코어 그대로.
- `CompareInput`/`CompareResult` shape = 코어 §6 그대로(5행·boundary_notice·badges).
- **신설 = `LaborPrecedent`(+ `LaborCaseType`·`LaborRequiredElement`·`LaborDeadlineRule` enum)뿐.** `LaborPrecedent`는 참조 코퍼스(case_id 없음), 나머지 enum은 `Item.detail`·compare 규칙 어휘. 코어 FK 규약 준수(판정례는 케이스 비종속이 정당한 예외 — §4 주석). 증적은 코어 `Evidence`로 봉인(LB 전용 증적 신설 없음).
- LB-01 타임라인·LB-02 D-day·LB-03 상태대조 = **모두 코어 `Item`/`Gate` 위의 파생·뷰**(신규 엔티티 아님).

---

*본 문서는 Phase 1 레일 보강이다. 코어 뼈대는 읽기 전용. 코어 변경이 필요하면 도비에 요청(직접 수정 금지). §0·§6의 [결정필요]는 도비 판단 대상.*
