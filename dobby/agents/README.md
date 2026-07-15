# dobby/agents — 직원 대본(지식 본체)

직원 한 명당 대본 파일 하나: `dobby/agents/<이름>.md`.
직원의 **정체성·역할·책임 범위·작업 절차·리포트 포맷**을 여기에 적는다.

- 실제로 서브에이전트로 띄우는 **껍데기**는 `.claude/agents/<이름>.md` (이 대본을 읽어 그대로 따르도록 포인터 + `model:` 티어).
- 도비는 이 대본을 직접 연기하지 않는다 — 반드시 `Agent` 툴로 위임한다.
- 이름은 해리포터 등장인물. 명부는 `dobby/team/roster.md`.

## 고용된 직원

- `hermione.md` — **헤르미온느**, 기획·명세(Feature Spec) 담당 (Opus).
- `ron.md` — **론**, 백엔드 구현 담당 (Sonnet).
- `harry.md` — **해리**, 프론트엔드 구현 담당 (Sonnet).
- `luna.md` — **루나**, 디자인 시스템 담당 (Opus).
- `moody.md` — **무디**, QA 검증 담당 (Sonnet).
