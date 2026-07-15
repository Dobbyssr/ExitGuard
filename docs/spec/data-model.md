# ExitGuard — 공유 코어 데이터 모델 (Phase 0 척추 · freeze 대상)

> **문서 성격** — 3레일(노무 LB / 영업비밀 TS / 보안 SEC)이 공통으로 매다는 **공유 코어 엔티티**의 필드·타입·관계·enum·상태머신을 1벌로 고정한다. 대표2·3의 레일 계약은 여기 정의를 그대로 import한다. **여기서 이름/필드/상태가 흔들리면 3레일이 갈아엎힌다.**
> **근거 SSOT** — 데모(`pitch/데모/ExitGuard-나모업로드-단일본.html`)가 1차 진실(base), `dobby/PRODUCT.md`는 델타. 용어 코드 식별자는 `docs/spec/유비쿼터스.md`와 100% 일치. API 스키마는 `docs/spec/api-spec.md`와 100% 일치.
> **경계** — 이것은 **논리 모델(계약)** 이다. SQLModel 클래스·마이그레이션·인덱스·폴더구조 등 **구현은 론(백엔드) 몫**. 여기서는 "무엇을·어떤 타입·어떤 상태로"까지만 고정한다.
> **작성**: 헤르미온느 · **작성일**: 2026-07-15

---

## 0. 범례·규약

- **타입 표기**: `str` `int` `bool` `datetime`(UTC ISO-8601) `date` `Decimal` `enum` `FK→X` `list[X]` `json`.
- **필수여부**: ● 필수 / ○ 선택(nullable).
- **레일 enum 코드는 `trade_secret`** 로 고정한다. (데모 소스는 축약형 `secret`를 썼다 — 코드 식별자는 `trade_secret`로 통일. 델타 §9-a)
- **주인공 = 김민준**(백엔드 개발자·권고사직·D-3). 기능리스트.md의 "김민수" 표기는 stale이며 데모·PRODUCT·본 문서 기준 **김민준**이 정본. (델타 §9-b)
- **전술적 DDD 아님**: repository/값객체/애그리거트/도메인이벤트 도입하지 않는다. **SQLModel 단일 모델**로 매핑되는 평면 엔티티 + 자연스러운 도메인 메서드 위치만 주석으로 표기한다(§8).

---

## 1. 엔티티 관계 개요

```
User ──(assignee/reviewer)── Approval ──belongs── Item ──belongs── Case
                                                    │                │
Profile ──maps── RailTemplate ──has── TemplateItem─┘ (항목 생성 근원)  │
                                                                      ├── Gate (1:1 파생·집계)
Standard ──referenced by── Item / CompareResult                       └── Evidence (1:N 봉인 이력)
```

- `Case` 1 : N `Item` (케이스가 항목을 가진다. 항목은 3레일에 분산)
- `Item` 1 : N `Approval` (항목별 상신-검토 레코드, 재상신 시 N)
- `Case` 1 : 1 `Gate` (게이트는 케이스의 항목/리스크에서 결정론적으로 파생 — 저장 or 계산, §5)
- `Case` 1 : N `Evidence` (처리 이력 단위의 봉인 레코드)
- `RailTemplate` 1 : N `TemplateItem`; `Profile` N : M `RailTemplate`(레일당 1개 매핑)
- `Standard` — `Item`·`CompareResult`가 근거로 참조(배지)

---

## 2. 열거형 (enum) — 3문서 공통 고정

### 2-1. `Rail` — 레일
| 코드 | 한글 | 접두어 |
|---|---|---|
| `labor` | 노무 | LB / 항목코드 `L-` |
| `trade_secret` | 영업비밀 | TS / 항목코드 `S-` |
| `security` | 보안 | SEC / 항목코드 `C-` |

### 2-2. `ExitReason` — 사유유형 (4종)
| 코드 | 한글 | 비고 |
|---|---|---|
| `voluntary` | 자발 | |
| `recommended_resignation` | 권고사직 | 김민준 케이스 |
| `dismissal` | 해고 | 해고예고·서면통지 대상 |
| `contract_expiry` | 계약만료 | 갱신기대권 검토 대상 |

### 2-3. `ItemStatus` — 검사항목 상태 (★상태머신 §4)
| 코드 | 한글(데모 표기) | 의미 |
|---|---|---|
| `pending` | 대기 | 아직 상신 전 |
| `submitted` | 상신됨 / 상신검토필요 | 담당자가 상신, 관리자 검토 대기 |
| `approved` | 충족(done) | 관리자 확인완료 |
| `rejected` | 반려 | 관리자 반려 → 재상신 필요 |
| `not_applicable` | 해당없음(na) | 유형상 대상 아님(예: 권고사직→해고예고 30일) |

> 데모 렌더 상태 `done`은 `approved`의 표시명이다(코드는 `approved`로 통일).

### 2-4. `ItemKind` — 항목 구분(필수성)
| 코드 | 한글 | 게이트 blocking 기본값 |
|---|---|---|
| `statutory` | 법정 | `true` (미충족 시 risk 카운트) |
| `internal` | 내규 | `false` |
| `recommended` | 권고 | `false` |

> 데모의 항목 태그 `법정`/`내규`/`권고`에 대응. `external`(외부)은 레일 확장용 예약(대표2·3이 필요 시 추가). blocking 여부는 `TemplateItem.blocking`으로 항목별 오버라이드 가능(§7).

### 2-5. `StandardTier` — 근거 층위 (근거 배지 L1/L2/L3)
| 코드 | 배지 | 한글 | 원천 |
|---|---|---|---|
| `L1` | L1 | 법령 | 국가법령정보센터(근기법·부정경쟁방지법 등) |
| `L2` | L2 | 판례·판정례 | 대법원 판례·중노위 판정례 |
| `L3` | L3 | 정부 가이드 | 고용부·특허청 매뉴얼·표준서식 |

### 2-6. `Role` — 사용자 역할
| 코드 | 한글 |
|---|---|
| `admin` | 관리자(상신 검토·승인·권한부여) |
| `user` | 일반사용자(담당자 — 레일 수행·대리 상신) |

> 퇴사자 본인 로그인 없음. 대상자는 액터가 아니라 데이터(Case). (PRODUCT §3-4)

### 2-7. `CompareRowKind` — 대조결과 행 종류 (5행 고정 §6)
`procedure`(절차) · `standard`(기준 대조) · `risk`(위험) · `status`(상태 대조) · `source`(출처)

---

## 3. 코어 엔티티

### 3-1. `Case` — 케이스(퇴사 1건)
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `subject_name` | str | ● | 대상자(퇴사자) 이름 — 예: 김민준 |
| `subject_job` | str | ● | 직무/직종 — 예: 개발 (Profile 매칭 축) |
| `subject_rank` | str | ● | 직급 — 예: 시니어 책임 |
| `subject_role_title` | str | ○ | 직책/역할명 — 예: 백엔드 개발자 |
| `exit_reason` | enum ExitReason | ● | 사유유형 4종 |
| `reason_text` | str | ○ | 회사사유 입력 텍스트(폼 입력 — compare 엔진 입력원) |
| `exit_date` | date | ● | 퇴직 예정일(기한 계산 기준) |
| `intake_route` | enum(`groupware`\|`dismissal`\|`resignation`) | ● | 접수경로 3종(CM-04) |
| `profile_id` | FK→Profile | ○ | 직무·직급→적용 프로파일(항목 자동배정) |
| `status` | enum(`in_progress`\|`review_waiting`\|`completed`) | ● | 케이스 진행상태(목록 필터 CM-03) |
| `created_by` | FK→User | ● | 접수 담당자 |
| `created_at` | datetime | ● | |
| `updated_at` | datetime | ● | |

- 파생값(저장 아님, 계산): `gate`(§5), 레일별 완료율. → API 상세응답에 포함.
- 도메인 메서드 위치(§8): `Case.classify_reason()`(reason_text 신호 분류는 compare 서비스 위임), `Case.apply_profile()`(프로파일→항목 생성).

### 3-2. `Item` — 검사항목
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `case_id` | FK→Case | ● | 소속 케이스 |
| `rail` | enum Rail | ● | 소속 레일 |
| `code` | str | ● | 항목코드 — `L-04`/`S-02`/`C-11` 등(레일 접두어 §2-1) |
| `name` | str | ● | 항목명 — 예: 금품청산 (14일) |
| `kind` | enum ItemKind | ● | 법정/내규/권고 |
| `status` | enum ItemStatus | ● | 상태머신(§4). 초기 `pending` |
| `blocking` | bool | ● | 게이트 차단 여부(TemplateItem에서 상속, §5) |
| `sub` | str | ○ | 진행 요약 한 줄 — 예: "잔여 4일 · 정산 반영 완료" |
| `deadline` | date | ○ | 법정 기한(있으면). 레일 상세 규칙은 대표2·3 |
| `standard_ids` | list[FK→Standard] | ○ | 근거 배지(L1/L2/L3) |
| `detail` | json | ○ | **레일별 상세 필드 예약 슬롯**(노무 기한요소 / TS 자산3요소 / SEC 회수대상). Phase 1에서 대표2·3이 스키마 확정. Phase 0은 뼈대만. |
| `created_at` / `updated_at` | datetime | ● | |

> ★ `detail`(json)이 **레일별 확장 예약 지점**이다. 대표2는 노무 기한 필드를, 대표3은 TS 자산 3요소·SEC 회수항목을 여기(또는 별도 레일 테이블)에 얹는다. Phase 0은 공통 필드만 고정.

### 3-3. `Approval` — 상신-검토 레코드
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `item_id` | FK→Item | ● | 대상 항목 |
| `submitter_id` | FK→User | ● | 상신자(담당자 — 대리 상신) |
| `memo` | str | ○ | 상신 메모 — 예: "급여·퇴직금·연차 4일 수당 반영 정산" |
| `attachments` | list[json{name,size}] | ○ | 첨부 문서 — 예: 급여정산내역서.pdf |
| `signed` | bool | ● | 전자서명 여부 |
| `basis_note` | str | ○ | 기준 근거 문구 — 예: "근로기준법 §36 금품청산 14일 이내" |
| `reviewer_id` | FK→User | ○ | 검토자(관리자) |
| `decision` | enum(`confirmed`\|`rejected`) | ○ | 검토 결과(미검토 시 null) |
| `reviewed_at` | datetime | ○ | |
| `submitted_at` | datetime | ● | |

- `decision=confirmed` → Item `submitted`→`approved`. `decision=rejected` → Item `submitted`→`rejected`(재상신 가능).
- 도메인 메서드 위치(§8): `Approval.confirm()` / `Approval.reject()` (Item 상태전이 트리거).

### 3-4. `Evidence` — 증적(변경불가·봉인)
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `case_id` | FK→Case | ● | 소속 케이스 |
| `seq` | int | ● | 처리 순번(이력 순서) |
| `occurred_at` | datetime | ● | 처리 일시 |
| `actor` | str | ● | 수행자 |
| `action` | str | ● | 처리 내용 — 예: "금품청산 정산 확인완료" |
| `document_ref` | str | ○ | 관련 문서명 |
| `payload` | json | ● | 봉인 대상 스냅샷(항목·상신·검토 사실) |
| `integrity_hash` | str | ● | SHA-256 해시(payload 무결성) |
| `prev_hash` | str | ○ | 직전 레코드 해시(체인 — 변경 탐지) |
| `sealed_at` | datetime | ● | 봉인 시각 |

- **변경불가**: 생성 후 수정 불가(append-only). `integrity_hash` = SHA-256(payload), `prev_hash` 체인으로 이력 위변조 탐지.
- Case 단위 봉인 상태: `sealed`(봉인완료) / `accruing`(축적중) — 아카이브 목록(CM-14)에서 파생.
- 도메인 메서드 위치(§8): `Evidence.seal()`(해시 계산·봉인), `Case.export_report()`(봉인 증적→PDF, CM-13).

### 3-5. `Standard` — 근거(3층 기준 스택)
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `tier` | enum StandardTier | ● | L1/L2/L3 |
| `rail` | enum Rail | ● | 소속 레일 |
| `title` | str | ● | 예: "근로기준법 제27조" / "부정경쟁방지법 제2조" |
| `article` | str | ○ | 조문/요지 — 예: "해고사유·시기 서면통지" |
| `body` | str | ○ | 인용 원문(compare `standard` 행에 사용) |
| `source_url` | str | ○ | 원문 링크(출처 배지) |
| `version` | str | ● | 예: `v2026.06` |
| `updated_at` | datetime | ● | 최신 반영 |

- 근거 배지 표현: `{tier, title, source_url, version}`. (API 배지 규약 = api-spec §공통)

### 3-6. `RailTemplate` + `TemplateItem` — 레일 템플릿(항목 라이브러리)
`RailTemplate` (레일별 기본 항목 묶음 = 케이스 체크리스트의 기준. "빈 종이 빌더 금지")
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `rail` | enum Rail | ● | |
| `name` | str | ● | 예: "기본 노무 템플릿" / "개발직 강화 템플릿" |
| `is_base` | bool | ● | 우리 제공 기본(L1 큐레이션=해자) vs 회사 커스텀 |

`TemplateItem` (템플릿에 담긴 항목 정의 → Case 접수 시 `Item`으로 복제)
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `rail_template_id` | FK→RailTemplate | ● | |
| `code` | str | ● | 항목코드(L-/S-/C-) |
| `name` | str | ● | |
| `kind` | enum ItemKind | ● | 법정/내규/권고 |
| `blocking` | bool | ● | 게이트 차단 여부(기본 `kind==statutory`) |
| `standard_ids` | list[FK→Standard] | ○ | 근거 |
| `detail_schema` | json | ○ | **레일별 필드 예약**(대표2·3 Phase 1) |

### 3-7. `Profile` — 직종·직급 프로파일(2계층 매핑)
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `name` | str | ● | 예: "개발직 · 시니어 이상" / "표준 (공통)" |
| `job` | str | ○ | 직종 축 |
| `rank` | str | ○ | 직급 축 |
| `rail_map` | json{labor,trade_secret,security → rail_template_id} | ● | 레일별 적용 RailTemplate 매핑 |

> **템플릿 2계층** = `Profile`(직종·직급 → 레일별 어떤 템플릿) → `RailTemplate`/`TemplateItem`(그 템플릿의 항목). Case가 `profile_id`를 받으면 rail_map의 각 RailTemplate의 TemplateItem을 `Item`으로 복제 생성(Fork & Customize). PRODUCT §3-3.

### 3-8. `User` — 사용자
| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `name` | str | ● | 예: 한지수 |
| `email` | str | ● | 로그인 ID |
| `role` | enum Role | ● | admin/user |
| `granted_scopes` | list[str] | ○ | admin이 user에게 부여한 권한(상신/레일수행/승인) |

> 인증은 CP 밖(데모는 관리자 로그인 상태로 시작). 2역할만. (PRODUCT §6-4)

---

## 4. 검사항목 상태머신 (`Item.status`) ★

```
        [접수·프로파일 적용]
                │
                ▼
   (유형상 대상 아님?)──yes──► not_applicable  (해당없음)
                │no
                ▼
            pending ──담당자 상신(Approval 생성)──► submitted
                                                     │
                        관리자 확인(decision=confirmed) │ 관리자 반려(decision=rejected)
                                       ┌──────────────┴──────────────┐
                                       ▼                             ▼
                                   approved (충족·done)           rejected (반려)
                                                                     │
                                                          재상신(새 Approval)
                                                                     ▼
                                                                 submitted
```

- **전이 트리거**: `pending→submitted`=담당자 상신, `submitted→approved`=관리자 confirmed, `submitted→rejected`=관리자 rejected, `rejected→submitted`=재상신, `*→not_applicable`=유형 규칙(접수 시 자동, 예: 권고사직→L-09 해고예고 na).
- **불변식**: `approved`/`not_applicable`만 게이트 "미충족 아님"으로 집계(§5).
- 데모 대응: L-01 approved(done), L-04 submitted(ap1), L-06 pending(ap2 대기), L-09 not_applicable(권고사직).

---

## 5. 통합 게이트 집계 (`Gate`) — 결정론적 파생 ★

`Gate`는 **저장 엔티티가 아니라 Case의 Item들에서 결정론적으로 계산되는 파생 객체**다(캐시로 저장 가능하나 진실은 계산식).

**필드(파생)**
| 필드 | 타입 | 계산 |
|---|---|---|
| `case_id` | FK→Case | |
| `rail_completion` | dict{rail→int%} | 레일별 완료율 |
| `overall_completion` | int% | 전체 완료율 |
| `risk_count` | int | 미해소 리스크(미충족 blocking 항목 수) |
| `defensible` | bool | `risk_count == 0` → "방어 가능 상태" |

**결정론적 계산식 (freeze)**
```
applicable(rail)   = count(items[rail] where status != not_applicable)
approved(rail)     = count(items[rail] where status == approved)
rail_completion[r] = round(100 * approved(r) / max(1, applicable(r)))

overall_completion = round(100 * sum_r approved(r) / max(1, sum_r applicable(r)))

risk_count = count(items where item.blocking == true
                              and status not in {approved, not_applicable})
defensible = (risk_count == 0)
```
- `defensible=true` → 종합 표시 "방어 가능 상태"(=승인). `risk_count>0` → "관제 중 · 미해소 리스크 N건".
- **경계**: 이 집계는 항목 상태의 **기계적 합산**이며 법적 판단이 아니다. "방어 가능 상태"는 *공개 기준 대비 항목 충족 상태*를 뜻하며 승소·적법을 보증하지 않는다.
- `blocking`은 `TemplateItem.blocking`→`Item.blocking`으로 상속(기본 `kind==statutory`). 데모 수치와의 미세정합은 시드에서 항목 blocking/status로 조정(캘리브레이션 knob).

---

## 6. compare 엔진 계약 shape (공용) ★ — 론 `app/services/compare.py`가 구현할 인터페이스

CM-05(인테이크 대조)·LB-04(판정례 대조)·TS-05(비밀관리성 대조) **세 레일 공용**. 여기서 shape를 고정하므로 레일은 규칙만 채운다.

### 6-1. Input — `CompareInput`
```
CompareInput {
  rail: Rail
  subject: str            # 대상 식별 — 항목코드(L-04) 또는 인테이크 신호 토픽
  case_facts: {           # 케이스 사실
    reason_text: str      # 회사사유 텍스트(신호 추출 원천)
    exit_reason: ExitReason
    exit_date: date
    job: str, rank: str
  }
  item_context: {         # 대조 대상 항목/기준(선택 — 인테이크는 없이 신호 스캔)
    code: str | null
    name: str | null
    standard_refs: list[Standard.id]
  } | null
}
```

### 6-2. Output — `CompareResult` (대조결과 5행 고정)
```
CompareResult {
  rail: Rail
  subject: str
  rows: [                          # 정확히 5행, kind 순서 고정
    { kind: "procedure", text }    # 절차: 사유 텍스트에서 리스크 신호 추출·분류
    { kind: "standard",  text }    # 기준 대조: 공개 기준 원문 인용 + 조문
    { kind: "risk",      text }    # 위험: "누락 시 …로 판정된 사례가 있습니다"(사례 프레이밍)
    { kind: "status",    text }    # 상태 대조: 현재 입력 대비 "미충족 N건" / 기한 D-day
    { kind: "source",    text, url }  # 출처: 원문 링크
  ]
  unmet_count: int                 # "미충족 N건"
  badges: [ { tier: StandardTier, title, url, version } ]   # 근거 배지 L1/L2/L3
  boundary_notice: str             # 고정 문구(§6-3)
}
```

### 6-3. 경계 주석 (직역법 §4 — 스키마 강제) ★
- `boundary_notice` **고정 문구**: `"본 결과는 위법 여부를 판정하지 않습니다. 공개된 법령·판례 기준과 회사 입력 상태의 대조 결과·기한만 제공하며, 구체 사건의 판단은 전문가의 몫입니다."`
- `risk` 행은 **단정 금지**. 반드시 "…로 판정된 **사례가 있습니다**" / "…리스크가 발생한 **공개 사례가 있습니다**" 프레이밍. ("위법입니다"/"부당해고입니다"/"패소합니다" 금지)
- `status` 행은 "미충족 N건" / "기한 D-day" 대조·관제 프레이밍만. "개선방안 제시" 어조 금지(노무관리진단 정의 회피 — PRODUCT §4).
- LLM 산출은 **공개 기준 인용·링크 위주**. 생성형 법률 판단·자문 배제. 판단 분기에는 상위 UI가 [전문가 연결]을 노출(api-spec 참조).

---

## 7. 레일 확장 예약 지점 (대표2·3가 여기에 붙인다)

| 예약 지점 | 위치 | 채우는 사람 |
|---|---|---|
| 노무 항목 상세(기한요소·정산 필드) | `Item.detail` / `TemplateItem.detail_schema` (rail=labor) | 대표2 |
| 영업비밀 자산 3요소(비밀표시·재서약·접근제한) | `Item.detail` (rail=trade_secret) — 자산 인벤토리는 별도 레일 테이블 신설 가능 | 대표3 |
| 보안 회수항목(계정·SaaS·기기) | `Item.detail` (rail=security) | 대표3 |
| 레일별 compare 규칙(신호→기준 매핑) | `compare.py` 레일 구현(shape는 §6 고정) | 대표2·3 |
| 레일 근거 시드 | `Standard`(rail별 L1/L2/L3 레코드) | 대표2·3 |

> Phase 0은 위 슬롯의 **존재와 타입**만 고정한다. 슬롯 내부 필드 정의는 Phase 1(레일별)이다.

---

## 8. 도메인 메서드 위치(주석 — 전술적 DDD 아님)

SQLModel 단일 모델에 자연스러운 상태전이/파생 메서드를 어디 두는지의 **가이드**일 뿐, 별도 계층을 만들라는 뜻이 아니다. 론은 도메인 향 3단(routers→services→db)에서 services에 배치.

- `Case.apply_profile()` — 프로파일 rail_map → Item 복제 생성 (case 서비스)
- `Item.transition(to)` — 상태머신 §4 검증·전이 (case 서비스)
- `Approval.confirm()/reject()` — Item 전이 트리거 (case 서비스)
- `Gate.compute(case)` — §5 결정론적 집계 (case 서비스, 순수함수)
- `compare(input) -> CompareResult` — §6 (compare 서비스, 레일 규칙 분기)
- `Evidence.seal(payload, prev)` — SHA-256 봉인·체인 (evidence 서비스)
- `Case.export_report()` — 봉인 증적 → PDF (evidence 서비스)

---

## 9. 델타 로그 (데모 base → 본 문서)

- **(a) 레일 코드**: 데모 소스 축약형 `secret` → 코드 식별자 **`trade_secret`** 통일(브리프 지시·용어집 정합).
- **(b) 주인공**: 데모·PRODUCT = **김민준**. 기능리스트.md의 "김민수"는 stale → 김민준이 정본.
- **(c) 상태 명명**: 데모 렌더 `done` → 코드 `approved`. `na` → `not_applicable`.
- **(d) Gate**: 데모 정적 % → §5 결정론적 계산식으로 파생(고도화).
- **(e) Evidence**: 데모 "SHA-256 무결성·수정 불가" 표기 → `integrity_hash`+`prev_hash` 체인으로 계약화(진짜 봉인).

---

*본 문서는 Phase 0 freeze 대상 척추다. 변경 시 api-spec.md·유비쿼터스.md·레일 계약(대표2·3)에 파급되므로 도비 승인 후 3문서 동시 갱신한다.*
