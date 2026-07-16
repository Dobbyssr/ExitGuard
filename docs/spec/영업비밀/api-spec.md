# ExitGuard — 영업비밀(TS) 레일 API 명세 (Phase 1 · 레일 엔드포인트)

> **문서 성격** — 코어 `../api-spec.md`가 **예약**한 `GET /cases/{id}/rails/trade_secret`의 내부 응답을 채운다. 공통 규약(envelope·에러·배지·직역법 §1-6/§1-7)은 코어 그대로 재사용.
> **뼈대 재정의 금지** — 상신/검토/게이트/증적/근거조회/compare는 **코어 §2 엔드포인트 재사용**(TS 전용 신설 없음). TS 고유 데이터 조회만 신설.
> **필드·타입** — `./data-model.md`(TS 레일) + `../data-model.md`(코어) 참조. 여기선 shape만.
> **작성**: 헤르미온느 · **작성일**: 2026-07-16

---

## 1. `GET /cases/{id}/rails/trade_secret` — 영업비밀 레일 상세 (TS-01·02) `[both]`

코어 뼈대 응답 `{ rail, completion, items, compare, badges }` + TS 고유 `assets`·`asset_summary` 확장.

**응답 200 `data`**:
```json
{
  "rail": "trade_secret",
  "completion": 40,
  "asset_summary": {
    "asset_count": 13,
    "protection_unmet": 4,
    "re_pledge_pending": 7
  },
  "assets": [
    {
      "id": "a1", "name": "핵심도면_v7", "category": "design",
      "secret_mark": false, "re_pledge": false, "access_control": true,
      "protection_status": "unmet",
      "source": "권한대장·접근로그", "is_sim": true
    },
    { "id": "a2", "name": "고객DB_스키마", "category": "data",
      "secret_mark": true, "re_pledge": false, "access_control": true,
      "protection_status": "re_pledge_needed", "source": "권한대장·접근로그", "is_sim": true }
  ],
  "items": [
    { "id": "i-s02", "code": "S-02", "name": "퇴직 비밀유지 재서약", "kind": "internal",
      "status": "submitted", "detail": { "requirement_focus": "re_pledge", "related_asset_ids": ["a2"] },
      "badges": [ ... ] }
  ],
  "compare": [ /* CompareResult (TS-05, §3) */ ],
  "badges": [
    { "tier": "L1", "title": "부정경쟁방지법 제2조", "url": "https://law.go.kr/...", "version": "v2026.06" },
    { "tier": "L2", "title": "영업비밀 비밀관리성 판단 기준", "url": "...", "version": "v2026.06" },
    { "tier": "L3", "title": "특허청 영업비밀 관리 매뉴얼", "url": "...", "version": "v2026.06" }
  ]
}
```

- `assets` = `TradeSecretAsset`(data-model §2). `protection_status`는 서버가 §2-3 결정론적 파생식으로 계산해 응답(저장 아님).
- `asset_summary` = data-model §2-4 KPI(13/4/7 — 데모값). TS-01(자동 특정) 산출.
- `completion` = 코어 `Gate.rail_completion["trade_secret"]`(§5 파생, 데모 40%). **레일에서 재계산 금지 — 코어 게이트 재사용.**
- `items` = 코어 `Item`(rail=trade_secret) + TS `detail`. 상태·배지는 코어 규약.
- 404 `NOT_FOUND`(케이스 없음).

> **TS-02(3요소 대조)** = `assets[].{secret_mark,re_pledge,access_control,protection_status}` 테이블. 별도 엔드포인트 불요(이 응답에 포함).

---

## 2. 비밀관리성 대조 — 코어 `POST /compare` 재사용 (TS-05) `[both]`

**신설 없음.** 코어 §2-3 `POST /compare`를 `rail="trade_secret"`으로 호출.

**요청** (`CompareInput`, 코어 §6-1):
```json
{ "rail": "trade_secret", "subject": "TS-05:secret_management",
  "case_facts": { "reason_text": "...", "exit_reason": "recommended_resignation",
                  "exit_date": "2026-07-19", "job": "개발", "rank": "시니어 책임" },
  "item_context": { "code": "S-01", "name": "비밀표시 점검",
                    "standard_refs": ["std-부경법2", "std-비밀관리성판례"] } }
```

**응답 200 `data`** (`CompareResult`, 코어 §6-2 · TS 규칙 data-model §4):
```json
{
  "rail": "trade_secret", "subject": "TS-05:secret_management",
  "rows": [
    { "kind": "procedure", "text": "비밀표시 없는 자산 N건 · 전원 접근 자산 M건이 확인됩니다." },
    { "kind": "standard",  "text": "부정경쟁방지법 §2 — 영업비밀은 '비밀로 관리된' 정보여야 보호대상입니다." },
    { "kind": "risk",      "text": "비밀표시가 없고 접근이 제한되지 않은 자료에 대해, 공개 판례에서 비밀관리성이 인정되지 않아 영업비밀로 보호받지 못한 것으로 판단된 사례가 있습니다." },
    { "kind": "status",    "text": "접근 자산 13건 중 보호요건 미충족 4건 · 재서약 미체결 7건" },
    { "kind": "source",    "text": "부정경쟁방지법 제2조 · 특허청 영업비밀 관리 매뉴얼", "url": "https://law.go.kr/..." }
  ],
  "unmet_count": 4,
  "badges": [ { "tier": "L1", ... }, { "tier": "L2", ... }, { "tier": "L3", ... } ],
  "boundary_notice": "본 결과는 위법 여부를 판정하지 않습니다. 공개된 법령·판례 기준과 회사 입력 상태의 대조 결과·기한만 제공하며, 구체 사건의 판단은 전문가의 몫입니다."
}
```

- `risk` 행 = **사례 프레이밍 고정**(단정 금지). `boundary_notice` = 코어 고정 문구 그대로.
- 판단 분기 노출 시 응답에 `expert_referral: true`(코어 §1-7) 가능.
- 422 `COMPARE_FAILED`.

---

## 3. 보완 처리 — 코어 엔드포인트 재사용 (신설 없음)

| TS 동작 | 사용 엔드포인트(코어) |
|---|---|
| 재서약(S-02) 상신 | `POST /items/{id}/submit` (`signed:true` 전자서명) |
| 재서약 확인/반려 | `POST /items/{id}/review` `[admin]` |
| 반출자료 회수(S-07) 상신·확인 | `POST /items/{id}/submit` · `/review` |
| 항목 상세 드로어 | `GET /items/{id}` |
| 게이트 집계 | `GET /cases/{id}/gate` |
| 증적 봉인 | `POST /cases/{id}/evidence` |
| 근거 기준 조회 | `GET /standards?rail=trade_secret` |

> S-02 재서약 `approved` 처리 시 서버는 연계 자산의 `re_pledge=true` 갱신 → `protection_status` 재파생(data-model §3). 별도 mutation 엔드포인트 신설 없음 — 코어 review 처리의 부수효과.

---

## 4. CP 커버 확인

| CP | 커버 |
|---|---|
| TS-01 접근 자산 자동 특정 | `GET …/rails/trade_secret` → `assets`·`asset_summary` |
| TS-02 보호요건 3요소 대조 | 동 응답 `assets[].3요소·protection_status` |
| TS-05 비밀관리성 대조 | `POST /compare`(rail=trade_secret) → `CompareResult` |

---

*본 문서는 Phase 1 레일 엔드포인트다. 코어 규약·엔드포인트는 읽기 전용 재사용. 코어 변경 필요 시 도비 요청.*
