"use client";

// 내비게이션 — DESIGN.md §4는 데스크톱 사이드바(252px 고정) 우선이라 명시하지만,
// "반응형 붕괴는 없게"도 함께 요구한다(§4). 그래서 md 미만에서는 사이드바를 숨기고
// 얇은 상단 바로 전환한다(같은 NAV 배열을 공유 — 항목 중복 정의 안 함).
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileStack, FilePlus2, Users } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/cases", label: "케이스 목록", icon: FileStack },
  { href: "/cases/new", label: "새 케이스 접수", icon: FilePlus2 },
];

// 로고 = ExitGuard 브랜드 마크(방패+체크). 데모(pitch/데모 standalone)의 SVG 패스를 그대로
// 가져오되, 색은 옆 "Guard" 워드마크와 맞춰 FE 브랜드 틸(--teal-1) 위 딥네이비(--primary) 배경.
function Logo() {
  return (
    <div className="flex items-center gap-2">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] bg-primary">
        <svg
          viewBox="420 190 360 490"
          className="h-[22px] w-[22px]"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            d="M600 210 L760 280 V430 C760 545 690 615 600 655 C510 615 440 545 440 430 V280 Z"
            style={{ stroke: "var(--teal-1)" }}
            strokeWidth={26}
            strokeLinejoin="round"
          />
          <path
            d="M545 430 l45 45 90 -110"
            style={{ stroke: "var(--teal-1)" }}
            strokeWidth={26}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="text-[16px] font-extrabold tracking-[-0.5px]">
        Exit<span style={{ color: "var(--teal-1)" }}>Guard</span>
      </span>
    </div>
  );
}

export function SidebarNav() {
  const pathname = usePathname();

  function isActive(href: string) {
    return pathname === href || (href !== "/cases" && pathname.startsWith(href));
  }

  return (
    <>
      {/* 데스크톱 사이드바 (md 이상) — 인쇄(방어 리포트 PDF 저장)엔 노출 안 함 */}
      <aside className="hidden w-[252px] shrink-0 flex-col border-r border-border bg-[var(--surface)] px-4 py-6 md:flex print:hidden">
        <div className="mb-8 px-2">
          <Logo />
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13.5px] font-semibold transition-colors",
                isActive(href) ? "bg-primary text-primary-foreground" : "text-foreground/70 hover:bg-secondary"
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          ))}
        </nav>
        <a
          href="mailto:expert@exitguard.example?subject=ExitGuard%20전문가%20확인%20요청"
          className="mt-auto flex items-center gap-3 rounded-xl border border-border px-3.5 py-2.5 text-[13.5px] font-semibold text-foreground/80 hover:bg-secondary"
        >
          <Users className="size-4" />
          전문가 연결
        </a>
      </aside>

      {/* 모바일 상단 바 (md 미만) — 반응형 붕괴 방지(DESIGN.md §4) */}
      <header className="flex w-full items-center justify-between gap-2 overflow-x-auto border-b border-border bg-[var(--surface)] px-4 py-3 md:hidden print:hidden">
        <Logo />
        <nav className="flex shrink-0 items-center gap-1">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              aria-label={label}
              className={cn(
                "flex items-center justify-center rounded-lg p-2",
                isActive(href) ? "bg-primary text-primary-foreground" : "text-foreground/70 hover:bg-secondary"
              )}
            >
              <Icon className="size-4" />
            </Link>
          ))}
          <a
            href="mailto:expert@exitguard.example?subject=ExitGuard%20전문가%20확인%20요청"
            aria-label="전문가 연결"
            className="flex items-center justify-center rounded-lg p-2 text-foreground/70 hover:bg-secondary"
          >
            <Users className="size-4" />
          </a>
        </nav>
      </header>
    </>
  );
}
