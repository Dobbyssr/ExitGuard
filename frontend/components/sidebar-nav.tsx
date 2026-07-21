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

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] bg-primary text-[15px] font-extrabold text-primary-foreground">
        G
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
      {/* 데스크톱 사이드바 (md 이상) */}
      <aside className="hidden w-[252px] shrink-0 flex-col border-r border-border bg-[var(--surface)] px-4 py-6 md:flex">
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
      <header className="flex w-full items-center justify-between gap-2 overflow-x-auto border-b border-border bg-[var(--surface)] px-4 py-3 md:hidden">
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
