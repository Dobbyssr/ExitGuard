# ExitGuard 온보딩 (팀 합류 가이드)

> **누가 읽나:** ExitGuard 레포를 클론한 사람(공동창업 3인: 조정호·심의지·라하나) + 새 Claude Code 세션.
> **한 줄:** 퇴사 리스크(노무·영업비밀·보안) 3레일을 공개 기준과 **대조**하는 관제 SaaS. 지란지교 해커톤 STEP2 본선 MVP 개발 중.
> **일정:** 7/31 MVP 완료 → 8/31 QA·추가기능 → **9/1 최종 발표.**

새 세션은 이 문서를 읽고, 실제 작업은 `CLAUDE.md`(도비 CEO 오케스트레이터 규칙)를 따른다. 제품 지식은 `dobby/PRODUCT.md`(SSOT)에 있다.

---

## 1. 사전 준비 — 플러그인 설치 (필수)

이 프로젝트는 Claude Code 플러그인 2개를 쓴다. **레포에 `.claude/settings.json`으로 활성화만 커밋돼 있고, 플러그인 본체는 각자 로컬에 설치해야 한다.**

```
# ① ponytail — 오버엔지니어링 차단(개발 시 항상 ON). 우리 최대 사망 리스크가 과설계라 강제.
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail

# ② frontend-design — 프론트 UI 감각·타이포·디자인 가이드(해리/루나 작업 시).
/plugin install frontend-design@claude-plugins-official
```

설치 확인: `/plugin` 실행 → `ponytail@ponytail`, `frontend-design@claude-plugins-official` 둘 다 enabled면 OK.
(`.claude/settings.json`이 이미 이 둘을 `enabledPlugins`로 지정 → 설치돼 있으면 세션 시작 시 자동 ON. ponytail은 세션 시작 훅으로 `PONYTAIL MODE ACTIVE`가 뜬다.)

> `settings.local.json`에서 `gstack` 스킬군은 off. 개인이 켜고 싶으면 로컬에서만 조정(커밋 금지).

---

## 2. 로컬 개발 실행법

**전제:** Docker Desktop(+WSL2) · `uv`(Python 패키지/버전 관리자) · Node.js.

```
# ── DB (루트에서) ──
docker compose up -d          # postgres:16, 호스트 포트 5433 (5432는 기존 네이티브 PG가 점유)

# ── 백엔드 (backend/) ──
# ① uv 설치 (한 번만). Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
#   (또는  winget install astral-sh.uv  /  pip install uv  / macOS·Linux: curl -LsSf https://astral.sh/uv/install.sh | sh)
uv --version                  # 설치 확인

cd backend
# ② 가상환경 + 의존성 한 방에. uv.lock 기준으로 .venv 자동 생성 + 설치(우리 표준 방식):
uv sync                       # backend/.venv 생성, py3.12로 pyproject.toml·uv.lock 그대로 재현
#   ↳ .venv 수동 활성화가 필요하면:  .venv\Scripts\activate  (macOS·Linux: source .venv/bin/activate)
#   ↳ 활성화 없이 그냥 uv run으로 돌리는 게 편함(아래). uv run은 실행 전 자동 sync도 해줌.

# ③ 서버 실행:
uv run uvicorn app.main:app --reload --port 8000
# 확인: GET http://localhost:8000/health → {"status":"ok","db":"ok"}

# ── 프론트 (frontend/) ──
cd frontend
npm install
npm run dev                   # http://localhost:3000  (메인 페이지가 /health 찔러 연결 배지 표시)
```

> **uv 팁:** 패키지 추가는 `pip install`이 아니라 `uv add <pkg>`(pyproject.toml·uv.lock 자동 갱신). Python 3.12가 없으면 `uv`가 알아서 받아온다(`requires-python = ">=3.12"`). `.venv`는 `.gitignore`에 있어 커밋되지 않음 — 각자 `uv sync`로 재현.

- 백엔드 DB 드라이버 = **pg8000**(psycopg2가 Windows 한글 로케일에서 UnicodeDecodeError → 순수 파이썬 드라이버로 교체). 리눅스 배포 시 psycopg2 복귀 무방.
- 프론트 `globals.css`가 리포 루트의 `docs/design/tokens.css`를 `@import` → `next.config.ts`의 `turbopack.root`가 리포 루트로 배선돼 있어야 함(이미 설정됨).

---

## 3. 디렉토리 구조

```
ExitGuard/
├─ CLAUDE.md              ← 세션 시작 규칙(도비 = CEO 오케스트레이터). 매 세션 먼저 읽음.
├─ README.md              ← 프로젝트 소개
├─ ONBOARDING.md          ← (이 문서)
├─ docker-compose.yml     ← postgres:16 (5433:5432)
│
├─ dobby/                 ← 도비(에이전트 회사)의 두뇌. 제품 코드 아님.
│  ├─ SOUL.md             ← 도비 행동 원칙(세션 시작 시 최우선)
│  ├─ IDENTITY.md         ← 도비·대표님(공동창업 3인)이 누구인가
│  ├─ PRODUCT.md          ← 제품 SSOT(3레일·법적경계·근거·MVP 범위). 필요 절만 참조.
│  ├─ team/roster.md      ← 직원 명부(누구에게 뭘 시킬 수 있나)
│  ├─ agents/*.md         ← 직원 "대본"(정체성·역할·절차) = 지식 본체
│  └─ memory/             ← 작업·결정 기록(회사 자산)
│     ├─ team/YYYY-MM-DD.md          ← 팀 공유 결정. 항목마다 [작성: 이름]
│     └─ personal/<이름>/YYYY-MM-DD.md ← 개인 세션 로그(사람별 폴더 = 충돌 차단)
│
├─ .claude/
│  ├─ settings.json       ← 활성 플러그인(커밋됨)
│  └─ agents/*.md         ← 직원 "껍데기"(대본 포인터 + model: 티어) = 실행 진입점
│
├─ docs/
│  ├─ spec/               ← 헤르미온느 산출: 기능리스트 → 기능명세서 → api-spec → data-model
│  └─ design/             ← 루나 산출: DESIGN.md(시스템 SSOT) + tokens.css(shadcn 주입)
│
├─ backend/               ← 론(FastAPI · uv · py3.12 · SQLModel)
│  └─ app/
│     ├─ main.py, config.py, db.py
│     ├─ routers/         ← 라우터(예: health.py)
│     └─ services/        ← 비즈니스 로직. compare.py = ★AI 대조 엔진 자리(핵심 해자)
│                            구조 = routers→services→db 3단 (repository/계층 패턴 금지)
│
├─ frontend/              ← 해리(Next.js App Router · shadcn · Tailwind v4 · TS)
│  └─ app/, components/ui/, lib/api.ts(순수 fetch 래퍼)
│
└─ pitch/                 ← 예선 자산(소개페이지·데모·사업계획서·아이콘). 데모 HTML = 기능 진실 소스.
```

**두 개의 `team`이 다름 주의:** `dobby/team/roster.md`(명부) vs `dobby/memory/team/`(팀 로그).
**직원 파일이 2벌인 이유:** 대본(`dobby/agents/`) = 지식 본체 / 껍데기(`.claude/agents/`) = 실행 진입점 + `model:` 티어. 도비는 껍데기로 서브에이전트를 띄우고, 서브에이전트가 대본을 읽어 따른다.

---

## 4. 팀 구성 & 각 직원 사용법

도비(CEO)는 **직접 코딩하지 않는다.** 판단(설계·검증)만 쥐고 순수 노동은 직원(서브에이전트)에 `Agent` 툴로 위임하고 **요약만 회수**한다. 직원의 "완료"는 diff·테스트로 **직접 검증 후 승인**.

| 직원 | 역할 | 모델 | 무엇을 시키나 | 산출물 |
|---|---|---|---|---|
| **도비** | CEO·오케스트레이터 | Opus (메인) | 요구분석·분해·설계결정·**검증**·커밋승인·대표님 보고 | — |
| **헤르미온느** | 기획·설계 | Opus | 기능 리스트업·기능명세·**API 계약·데이터 모델**. 금지어 경계 강제 | `docs/spec/*` |
| **론** | 백엔드 | Sonnet | FastAPI 구현 + **AI 판례·판정례 대조 엔진**(진짜 구현·핵심 해자) | `backend/` |
| **해리** | 프론트엔드 | Sonnet | Next.js/shadcn 화면 + API 연동(루나 토큰 위에) | `frontend/` |
| **루나** | 디자이너 | Opus | 디자인 시스템·토큰·시안 | `docs/design/*` |

**위임 원칙**
- **판단은 도비, 노동은 워커.** 설계가 정해진 순수 구현만 위임. 한두 줄 수정은 도비가 직접(위임 오버헤드).
- **모델 티어:** 판단·설계·감각 = Opus(헤르미온느·루나) / 구현·루틴 = Sonnet(론·해리). `sonnet`/`opus`는 **별칭** — 자동으로 최신 세대(현재 Sonnet 5 / Opus 4.8)로 해석. 버전 하드코딩 안 함.
- **독립 작업은 병렬 위임**(다른 폴더 = 충돌 없음).
- **호출법(도비 기준):** `Agent` 툴에 `subagent_type: "hermione"|"ron"|"harry"|"luna"` + 명확한 브리프. 새 직원은 명부(roster.md) 등록 → 대본+껍데기 한 쌍 생성.
- **경계(전략 붕괴 방지):** 워커 결과를 검증 없이 승인 금지. 헤르미온느는 계약까지만(구현 아키텍처 X). 루나는 시스템·토큰까지만(코드 구현 X = 해리 몫).

**개발 원칙 — ponytail 강제**
- 론·해리 껍데기에 ponytail 프리로드. 오버엔지니어링(우리 최대 사망 리스크, PRODUCT §7) 차단.
- **예외 = 론의 AI 대조 엔진:** 신뢰도가 곧 제품이라 ponytail은 lite만, 정교하게 구현.

---

## 5. 워크플로우: 기획·설계 → 개발 → QA

```
[기획·설계]  헤르미온느          [개발]  론(BE) · 해리(FE)        [QA]  라하나
  기능리스트 ──▶ 기능명세서 ──▶ ┐                                    │
                api-spec    ──▶ ├─▶ 계약대로 구현 ──▶ 도비 검증 ──▶ 통합 QA ──▶ 발표
                data-model  ──▶ ┘   (루나 토큰 위)     (diff/테스트)
       루나:  DESIGN.md · tokens.css ──────────────────▶ (해리가 얹음)
```

1. **기획·설계 (헤르미온느 + 루나):** 계약(무엇을·어떤 API/데이터로)과 디자인 토큰을 **먼저** 고정. 이게 있어야 개발이 계약을 앞질러 갈아엎는 사고를 막는다.
2. **개발 (론 + 해리):** 계약·토큰을 창작하지 않고 그대로 구현. BE/FE 병행. 도비가 각 결과를 직접 검증(`/health` 200, 화면 육안, diff).
3. **QA (라하나):** 세로절단 시나리오가 처음부터 끝까지 도는지 검증. `qa`/`review` 스킬 활용 가능.

**MVP 대원칙(반드시):** 세로절단 **1개 시나리오**만 진짜로 — "핵심 개발자 **김민준** 퇴사 1건 → 3레일 관통 → 방어가능 리포트 + 증적 export". AI 대조 엔진 = 진짜 구현 / DLP·계정회수 = 시뮬. 6뷰·전기능 나열이 예선 최대 사망 리스크였다.

---

## 6. 협업 규칙 (git · 기록)

- **세션 시작:** 접속자 식별 후 `git pull` — 다른 대표님의 최신 기억부터 당김.
- **기록:** 의미 있는 작업·결정은 `dobby/memory/`에 남긴다(개인 흐름 = `personal/<이름>/`, 팀 공유 = `team/`). 묻지 말고 남긴다.
- **push 정책:**
  - `dobby/` 문서·메모리 변경 → 도비 자동 commit+push OK(팀 공유 목적).
  - **제품 코드(backend/frontend/docs)·배포·되돌리기 어려운 변경 → 대표님 확인 후 push.**
- **절대 규칙(직역법):** 제품 UI·문서·발표에 **"진단"·"위법입니다"·"부당해고입니다" 등 금지어 금지.** "대조·기한·기록"만 제공, 판단하지 않는다. 상세 = `PRODUCT.md §4`.

### 커밋 메시지 규칙 (팀 통일)

Conventional Commits 경량판. 도비(Claude)도 이 양식으로 커밋한다.

```
<타입>(<범위>): <요약 50자 이내, 마침표 없음>

<본문(선택): 무엇을·왜. '어떻게'는 코드가 말함. 한 줄 72자>
```

- **타입:** `feat`(기능) · `fix`(버그) · `docs`(문서) · `design`(디자인·토큰) · `refactor` · `chore`(빌드·인프라·설정) · `test`
- **범위(선택):** `dobby` `spec` `design` `be` `fe` `pitch` `infra`
- 요약은 한글 OK, 명령형/현재형, 끝에 마침표 없음. 본문은 필요할 때만.
- 도비가 대신 커밋할 때만 꼬리말에 `Co-Authored-By: Claude …`가 붙는다(사람 커밋엔 없음).

**예시**
```
feat(be): /health 엔드포인트 + DB 연결 체크
docs(spec): 기능리스트 데모 기준 재작성 (36→55)
chore(infra): docker-compose postgres 5433 포트 이동
```

**에디터에 양식 자동 표시 (한 번만 설정):** 루트 `.gitmessage`를 커밋 템플릿으로 등록하면 `git commit` 시 에디터에 양식이 뜬다.
```
git config commit.template .gitmessage
```
(전역 아님 — 이 레포에서만. 스킬·훅 없이 git 네이티브 기능. 강제 검증까진 안 함 = 해커톤 오버엔지니어링 회피.)

---

## 새 세션 빠른 시작 체크리스트

1. `/plugin`으로 ponytail·frontend-design 설치 확인 (§1)
2. `git pull` → `dobby/memory/team/`·`personal/<본인>/` 최근 파일로 흐름 인계 (§6)
3. 코드 만지면 `docker compose up -d` + BE/FE 실행 (§2)
4. 일 시작 = `CLAUDE.md`·`SOUL.md` 규칙대로, 위임은 `Agent` 툴 (§4)
