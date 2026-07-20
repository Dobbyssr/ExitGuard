---
name: db-column-comments-rule
description: DB 스키마 모든 컬럼에 코멘트를 단다 — 상시 규칙 (조정호 대표님 지시)
metadata:
  type: feedback
---

조정호 대표님 지시(2026-07-20): **Alembic 스키마의 각 컬럼에 코멘트(`COMMENT ON COLUMN`)를 반드시 단다.** 신규 컬럼도 항상.

**Why:** 스키마가 자기설명적이어야 함 — 계약(data-model 필드 설명)이 DB 자체에 박혀 있어야 유지보수·감수·온보딩에 유리.

**How to apply:**
- SQLAlchemy `mapped_column(..., comment="...")` → Alembic autogenerate가 코멘트 diff까지 잡아 리비전에 반영.
- 코멘트 문구 근거 = `docs/spec/data-model.md` 각 엔티티 필드 "설명". `§17 직역법` 준수 — 판단/진단/조언 함의 문구 금지.
- **상시 규칙으로 `backend/CLAUDE.md §9`에 명문화** (일회성 소급 아님 — 앞으로 만드는 모든 모델 컬럼에 적용).
- 절차: 론 추가 → autogenerate → 드리프트 0 검증 → 스네이프 감수(계약일치·금지어) → 도비 검증·커밋.
- 최초 소급 적용 = [[db-column-comments-rule]] 생성 시점 기준 첫 도메인 2단계(case 세로절단)+스네이프 round3 완료 직후 (task #5).
