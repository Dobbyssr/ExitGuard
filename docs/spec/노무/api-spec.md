# ExitGuard — 노무(LB) 레일 API 명세 (Phase 1 · 레일 엔드포인트)

> **문서 성격** — 코어 `../api-spec.md`가 **예약**한 `GET /cases/{id}/rails/labor`의 내부 응답을 채운다. 공통 규약(envelope·에러·배지·직역법 §1-6/§1-7)은 코어 그대로 재사용.
> **뼈대 재정의 금지** — 상신/검토/게이트/증적/근거조회/compare는 **코어 §2 엔드포인트 재사용**(LB 전용 신설 없음). LB 고유 데이터 조회만 신설.
> **필드·타입** — `./data-model.md`(LB 레일) + `../data-model.md`(코어) 참조. 여기선 shape만.
> **작성**: 헤르미온느 · **작성일**: 2026-07-20

---

## 1. `GET /cases/{id}/rails/labor` — 노무 레일 상세 (LB-01·02·03) `[both]`

코어 뼈대 응답 `{ rail, completion, items, compare, badges }` + LB 고유 `timeline`·`item_summary` 확장.

**응답 200 `data`**:
```json
{
  "rail": "labor",
  "completion": 40,
  "item_summary": {
    "total_count": 6,
    "met_count": 2,
    "unmet_count": 3,
    "na_count": 1
  },
  "timeline": [
    { "code": "L-04", "name": "금품청산 (14일)", "deadline_rule": "settlement_14d",
      "deadline_basis": "근로기준법 제36조", "deadline": "2026-08-02", "dday": 3,
      "timeline_group": "settlement" },
    { "code": "L-02", "name": "연차 미사용 수당 정산", "deadline_rule": "settlement_14d",
      "deadline_basis": "근로기준법 제36조", "deadline": "2026-08-02", "dday": 3,
      "timeline_group": "settlement" },
    { "code": "L-06", "name": "이직확인서 발급", "deadline_rule": "separation_cert",
      "deadline_basis": null, "deadline": null, "dday": null, "timeline_group": "filing" },
    { "code": "L-08", "name": "4대보험 상실신고", "deadline_rule": "insurance_loss",
      "deadline_basis": null, "deadline": null, "dday": null, "timeline_group": "filing" },
    { "code": "L-09", "name": "해고예고 (30일)", "deadline_rule": "dismissal_notice_30d",
      "deadline_basis": "근로기준법 제26조", "deadline": null, "dday": null, "timeline_group": "notice" }
  ],
  "items": [
    { "id": "i-l01", "code": "L-01", "name": "사직 합의서 서면 확인", "kind": "internal",
      "status": "approved", "blocking": false,
      "detail": { "deadline_rule": "none", "deadline_basis": null, "dday": null, "timeline_group": null },
      "three_state": "충족", "badges": [ ... ] },
    { "id": "i-l04", "code": "L-04", "name": "금품청산 (14일)", "kind": "statutory",
      "status": "submitted", "blocking": true,
      "detail": { "deadline_rule": "settlement_14d", "deadline_basis": "근로기준법 제36조", "dday": 3, "timeline_group": "settlement" },
      "three_state": "미충족", "three_state_sub": "상신검토필요", "badges": [ ... ] },
    { "id": "i-l09", "code": "L-09", "name": "해고예고 (30일)", "kind": "statutory",
      "status": "not_applicable", "blocking": true,
      "detail": { "deadline_rule": "dismissal_notice_30d", "deadline_basis": "근로기준법 제26조", "dday": null, "timeline_group": "notice" },
      "three_state": "해당없음", "badges": [ ... ] }
  ],
  "compare": [ /* CompareResult (LB-04, §2) */ ],
  "badges": [
    { "tier": "L1", "title": "근로기준법 제36조", "url": "https://law.go.kr/...", "version": "v2025.10" },
    { "tier": "L1", "title": "근로기준법 제27조", "url": "https://law.go.kr/...", "version": "v2025.10" },
    { "tier": "L2", "title": "중앙노동위원회 주요 판정례", "url": "https://www.nlrc.go.kr", "version": "v2026.05" },
    { "tier": "L3", "title": "고용노동부 해고·금품청산 안내", "url": "https://www.moel.go.kr", "version": "v2026" }
  ]
}
```

- `item_summary` = LB-03 명시적 count(data-model §3-2). **서버가 count로 계산**(set 아님) — 불변식 `met+unmet+na == total`.
- `timeline` = LB-01 결정론적 기한 배치(data-model §2-2). `deadline`은 `settlement_14d`만 실측 계산(`exit_date+14`), `separation_cert`·`insurance_loss`는 **`null`(`[시드확인필요]`)**, `dismissal_notice_30d`는 권고사직 시 `null`(항목 status=`not_applicable`).
- `dday` = LB-02 파생(`deadline − reference_date` = **잔여일**; 양수=남음→`D-dday`, 음수=경과→`D+|dday|`). 예시 `3`은 D-3 임박(금품청산 지급기한 3일 남음 · reference_date 기준 · 시드로 조정되는 값). PRODUCT §6 "D-3 근접" 정합.
- `items[].three_state` = LB-03 3-상태(data-model §3-1). `submitted`는 `three_state_sub`로 "상신검토필요" 세분.
- `completion` = 코어 `Gate.rail_completion["labor"]`(§5 파생, 40%). **레일에서 재계산 금지 — 코어 게이트 재사용.**
- `items` = 코어 `Item`(rail=labor) + LB `detail`. 상태·배지는 코어 규약.
- 404 `NOT_FOUND`(케이스 없음).

> **LB-01 타임라인** = `timeline[]`, **LB-02 D-day** = `timeline[].dday`·`items[].detail.dday`, **LB-03 상태 대조** = `item_summary` + `items[].three_state`. 별도 엔드포인트 불요(이 응답에 포함).

---

## 2. 판정례 대조 — 코어 `POST /compare` 재사용 (LB-04) `[both]`

**신설 없음.** 코어 §2-3 `POST /compare`를 `rail="labor"`로 호출.

**요청** (`CompareInput`, 코어 §6-1):
```json
{ "rail": "labor", "subject": "LB-04:written_notice",
  "case_facts": { "reason_text": "업무 성과 부진으로 권고사직 처리, 대상자에게 문자로 통보함",
                  "exit_reason": "recommended_resignation",
                  "exit_date": "2026-07-19", "job": "개발", "rank": "시니어 책임" },
  "item_context": { "code": "L-09", "name": "해고예고 (30일)",
                    "standard_refs": ["std-근기법27", "std-중노위판정례"] } }
```

**응답 200 `data`** (`CompareResult`, 코어 §6-2 · LB 규칙 data-model §5):
```json
{
  "rail": "labor", "subject": "LB-04:written_notice",
  "rows": [
    { "kind": "procedure", "text": "회사사유 텍스트에서 구두·문자 통보 정황 신호가 확인됩니다." },
    { "kind": "standard",  "text": "근로기준법 제27조 — 해고 시 해고사유와 시기를 서면으로 통지해야 합니다." },
    { "kind": "risk",      "text": "구두·약식으로 통보하고 서면통지가 누락된 경우, 공개 판정례에서 부당해고로 판정된 사례가 있습니다. (중앙노동위 판정례: 휴대폰 문자로 통보→서면통지 의무 위반)" },
    { "kind": "status",    "text": "노무 검사 항목 6건 중 미충족 3건 · 금품청산(제36조) 지급기한 D-3" },
    { "kind": "source",    "text": "근로기준법 제27조 · 중앙노동위원회 주요 판정례", "url": "https://law.go.kr/..." }
  ],
  "unmet_count": 3,
  "badges": [ { "tier": "L1", ... }, { "tier": "L2", ... }, { "tier": "L3", ... } ],
  "boundary_notice": "본 결과는 위법 여부를 판정하지 않습니다. 공개된 법령·판례 기준과 회사 입력 상태의 대조 결과·기한만 제공하며, 구체 사건의 판단은 전문가의 몫입니다.",
  "expert_referral": true
}
```

- `procedure` 행 = `reason_text` 구두/문자 통보 신호 추출(data-model §5-2). `risk` 행 = **사례 프레이밍 고정**(단정 금지, 순번 51·388 인용).
- **§36 금품청산 판정례 risk 행 없음**(코퍼스 0건 — data-model §4-2). §36은 `status` 행 D-day로만.
- **사건번호 미표기**: 인용 판정례(순번 51·388)에 정식 `case_no`가 없으므로 사건번호를 서술에 넣지 않음(창작 금지).
- `unmet_count` = LB-03 `item_summary.unmet_count`(=3)와 일치.
- `boundary_notice` = 코어 고정 문구 그대로. `expert_referral: true`(코어 §1-7) 판단 분기 노출.
- 422 `COMPARE_FAILED`.

---

## 3. 보완 처리·기한 증적 — 코어 엔드포인트 재사용 (신설 없음)

| LB 동작 | 사용 엔드포인트(코어) |
|---|---|
| 금품청산·이직확인서 등 항목 상신 (LB-06) | `POST /items/{id}/submit` (`memo`·`attachments`·`signed`) |
| 항목 확인/반려 | `POST /items/{id}/review` `[admin]` |
| 항목 상세 드로어(근거·확인요건) | `GET /items/{id}` |
| 게이트 집계(레일 완료율·risk) | `GET /cases/{id}/gate` |
| 정산 증적 봉인 (LB-06, 14일 충족 근거) | `POST /cases/{id}/evidence` |
| 근거 기준 조회 (LB-08) | `GET /standards?rail=labor` |
| 인테이크 대조(접수 직후) | `POST /cases/{id}/intake-compare` → `POST /compare` |

> LB-06(정산 증적) = L-04 항목 코어 상신-검토(`Approval`) → 확인 시 코어 증적 봉인(`Evidence`). 별도 mutation 없음. L-04가 `approved`되면 코어 게이트가 완료율·risk를 재파생.

---

## 4. LB 근거 코퍼스 조회 — `LaborPrecedent` (선택 · 내부 조회) `[both]`

LB-04 compare가 내부적으로 `LaborPrecedent`(data-model §4)를 조회한다. 외부 노출은 선택(디버그/근거 열람용). MVP 세로절단 구동에 load-bearing 아님 — compare 응답 `risk`·`source`로 충분.

#### `GET /rails/labor/precedents` — 판정례 코퍼스 조회 (선택) `[both]`
`?element=written_notice&category=disciplinary_dismissal&q=&page=&size=`
응답: `data`=[`LaborPrecedent`(seq·category·title·decided_on·case_no·matched_elements·is_seed)], `meta.pagination`.
- `case_no`는 약 27%만 존재(나머지 null — data-model §4-2). 필터 `element`로 요구 요소별 조회.

---

## 5. CP 커버 확인

| CP | 커버 |
|---|---|
| LB-01 법정 기한 타임라인 | `GET …/rails/labor` → `timeline[]`(deadline·deadline_basis·timeline_group) |
| LB-02 D-day 관제·알림 | 동 응답 `timeline[].dday`·`items[].detail.dday` |
| LB-03 검사 항목 상태 대조 | 동 응답 `item_summary` + `items[].three_state` |
| LB-04 판정례 대조 알림 | `POST /compare`(rail=labor) → `CompareResult` |
| LB-08 기준 대조 근거 카드 | 모든 응답 `badges`(L1/L2/L3) + `boundary_notice` + `GET /standards?rail=labor` |
| LB-05 리스크+전문가 (얇음) | compare `status`/`risk` + `expert_referral`(코어 §1-7) |
| LB-06 정산 증적 (얇음) | 코어 `POST /items/{id}/submit`·`/review` + `POST /cases/{id}/evidence` |

---

*본 문서는 Phase 1 레일 엔드포인트다. 코어 규약·엔드포인트는 읽기 전용 재사용. 코어 변경 필요 시 도비 요청.*
