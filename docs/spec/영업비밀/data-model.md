# ExitGuard — 영업비밀(TS) 레일 데이터 모델 (Phase 1 · 레일 보강)

> **문서 성격** — 공유 코어(`../data-model.md`)를 **import만** 하고, 영업비밀 레일 고유 데이터(접근 자산 인벤토리·보호요건 3요소·비밀관리성 대조 규칙)만 보강한다.
> **뼈대 재정의 금지** — `Case`·`Item`·`Approval`·`Evidence`·`Standard`·`Gate`·enum(`Rail`,`ItemStatus`,`ItemKind`,`StandardTier`)·`CompareInput`/`CompareResult` shape는 코어에서 그대로 가져온다. 여기서 다시 정의하지 않는다.
> **근거 SSOT** — 데모(`pitch/데모/ExitGuard-나모업로드-단일본.html`)가 1차 진실. 자산 6건·KPI(13/4/7)·완료율 40%는 데모 값. 창작 금지.
> **레일 코드** — `trade_secret` (접두어 TS · 항목코드 `S-`). 데모 축약형 `secret`은 stale.
> **작성**: 헤르미온느 · **작성일**: 2026-07-16

---

## 1. 레일 확장 지점 (코어 §7 예약 슬롯 중 TS가 채우는 것)

| 코어 예약 지점 | TS가 채우는 내용 | 위치 |
|---|---|---|
| 별도 레일 테이블(코어 §7 "자산 인벤토리는 별도 레일 테이블 신설 가능") | **`TradeSecretAsset`** — 접근 자산 13건 인벤토리 + 3요소 | §2 (신설) |
| `Item.detail`(rail=trade_secret) | TS 검사항목(S-02 재서약·S-07 반출자료 회수 등) 상세 | §3 |
| `compare.py` TS 규칙(shape 고정) | 비밀관리성 패턴 → L2 판례 요소 매핑(TS-05) | §4 |
| `Standard`(rail=trade_secret) L1/L2/L3 | 부경법 §2·비밀관리성 판례·특허청 매뉴얼 | §5 |

> **왜 별도 테이블인가**: 코어 `Item`은 "검사항목(재서약·회수 등 처리 단위)"이다. TS **자산**(핵심도면·API키 등 13건, 각 3요소 상태)은 검사항목이 아니라 대조 대상 데이터다. 개념이 다르므로 코어 §7이 허용한 별도 레일 테이블로 신설한다. 코어 FK(`case_id`)·증적 규약은 준수한다.

---

## 2. `TradeSecretAsset` — 접근 자산 인벤토리 (신설 · 레일 전용) ★

퇴사자가 접근한 핵심 자산 1건 = 1행. `Case` 1 : N `TradeSecretAsset`. **TS-01(자동 특정)의 산출물이자 TS-02(3요소 대조)·TS-05(비밀관리성)의 입력.**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `case_id` | FK→Case | ● | 소속 케이스(코어 FK 규약) |
| `name` | str | ● | 자산명 — 예: `핵심도면_v7` (데모값) |
| `category` | enum AssetCategory | ● | 분류(§2-1) |
| `secret_mark` | bool | ● | 비밀표시 요소(3요소 ①) — ✓표시 / ✕없음 |
| `re_pledge` | bool | ● | 재서약 요소(3요소 ②) — ✓완료 / ✕미체결 |
| `access_control` | bool | ● | 접근제한 요소(3요소 ③) — ✓제한 / ✕전원 |
| `protection_status` | enum AssetProtectionStatus | ● | 3요소에서 **결정론적 파생**(§2-3). 저장 아님(계산) |
| `source` | str | ○ | 특정 근거 — 예: "권한대장·접근로그"(TS-01 입력, **시뮬**) |
| `is_sim` | bool | ● | 입력 데이터 출처. 자산 특정 **로직=진짜구현 / 입력=시뮬데이터**(기능리스트 §7 분리표기) → 본 MVP는 전부 `true` |
| `created_at` / `updated_at` | datetime | ● | |

> ★ 자산은 **상신-검토(Approval) 대상이 아니다.** 자산의 보완(재서약·비밀표시)은 해당 TS **검사항목**(`Item` S-02 재서약 / S-07 회수)의 상신-검토로 처리되고, 자산의 3요소 상태는 그 처리 결과로 갱신된다(§3 연계).

### 2-1. `AssetCategory` — 자산 분류 (enum, 데모 정합)
| 코드 | 한글 | 데모 예시 |
|---|---|---|
| `design` | 설계도면 | 핵심도면_v7 · 인프라_구성도 |
| `data` | 데이터 | 고객DB_스키마 |
| `credential` | 자격증명 | API_인증키_모음 |
| `source_code` | 소스코드 | 배포_스크립트_v3 |
| `document` | 문서 | 사업계획_2026 |

### 2-2. `AssetProtectionStatus` — 보호요건 상태 (enum, 4종 · 데모 정합)
| 코드 | 한글(데모 배지) | 색 |
|---|---|---|
| `met` | 충족 | green |
| `re_pledge_needed` | 재서약 필요 | amber |
| `mark_needed` | 표시 필요 | amber |
| `unmet` | 요건 미충족 | red |

### 2-3. `protection_status` 결정론적 파생식 (freeze) ★
3요소 bool에서 기계적으로 계산한다. **법적 판단이 아니라 요소 대조 결과다.**

```
# 결여 요소의 개수(count)로 계산한다. 집합(set)이 아니라 개수다.
# (bool을 set literal로 넣으면 값이 겹칠 때 중복 제거되어 개수가 왜곡됨 — 주의)
missing_count = int(not secret_mark) + int(not re_pledge) + int(not access_control)

if missing_count == 0:               protection_status = met
elif not access_control:             protection_status = unmet          # 전원 접근 = 비밀관리성 핵심 요소 결여
elif missing_count >= 2:             protection_status = unmet
elif not re_pledge (유일 결여):       protection_status = re_pledge_needed
elif not secret_mark (유일 결여):     protection_status = mark_needed
```

**데모 6행 전수 대조 (캘리브레이션 knob — 시드가 이 표를 재현해야 함)**:
| 자산명 | 비밀표시 | 재서약 | 접근제한 | → status | 데모 배지 |
|---|---|---|---|---|---|
| 핵심도면_v7 | ✕ | ✕ | ✓ | `unmet` (2결여) | 요건 미충족 ✓ |
| 고객DB_스키마 | ✓ | ✕ | ✓ | `re_pledge_needed` | 재서약 필요 ✓ |
| API_인증키_모음 | ✓ | ✓ | ✕ | `unmet` (접근제한 결여) | 요건 미충족 ✓ |
| 배포_스크립트_v3 | ✓ | ✓ | ✓ | `met` | 충족 ✓ |
| 사업계획_2026 | ✕ | ✓ | ✓ | `mark_needed` | 표시 필요 ✓ |
| 인프라_구성도 | ✓ | ✓ | ✓ | `met` | 충족 ✓ |

6행 전부 데모 배지와 일치.

### 2-4. 자산 인벤토리 요약 (KPI 파생 · 데모 §10 정합)
`GET /cases/{id}/rails/trade_secret` 응답의 `asset_summary`로 노출(§api-spec).
```
asset_count          = count(assets)                                = 13   # 접근 자산
protection_unmet     = count(assets where protection_status==unmet) =  4   # 보호요건 미충족
re_pledge_pending    = count(assets where re_pledge==false)         =  7   # 재서약 미체결
```
- **데모값(유비쿼터스 §10)**: 접근자산 **13** · 보호요건 미충족 **4** · 재서약 미체결 **7**.
- **시드 정합 규약**: 데모 자산표는 13건 중 **6건만 명시**(§2-3). 나머지 **7건은 시뮬 시드**로 `is_sim=true`로 채워 KPI(13/4/7)를 맞춘다 — 자산명은 계약에 load-bearing 아님(개발 시드에서 결정). 명시 6건은 데모값 verbatim 고정.
  - 미충족 4건 = 명시 2건(핵심도면·API키) + 시뮬 2건.
  - 재서약 미체결 7건 = 명시 2건(핵심도면·고객DB) + 시뮬 5건.

---

## 3. `Item.detail` — TS 검사항목 상세 (rail=trade_secret)

TS **검사항목**(`Item`, 코어 §3-2)의 `detail`(json) 슬롯 스키마. 자산 인벤토리(§2)와 별개. 데모 템플릿/항목 정합.

```
Item.detail (rail=trade_secret) {
  requirement_focus: enum { secret_mark | re_pledge | access_control | asset_recovery } | null
                       # 이 항목이 어느 보호요건을 처리하는가(자산 3요소 연계)
  related_asset_ids: list[TradeSecretAsset.id]   # 이 항목이 대상으로 하는 자산(예: S-07 회수 → 미충족 자산들)
}
```

**데모 정합 TS 검사항목(항목코드 S- · 코어 `Item`으로 생성)**:
| code | name | kind | status(데모) | detail.requirement_focus |
|---|---|---|---|---|
| `S-02` | 퇴직 비밀유지 재서약 | 내규(`internal`) | `submitted`→`approved` | `re_pledge` |
| `S-07` | 핵심도면·API키 반출자료 회수 | 권고(`recommended`) | `pending` | `asset_recovery` |
| `S-01` | 비밀표시 점검 | 내규 | (템플릿) | `secret_mark` |
| `S-03` | 접근권한 말소 | 내규 | (템플릿) | `access_control` |
| `S-05` | 개인기기 자료 삭제 확인 | 내규 | (템플릿) | `asset_recovery` |

- S-02 sub(데모): "대상자 전자서명 상신 · 확인 필요" → 확인 시 "전자서명 확인 완료".
- S-07 sub(데모): "접근 자산 13건 중 보호요건 미충족 4건".
- **연계**: S-02 재서약 `approved` → 해당 자산들의 `re_pledge=true` 갱신 → `protection_status` 재파생. (자산 3요소는 검사항목 처리 결과의 뷰)
- **blocking**: 데모 TS 항목은 내규/권고(`blocking=false`) 위주 → TS 미충족은 게이트 `risk_count`를 직접 올리지 않을 수 있음. 게이트 집계는 코어 §5식 그대로(레일에서 재정의 금지). TS 완료율은 코어 Gate 파생(데모 40%).

> TS 템플릿(데모 `RAIL_PRESETS.secret`): 기본 영업비밀 템플릿 / 개발·연구직 강화 템플릿 / 영업직 강화 템플릿. 코어 `RailTemplate`/`TemplateItem`으로 표현(재정의 아님).

---

## 4. compare 규칙 — 비밀관리성 대조 (TS-05) ★

**shape는 코어 §6 `CompareInput`/`CompareResult` 그대로. 여기서는 TS 레일의 *규칙 내용*만 채운다.**

### 4-1. 입력
```
CompareInput {
  rail: "trade_secret"
  subject: "TS-05:secret_management" | asset_id           # 케이스 전체 또는 자산 단위
  case_facts: { reason_text, exit_reason, exit_date, job, rank }
  item_context: { code: "S-01"|null, name, standard_refs: [부경법§2, 비밀관리성 판례] }
}
```

### 4-2. 신호 → 판례 요소 매핑 규칙 (비밀관리성 패턴)
자산 인벤토리(§2)의 3요소 상태에서 **비밀관리성 결여 신호**를 스캔한다.

| 신호(패턴) | 원천 | → 매핑되는 판례 요구 요소(L2) |
|---|---|---|
| `secret_mark==false` (비밀표시 없음) | 자산 3요소 | 비밀관리성: **비밀 표시·분류** 조치 |
| `access_control==false` (전원 접근) | 자산 3요소 | 비밀관리성: **접근 권한 제한**(대상·범위 통제) |
| `re_pledge==false` (재서약 미체결) | 자산 3요소 / S-02 | 비밀관리성: **비밀유지의무 부과**(서약) |
| 복합("비밀표시 없음 + 전원 접근") | 위 2개 동시 | 비밀관리성 **부정** 위험 신호 |

### 4-3. 출력 5행(코어 §6-2 고정 kind 순서) — TS-05 규칙이 채우는 텍스트

| kind | TS-05가 채우는 내용 |
|---|---|
| `procedure` | 자산 인벤토리에서 추출한 비밀관리성 결여 신호 요약 — 예: "비밀표시 없는 자산 N건 · 전원 접근 자산 M건" |
| `standard` | L1 인용: 부정경쟁방지법 §2 — 영업비밀은 **"비밀로 관리된"** 정보(비밀관리성)여야 보호대상. |
| `risk` | **사례 프레이밍(단정 금지)**: "비밀표시가 없고 접근이 제한되지 않은 자료에 대해, 공개 판례에서 **비밀관리성이 인정되지 않아 영업비밀로 보호받지 못한 것으로 판단된 사례가 있습니다.**" |
| `status` | 대조 결과: "접근 자산 13건 중 보호요건 미충족 **4건** · 재서약 미체결 **7건**"(미충족 N건 프레이밍) |
| `source` | 출처 링크: 부경법 §2(law.go.kr) + 특허청 영업비밀 관리 매뉴얼 |

- `unmet_count` = `protection_unmet`(=4) 등 대조 대상별 미충족 수.
- `badges` = §5 Standard 레코드(L1/L2/L3)에서 생성.
- `boundary_notice` = **코어 §6-3 고정 문구 그대로**(재작성 금지):
  > "본 결과는 위법 여부를 판정하지 않습니다. 공개된 법령·판례 기준과 회사 입력 상태의 대조 결과·기한만 제공하며, 구체 사건의 판단은 전문가의 몫입니다."

---

## 5. 근거 시드 — `Standard` (rail=trade_secret)

코어 `Standard`(§3-5) 레코드. 근거 배지의 원천.

| tier | title | article | body(요지) | source_url | version |
|---|---|---|---|---|---|
| **L1** | 부정경쟁방지 및 영업비밀보호에 관한 법률 제2조 | 영업비밀의 정의·보호요건 | "'영업비밀'이란 공공연히 알려져 있지 아니하고 독립된 경제적 가치를 가지는 것으로서 **비밀로 관리된** 생산방법·판매방법, 그 밖에 영업활동에 유용한 기술상·경영상의 정보를 말한다." (비밀관리성 요건) | https://law.go.kr/법령/부정경쟁방지및영업비밀보호에관한법률 | v2026.06 |
| **L2** | 영업비밀 비밀관리성 판단 기준(대법원 판례 요소) | 비밀관리성 인정 요소 | "법원은 정보 보유자가 **비밀 표시·분류, 접근 권한 제한, 비밀유지의무 부과** 등 객관적으로 비밀로 관리하려는 조치를 취했는지를 종합하여 비밀관리성을 판단한다. 해당 조치가 없으면 비밀관리성이 인정되지 않은 사례가 있다." | [시드확인필요: 구체 사건번호는 개발 시드 단계에서 공개 판례 확정 — 헤르미온느가 사건번호를 창작하지 않음] | v2026.06 |
| **L3** | 특허청 「영업비밀 보호를 위한 관리 매뉴얼」 | 비밀관리 체계·표준서식 | 비밀 표시 방법·접근권한 관리·비밀유지 서약서 표준서식 등 운영 체크리스트(가장 안전한 원천). | https://www.tradesecret.or.kr (한국특허정보원 영업비밀보호센터) | v2026.06 |

> **[결정필요] L2 사건번호**: 비밀관리성 부정 판례의 **구체 사건번호**는 실제 공개 판례로 확정해야 한다(창작 금지). 계약(shape·요소 매핑)은 확정, 사건번호만 시드 채움 단계 확인. risk 행은 사건번호 없이도 "…판단된 사례가 있습니다" 프레이밍으로 안전.

---

## 6. 정합성 규약 (코어와 100% 일치 확인)

- `Case`·`Item`·`Approval`·`Evidence`·`Standard`·`Gate` = 코어 정의 그대로. **재정의 0건.**
- enum `ItemStatus`(pending/submitted/approved/rejected/not_applicable)·`ItemKind`(statutory/internal/recommended)·`StandardTier`(L1/L2/L3)·`Rail`(trade_secret) = 코어 그대로.
- `CompareInput`/`CompareResult` shape = 코어 §6 그대로(5행·boundary_notice·badges).
- 신설 = `TradeSecretAsset`(+ `AssetCategory`·`AssetProtectionStatus` enum)뿐. 코어 FK(`case_id`) 규약 준수. 증적은 코어 `Evidence`로 봉인(TS 전용 증적 신설 없음).

---

*본 문서는 Phase 1 레일 보강이다. 코어 뼈대는 읽기 전용. 코어 변경이 필요하면 도비에 요청(직접 수정 금지).*
