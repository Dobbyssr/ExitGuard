# ExitGuard — 보안(SEC) 레일 데이터 모델 (Phase 1 · 레일 보강)

> **문서 성격** — 코어(`../data-model.md`)를 import만 하고 보안 레일 고유 데이터(회수 체크리스트·이상반출 로그)만 보강한다. **대부분 시뮬데이터 → 가볍게.**
> **뼈대 재정의 금지** — `Case`·`Item`·`Approval`·`Evidence`·`Standard`·`Gate`·enum·상태머신은 코어 그대로.
> **근거 SSOT** — 데모: 회수 항목 6건 + 이상반출 1건(4.2GB) + 진행률 88%(계정 2/3·SaaS 1/2·기기 2/2). 창작 금지.
> **레일 코드** — `security` (접두어 SEC · 항목코드 `C-`).
> **작성**: 헤르미온느 · **작성일**: 2026-07-16

---

## 1. 레일 확장 지점

| 코어 예약 지점 | SEC가 채우는 내용 | 위치 |
|---|---|---|
| `Item.detail`(rail=security) | 회수 대상 분류·방식(시뮬) | §2 |
| 별도 레일 테이블(시뮬) | 이상반출 로그 1건 | §3 (신설) |
| `Standard`(rail=security) | 정보통신망법 §28(근거 배지용) | §4 |

> **경계(SEC-04)**: 보안 레일은 **"확인 기록"이지 회수 실행이 아니다.** 계정·SaaS 실제 회수 실행·실연동은 Post-MVP `[시뮬데이터]`. 본 레일은 체크리스트 상신-검토 기록만.

---

## 2. `Item.detail` — 회수 체크리스트 항목 (rail=security · 시뮬)

회수 항목 = 코어 `Item`(code `C-`). 상신-검토는 코어 `Approval` 재사용(대상자 회수 상신 → 관리자 확인).

```
Item.detail (rail=security) {
  recovery_category: enum { account | saas | device }   # 계정 / 외부 SaaS / 기기
  recovery_method:   enum { manual_check | integration_auto | return_signature | log_compare } | null
  is_sim: true        # 회수 원천·실행은 시뮬(오피스키퍼·HR 연동 stub)
}
```

**데모 정합 회수 항목 6건**:
| code | name | recovery_category | status(데모) |
|---|---|---|---|
| `C-11` | 이메일 계정 (Google Workspace) | `account` | `approved`(회수 완료) |
| `C-12` | VPN 접근 | `account` | `approved` |
| `C-01` | GitHub 조직 권한 | `account` | `submitted`→`approved` |
| `C-21` | Slack | `saas` | `approved` |
| `C-02` | Figma · Notion | `saas` | `submitted`→`approved` |
| `C-31` | 노트북 · 보안키 반납 | `device` | `approved` |

- **회수 진행률(데모, SEC-03 참고)**: 계정 **2/3** · SaaS **1/2** · 기기 **2/2** → **88%**(노트북·보안키 = 기기 2건). 코어 `Gate.rail_completion["security"]`(§5 파생)으로 표현 — 레일 재계산 금지. 데모 게이트 시드 `security 88%`(유비쿼터스 §10).
- **kind**: 데모 회수 항목은 내규(`internal`, `blocking=false`) 위주.

---

## 3. `AnomalyExportLog` — 이상반출 이력 (신설 · 시뮬 · SEC-02) ★

퇴사 통보 후 이상 대용량 반출 감지 로그. **오피스키퍼/DLP 로그 시뮬**(고정 시드). `Case` 1 : N.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `id` | int/uuid | ● | PK |
| `case_id` | FK→Case | ● | 소속 케이스(코어 FK 규약) |
| `detected_at` | datetime | ● | 감지 일시(퇴사 통보 후 30일 내) |
| `size_bytes` | int | ● | 반출 용량 — 데모 **4.2GB** |
| `size_label` | str | ● | 표시값 — `"4.2GB"` |
| `window_days` | int | ● | 감지 기간 — `30`(최근 30일) |
| `description` | str | ● | 예: "대용량 다운로드 1건" |
| `is_sim` | bool | ● | 항상 `true`(DLP 로그 시뮬) |

- **데모값 고정**: 퇴사 통보 후 최근 **30일** 내 대용량 다운로드 **1건 (4.2GB)** 감지(데모 line 2181 verbatim).
- 상태머신·상신-검토 대상 아님(조회 전용 시뮬 로그).

---

## 4. 근거 시드 — `Standard` (rail=security)

배지용 최소 시드(SEC는 compare 대조 대상 아님 — 시뮬).

| tier | title | article | source_url | version |
|---|---|---|---|---|
| **L1** | 정보통신망법 제28조 | 접근권한 회수·기술적 보호조치 | https://law.go.kr/... | v2026.07 |

> SEC CP(01·02)는 `[시뮬데이터]`라 판례(L2) 대조 없음. 근거 배지는 L1 최소 1건.

---

## 5. 정합성 규약

- `Case`·`Item`·`Approval`·`Evidence`·`Gate`·`Standard` = 코어 그대로. **재정의 0건.**
- 신설 = `AnomalyExportLog`(시뮬)뿐. 코어 FK(`case_id`) 준수.
- 회수 항목 상신-검토는 코어 `Approval` + 상태머신(§4) 재사용. 증적은 코어 `Evidence`.
- enum `recovery_category`·`recovery_method`는 `Item.detail` 내부 필드(코어 enum 아님, 레일 로컬).

---

*본 문서는 Phase 1 레일 보강이다. 코어 뼈대는 읽기 전용.*
