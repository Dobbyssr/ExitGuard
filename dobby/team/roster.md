# 직원 명부 (Team Roster)

> ExitGuard 팀의 인력 명부. 직원 이름은 **해리포터 등장인물**로 짓는다.
> 고용 절차: ① 이 표에 등록 → ② 대본 `dobby/agents/<이름>.md` 작성 → ③ 껍데기 `.claude/agents/<이름>.md` 작성(대본 포인터 + `model:` 티어) → ④ `Agent` 툴로 호출.

## 현재 인력

| 이름 | 역할 | 대본 (`dobby/agents/`) | 껍데기 (`.claude/agents/`) | 모델 티어 | 상태 |
|---|---|---|---|---|---|
| **도비 (Dobby)** | CEO · 총괄 오케스트레이터 | — (메인, `CLAUDE.md`) | — | Opus | ✅ 가동 |
| **헤르미온느 (Hermione)** | 기획·설계 (Feature Spec + API Spec + Data Model) | `hermione.md` | `hermione.md` | Opus | ✅ 가동 |
| **론 (Ron)** | 백엔드 (FastAPI/uv/PostgreSQL + AI 대조 엔진) | `ron.md` | `ron.md` | Sonnet | ✅ 가동 |
| **해리 (Harry)** | 프론트엔드 (Next.js/shadcn) | `harry.md` | `harry.md` | Sonnet | ✅ 가동 |
| **루나 (Luna)** | 디자이너 (디자인 시스템·토큰) | `luna.md` | `luna.md` | Opus | ✅ 가동 |

## 고용 예정 (해리포터 이름 — 역할 미확정, 대표님 지정 대기)

> 실제 이름·역할 배정은 대표님이 정한다. 아래는 자리만 잡아둔 것.

| 후보 역할 | 이름(예: Snape / Neville / …) | 모델 티어(안) |
|---|---|---|
| AI/RAG 전담(론에서 분리 시) | _미정_ | Opus |
| QA | _미정_ | Sonnet |

## 모델 티어 원칙

- **Opus** = 판단·설계·타이스트·R&D (기획, AI/RAG 설계 등)
- **Sonnet** = 구현·루틴 (프론트/백 구현, 정해진 스펙의 QA)
- **Haiku** = 순수 기계적 잡무 (해당 시)
- 각 직원 껍데기 `.claude/agents/<이름>.md` frontmatter의 `model:` 로 고정한다. 예외 건은 `Agent` 툴 `model` 파라미터로 그 호출만 덮어쓴다.
