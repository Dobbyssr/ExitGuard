# ExitGuard — 디자인 시스템 (DESIGN.md · SSOT)

> **성격**: ExitGuard UI의 단일 진실. 색·타이포·간격·컴포넌트 룩·모션·다크모드를 여기서 확정한다.
> **출발점**: 백지 창작이 아니다. 확정 로고 + `pitch/데모/ExitGuard-나모업로드-단일본.html`(실제 색·레이아웃·다크모드·테마 시스템의 진실 소스)에서 **추출**해 시스템화했다. "Fork & Customize"(PRODUCT §3-3)의 정신 그대로.
> **토큰**: `docs/design/tokens.css` (shadcn/ui 주입용). 이 문서의 값과 1:1.
> **적용 범위**: MVP 세로절단 1개 — *핵심 개발자 김민준 퇴사 1건 → 3레일 관제 → 방어가능 리포트*. 전기능 시안 아님.

---

## ✅ [확정] — primary(주색) = 딥네이비 `#3C4E72`

**2026-07-14 대표님 결재: A안(딥네이비) 확정.** 현행 tokens.css 그대로(변경 0줄). teal은 로고(`Guard`·앱아이콘)·노무 레일색으로만 존재하고, 주요 CTA·포커스 링·사이드바 활성은 딥네이비로 간다 — 레일색과 채도로 분리돼 CTA가 레일 태그와 안 섞이는 게 채택 이유. 아래는 결정 근거 기록(참고용, 재론 금지).

### 사실 확인 (전제 보정)
tokens.css 주석·기존 브리프는 *"데모 기본 프라이머리는 청록이었다"* 고 하나, **현재 데모 파일은 네이비로 출고된다**: `theme:'navy'`(데모 3618행) · `let t='navy'`(3843행) · `localStorage.setItem('eg-theme','navy')`(3844행). 데모를 열면 네이비로 렌더되고, teal은 테마 피커의 5개 프리셋(teal/indigo/sage/clay/navy) 중 하나로만 남아 있다. → **현행 tokens.css(navy) = 데모 실제 출고 상태와 일치.**

단, teal은 **로고 자체에 강하게 박혀 있다**: 워드마크 `Guard`(teal `#0FB2C4`, 800) · 앱아이콘 타일(teal 그라디언트 `#12C1D4`→`#0E97A9`) · 마크 노무 레일. 그래서 primary가 네이비여도 teal은 화면에 존재한다. 이 결정은 "teal을 지우냐"가 아니라 **"주요 CTA·포커스 링을 무슨 색으로 하냐"** 의 문제다.

### 두 안 근거
| | **A. 딥네이비 `#3C4E72` (현행)** | **B. 청록 teal `#0FB2C4`** |
|---|---|---|
| 논리 | 로고 G·`Exit`의 앵커색, 신뢰·관제 톤. 3레일 색과 채도로 분리돼 CTA가 레일 태그와 안 섞임. 변경 0줄. | 이름 강세(`Guard`)·앱아이콘과 primary 일치 → 브랜드 일관성 최고, 더 눈에 띄는 CTA. |
| 리스크 | teal이 로고엔 있는데 UI 주색이 아니라 "브랜드색 두 개"로 읽힐 수 있음. | teal이 **노무 레일색과 동일(`#0FB2C4`)** → 주요 버튼과 "노무 레일" 태그가 같은 색이 되어 레일 정체성이 흐려짐(§2-2 "레일색은 레일에만" 규칙과 충돌). B 채택 시 노무 레일색을 다른 청록(예 `#0E9AA6`)으로 미는 **연쇄 결정**이 붙음. |

### 정확한 시각적 영향 (B로 갈 때 바뀌는 것 — 딱 3줄)
```css
:root {
  --primary: #0FB2C4;          /* 3C4E72 → 주요 CTA·브랜드 버튼 */
  --ring: #0FB2C4;             /* 3C4E72 → 인풋 포커스 링 */
  --sidebar-primary: #0FB2C4;  /* 3C4E72 → 사이드바 활성 항목 */
}
```
- 영향: 채우기 버튼, 인풋 포커스 링, 사이드바 선택 항목, `bg-primary`/`ring`/`text-primary` 유틸리티 전부.
- **다크도 함께 결정**: 현재 다크 `--primary #45577E`. B면 다크도 teal 계열(예 `#12C1D4`)로 맞춰야 라이트/다크 안 어긋남.

> 루나는 결정하지 않는다. A는 변경 0줄+레일 정체성 깨끗, B는 브랜드 일관성 최고+레일 충돌 연쇄. 대표님 취향 결재.

---

## 1. 브랜드 아이덴티티

### 로고 (확정 — 변경 금지)
`pitch/아이콘/exitguard-logo.svg` — 각진 기하학적 **G** 모노그램. 왼쪽에서 3개의 레일(청록/보라/앰버)이 게이트로 수렴하는 형상 = "퇴사 이벤트가 하나의 게이트로 묶인다"는 제품 논리의 시각화.
- G 획: 딥네이비 `#3C4E72`, 균일 stroke 14, 사각 종단(squared terminal). 둥근 G 금지.
- 3레일 rect: 위→아래 청록 `#0FB2C4` / 보라 `#8B5CF6` / 앰버 `#F59E0B`. 이 순서·색은 제품 전체의 레일 정체성과 잠금.
- 최소 여백 = 레일 rect 1개 높이. 청록/보라/앰버 순서를 재배열하거나 색을 바꾸지 않는다.

### 아이덴티티 한 줄
차분하고 관제(管制)스러운 SaaS. 화려함보다 **신뢰·정확·기록**. 잉크는 청록빛이 도는 딥슬레이트, 표면은 냉정한 회백. 감정을 자극하지 않고 상태를 명료하게 보여준다.

---

## 2. 색 팔레트 (정확한 HEX — 데모 원본)

### 2-1. 브랜드 앵커 — 딥네이비
| 역할 | HEX | 용도 |
|---|---|---|
| **Primary** | `#3C4E72` | 로고 G · 주요 CTA · 사이드바 활성 · ring/focus |
| Primary 2 | `#45577E` | hover·다크모드 primary |
| Primary 3 | `#2F3F5D` | pressed·강조 텍스트 |
| Primary 4 | `#26324b` | 최심 |
| soft | `#E4E8F1` | primary 소프트 배경 |
| glow | `rgba(60,78,114,0.36)` | CTA 그림자 발광 |

### 2-2. 3레일 시맨틱 색 (제품의 핵심 — 레일 정체성 전용)
> 이 세 색은 **오직 레일을 식별할 때만** 쓴다. 일반 UI 강조 색으로 전용하지 않는다(전용하면 "이 요소가 노무 레일 액션인가?" 오독 발생).

| 레일 | 색 | HEX (rail / soft / ink) |
|---|---|---|
| 🟦 **노무** (절차·법정기한·분쟁 알림) | 청록 | `#0FB2C4` / `#D6F5F7` / `#0E8A99` |
| 🟪 **영업비밀** (핵심자산 특정·재서약) | 보라 | `#8B5CF6` / `#ECE4F8` / `#7C3AED` |
| 🟧 **보안** (계정·SaaS·자산 회수) | 앰버 | `#F59E0B` / `#FDF1DC` / `#D97706` |

- `rail` = 진한 원색(점·아이콘·프로그레스 바 채움). `soft` = 배지/카드 배경. `ink` = soft 위 텍스트.
- 진행률 바, 레일 탭 도트, 레일 상세 헤더 그라디언트가 이 색을 쓴다.

### 2-3. 중립 스케일 (라이트)
| 토큰 | HEX | 용도 |
|---|---|---|
| canvas / background | `#E4ECEF` | 페이지 바탕 |
| surface / card | `#ffffff` | 카드·패널 |
| panel | `#F7FAFB` | 부 패널 |
| soft | `#F1F5F6` | 칩·부버튼 배경 |
| soft2 | `#F6F8F9` | 더 옅은 표면 |
| line | `#EAEFF1` | 테두리 |
| line2 | `#EDF3F4` | 옅은 구분선 |
| ink | `#14343A` | 본문(청록빛 딥슬레이트) |
| ink2 | `#41616A` | 부 텍스트 |
| muted | `#7C949B` | 캡션 |
| muted2 / muted3 | `#9DB0B5` / `#B4C4C8` | 더 흐린 |

### 2-4. 상태·케이스유형 색
| 의미 | 색 | HEX (fg / soft-bg) |
|---|---|---|
| 해고 · 리스크 알림 | red | `#E11D48` / `#FCE4E7` |
| 권고사직 | amber | `#D97706` / `#FDF1DC` |
| 자발 | purple | `#7C3AED` / `#ECE4F8` |
| 충족·성공 | green | `#22A06B` / `#DCF5E9` |

> ※ 상태 색은 §4 문구 규율과 함께 읽을 것. 빨강은 판단·단정 신호가 아니라 **"리스크 알림 N건 / 법정 기한 D-N"** 의 주의 신호로만 쓴다.

---

## 3. 타이포그래피

- **글꼴**: `Pretendard` (fallback `-apple-system, BlinkMacSystemFont, sans-serif`). 데모 확정. 한글·숫자 가독 최우선.
- **자간**: 큰 제목(≥20px)에 `letter-spacing:-0.5px`. 본문 기본.
- **스무딩**: `-webkit-font-smoothing:antialiased`.

### 타입 스케일 (데모에서 실제 쓰인 값)
| 레벨 | size / weight | 용도 |
|---|---|---|
| Display | 23px / 800 | 뷰 타이틀 ("전문가 연결" 등) |
| Metric | 22px / 800, `-0.5px` | 큰 수치 (방어 가능률 82%) |
| H1 | 18px / 800 | 카드 헤더 |
| H2 | 14.5px / 800 | 섹션 제목 ("법령 근거") |
| Body-strong | 13.5px / 700–800 | 강조 본문·버튼 |
| Body | 13px / 600 | 기본 |
| Label | 12.5px / 600 | 칩·탭 |
| Caption | 11.5px / 600 | 보조 설명 |
| Micro | 10px / 700 | 배지(L1/L2/L3) |

- **weight 규율**: 800(강조·제목·수치) / 700(버튼·배지) / 600(라벨·본문). 400 상시 사용은 피하고 600을 본문 하한으로.

---

## 4. 간격·반경·그림자·레이아웃

### 간격 (4px 그리드 기반, 데모 실측)
주 리듬: `8 · 12 · 14 · 16 · 20 · 24 · 26`px. 카드 내부 패딩 `20px`, 카드 헤더-본문 간 `12–14px`, 카드 간 gap `16–20px`.

### 반경 (radius)
| 토큰 | 값 | 용도 |
|---|---|---|
| card | 20px | 카드·패널·레일 상세 헤더 |
| btn | 12px | 버튼·드롭다운 메뉴·입력 |
| chip | 11px | 칩·아이콘 버튼(38–42px 정사각) |
| badge | 9px | 태그 배지·부버튼 |
| xs | 7px | L1/L2/L3 배지(22×22)·작은 도트 |

### 그림자
| 토큰 | 값 |
|---|---|
| card | `0 10px 30px rgba(30,60,68,0.05)` |
| menu | `0 16px 40px rgba(20,40,45,0.16)` |
| glow (CTA) | `0 8px 18px var(--eg-glow)` |

### 레이아웃
- **사이드바 252px 고정** + 우측 유동 메인. 사이드바 배경 = surface, 우측 border `1px var(--line)`.
- 콘텐츠 카드 그리드. 좁은 화면에서 카드 세로 스택.
- 데모는 데스크톱 관제 화면 우선(담당자용 SaaS). 모바일은 MVP 범위 밖 — 단, 카드/스택 구조라 반응형 붕괴는 없게.

---

## 5. 컴포넌트 룩 (데모 기준)

- **카드**: `background surface · radius 20 · shadow-card`. 헤더(아이콘+타이틀 800)→본문→푸터(구분선 위 메타/CTA).
- **주요 버튼(CTA)**: `background primary · color #fff · radius 12 · padding 12px · weight 700 · shadow-glow`. 예: "리포트 생성", "퇴사자 등록".
- **부 버튼**: `background surface · color primary/ink · border 1px line2 · radius 9`. 예: "전문가 연결".
- **칩**: `background soft · radius 11 · padding 10×14 · weight 600 · color ink2`. 드롭다운은 우측 chevron.
- **아이콘 버튼**: 34–42px 정사각, `background surface · border 1px line · radius 10–12`. lucide류 stroke 2.2–2.6, round cap/join.
- **레일 탭**: 알약형, 좌측 8px 원형 도트(레일 색), 활성 시 배경/그림자. 노무=청록·영업비밀=보라·보안=앰버 도트.
- **진행률 바**: 높이 7–9px, radius 5–6, 트랙=soft, 채움=해당 레일 색(또는 `linear-gradient(90deg, primary, teal)` 요약 지표).
- **레일 상세 헤더**: `linear-gradient(135deg, eg-1, eg-2)` 카드, 흰 텍스트, radius 20.
- **토스트**: 하단 등장, `egtoast` 애니메이션. "✓ …추가했습니다" 형태.
- **다크 토글**: 사이드바 하단 스위치(38×22 알약, knob 16px). 클래스 기반.

### ⚖️ §4 필수 시각 요소 (직역법 경계 — 반드시 구현)
1. **L1/L2/L3 출처 배지** — 모든 판정/알림 근거에 부착. 22×22, radius 7, 10px/700:
   - `L1` 법령 — fg `#0E8A99` / bg `#D6F5F7` (국가법령정보센터)
   - `L2` 판례·판정례 — fg `#8B5CF6` / bg `#ECE4F8` (중노위·대법원)
   - `L3` 정부 가이드 — fg `#22A06B` / bg `#DCF5E9` (고용부 매뉴얼)
   - → "GPT 래퍼 아니냐" 방어. 모든 근거 문장에 출처가 보이게.
2. **[전문가 연결]** — 판단이 필요한 분기마다 부 버튼으로 상시 배치. 별도 뷰도 있음. "판단 주체=전문가, 우리=도구" 구조를 UI로 못박는다.
3. **알림 카피는 상태·기한·사례** — "리스크 알림 N건" / "법정 기한 D-N" / "기준 대비 미충족 항목 N건" / "…판정된 사례가 있습니다". 판단 단정 금지(§4 표 참조).

---

## 6. 모션 원칙

데모 실제 keyframe 기반. **차분·짧게·기능적으로.** 장식성 애니메이션 금지.
| 이름 | 동작 | 용도 |
|---|---|---|
| pop | `scale(.97)→1 + fade` | 카드/모달 등장 |
| fade | opacity 0→1 | 뷰 전환 |
| drawer | `translateX(100%)→0` | 우측 드로어 |
| toast | `translateY(14px)+fade` | 토스트 |
| pulse | opacity 1↔.45 | 실시간/대기 상태 점 |

- 지속시간 짧게(150–250ms), ease-out. `prefers-reduced-motion` 존중.

---

## 7. 다크모드 (데모에 실재 — 라이트/다크 둘 다 지원)

클래스 기반(`<html class="dark">`). 데모의 `NEUTRAL_DARK` 원본을 그대로 채택.
| 토큰 | 라이트 | 다크 |
|---|---|---|
| background | `#E4ECEF` | `#0f131a` |
| surface/card | `#ffffff` | `#1d232e` |
| panel | `#F7FAFB` | `#161b24` |
| soft | `#F1F5F6` | `#232a36` |
| line | `#EAEFF1` | `#2c3440` |
| ink | `#14343A` | `#eef2f6` |
| ink2 | `#41616A` | `#c2ccd4` |
| primary | `#3C4E72` | `#45577E` (한 톤 밝게, 가독) |

- **레일 색은 다크에서 hue 유지**, soft 배경만 `color-mix(in srgb, <레일색> ~26%, #1d232e)`로 다크 표면과 혼합. ink는 밝은 톤으로 대체(예: 보라 ink `#b79cf8`). 정확값은 `tokens.css` `.dark` 블록.
- 다크에서 카드 그림자는 `rgba(0,0,0,0.35~0.5)`로 강화.

---

## 8. 디자인 토큰 → shadcn 주입

`docs/design/tokens.css` 참조. 요약:
- **shadcn 시맨틱 계약**(`--background/--foreground/--card/--primary/--secondary/--muted/--accent/--destructive/--border/--input/--ring/--radius/--chart-*/--sidebar-*`)을 라이트(`:root`)·다크(`.dark`) 모두 정의.
- **ExitGuard 도메인 토큰**(`--rail-*`, `--src-l1/2/3`, `--status-*`, `--eg-*`, radius/shadow 스케일)을 네임스페이스로 추가.
- **Tailwind v4**: 하단 `@theme inline` 블록이 `bg-primary`, `text-rail-secret`, `bg-rail-labor-soft` 등 유틸리티로 노출. **v3**면 `tailwind.config`의 `theme.extend.colors`에 `var(--...)` 매핑.
- 해리: `app/globals.css`에 이 파일을 붙이고 `<body class="font-sans">` + Pretendard 웹폰트 로드. shadcn `init` 후 생성된 기본 globals 색 블록을 이 파일로 교체.

---

## 9. tokens.css 대조 — 확인된 불일치·갭

값을 전수 대조했다. 대부분 데모(navy 프리셋+중립 스케일)와 **정확히 일치**한다. 아래 3건만 표면화:

1. **[미결정 — 최상단 참조]** primary 색 = 딥네이비 vs 청록. 이 문서는 **결정하지 않는다.** 근거·시각영향·되돌리기 3줄은 문서 최상단 `⚠️ [결정필요]` 섹션. 현재 tokens.css는 딥네이비.
2. **[프레이밍 정정]** tokens.css 헤더 주석은 "데모 기본 프라이머리는 청록"이라 하나, 데모는 **navy로 출고**된다(3618·3843·3844행). 현행 tokens.css(navy)가 데모 실제 상태와 일치. → 주석 문구는 역사적 흔적.
3. **[경미, 확인 요망]** 다크 `--ring`/`--sidebar-ring`/`--chart-5` = `#6672E0`는 데모 **navy 프리셋이 아니라 indigo 프리셋의 `eg2`** 에서 온 값(navy `eg2`는 `#45577E`). 다크 포커스 링을 밝게 하려는 의도로 보이나 출처 팔레트가 다름. 의도면 유지.
4. **[갭, 해리 실무 영향]** 데모는 옅은 teal 정보 콜아웃 배경 `--k-teal`(라이트 `#F1FBFC`)을 힌트 박스에 광범위하게 쓴다(데모 2233·2838행 등). tokens.css엔 이 매우 옅은 teal 표면 토큰이 없다 — 가장 가까운 `--accent`/`--teal-soft`는 `#D6F5F7`로 더 진함. 힌트 박스를 `--accent`로 대체하면 데모보다 진해 보임. 필요 시 `--eg-info-bg: #F1FBFC` 추가를 루나에 요청(현재 추가 안 함).

*(중립·레일·상태·출처 배지 값은 데모와 1:1 일치 확인.)*

---

## 부록 · 소스
- 진실 소스: `pitch/데모/ExitGuard-나모업로드-단일본.html` (팔레트·NEUTRAL_LIGHT/DARK·PALETTES·keyframe)
- 로고: `pitch/아이콘/exitguard-logo.svg` (+ wordmark·appicon)
- 소개페이지: `pitch/소개페이지/EixtGuard_소개페이지.html`
- 규율: `dobby/PRODUCT.md §3-3`(Fork & Customize)·`§4`(문구 규율)·`§6`(MVP 범위)
