# ExitGuard — 보안(SEC) 레일 API 명세 (Phase 1 · 레일 엔드포인트)

> **문서 성격** — 코어 `../api-spec.md`가 예약한 `GET /cases/{id}/rails/security` 내부 응답을 채운다. 공통 규약(envelope·에러·배지·직역법)은 코어 재사용. **대부분 시뮬 → 가볍게.**
> **뼈대 재정의 금지** — 회수 상신/검토/게이트/증적은 코어 §2 엔드포인트 재사용. SEC 고유 조회만.
> **⚖️ 경계(SEC-04)** — 이 레일은 **"확인 기록"이지 회수 실행이 아니다.** 응답에 경계 문구 필수.
> **작성**: 헤르미온느 · **작성일**: 2026-07-16

---

## 1. `GET /cases/{id}/rails/security` — 보안 레일 상세 (SEC-01·02) `[both]`

코어 뼈대 응답 `{ rail, completion, items, badges }` + SEC 고유 `anomaly_exports`·`recovery_progress`·`boundary_notice` 확장.

**응답 200 `data`**:
```json
{
  "rail": "security",
  "completion": 88,
  "recovery_progress": {
    "account": { "recovered": 2, "total": 3 },
    "saas":    { "recovered": 1, "total": 2 },
    "device":  { "recovered": 2, "total": 2 },
    "overall_percent": 88
  },
  "items": [
    { "id": "i-c11", "code": "C-11", "name": "이메일 계정 (Google Workspace)", "kind": "internal",
      "status": "approved", "detail": { "recovery_category": "account", "recovery_method": "manual_check", "is_sim": true } },
    { "id": "i-c01", "code": "C-01", "name": "GitHub 조직 권한", "kind": "internal",
      "status": "submitted", "detail": { "recovery_category": "account", "recovery_method": "manual_check", "is_sim": true } }
  ],
  "anomaly_exports": [
    { "id": "ax1", "detected_at": "2026-07-05T09:12:00Z",
      "size_label": "4.2GB", "window_days": 30,
      "description": "대용량 다운로드 1건", "is_sim": true }
  ],
  "badges": [
    { "tier": "L1", "title": "정보통신망법 제28조", "url": "https://law.go.kr/...", "version": "v2026.07" }
  ],
  "boundary_notice": "체크리스트는 회수 실행이 아닌 확인 기록입니다."
}
```

- `items` = 코어 `Item`(rail=security, code C-) + SEC `detail`(data-model §2). 회수 6건.
- `anomaly_exports` = `AnomalyExportLog`(data-model §3, 시뮬). 데모: 퇴사 통보 후 30일 내 4.2GB 1건.
- `recovery_progress` = 데모 진행률(계정 2/3·SaaS 1/2·기기 2/2·88%). `completion` = 코어 `Gate.rail_completion["security"]`(§5 파생) — **레일 재계산 금지**.
- **`boundary_notice` 필수(SEC-04)**: `"체크리스트는 회수 실행이 아닌 확인 기록입니다."`(데모 verbatim). 회수 항목이 확인 기록임을 명세·응답에 강제.
- 404 `NOT_FOUND`.

> **SEC-01(회수 체크리스트)** = `items` + `recovery_progress`. **SEC-02(이상반출 이력)** = `anomaly_exports`. 별도 엔드포인트 불요(이 응답에 포함).

---

## 2. 회수 상신-검토 — 코어 엔드포인트 재사용 (신설 없음)

| SEC 동작 | 사용 엔드포인트(코어) | 경계 |
|---|---|---|
| 회수 항목 상신(대상자 회수 상신) | `POST /items/{id}/submit` `[user]` | 회수 **확인 기록** 상신(실행 아님) |
| 회수 확인/반려(관리자 확인) | `POST /items/{id}/review` `[admin]` | 확인 기록 승인 |
| 회수 항목 상세 | `GET /items/{id}` | |
| 게이트 집계 | `GET /cases/{id}/gate` | `security` 완료율 포함 |
| 증적 봉인 | `POST /cases/{id}/evidence` | 회수 확인 사실 봉인 |

- 상태전이는 코어 §4 상태머신 그대로: `pending→submitted→approved`(회수 확인 완료) / `rejected`(재상신).
- **경계 강제**: 상신 memo·응답 어디에도 "계정을 회수했다(실행)" 단정 금지. "회수 확인/반납 확인" = 기록. 실제 계정 폐쇄·SaaS 탈퇴 실행은 `[시뮬데이터]`(SEC-05, Post-MVP).

---

## 3. CP 커버 확인

| CP | 커버 |
|---|---|
| SEC-01 계정·SaaS·기기 회수 체크리스트 | `GET …/rails/security` → `items`·`recovery_progress` + 코어 `submit`/`review`(상신→확인) |
| SEC-02 이상반출 이력 | 동 응답 `anomaly_exports`(4.2GB 시뮬) |
| (SEC-04 경계) | 응답 `boundary_notice` 필수 |

---

*본 문서는 Phase 1 레일 엔드포인트다. 코어 규약은 읽기 전용 재사용.*
