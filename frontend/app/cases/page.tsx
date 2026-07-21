import Link from "next/link";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { listCases, type CaseListFilter } from "@/lib/api";
import { caseStatusFilterLabel } from "@/lib/labels";
import { CaseCard } from "./case-card";
import { cn } from "@/lib/utils";

const FILTERS: CaseListFilter[] = ["all", "in_progress", "review_waiting", "completed"];

// 케이스 목록(CM-03) — GET /cases. 필터/검색/정렬은 querystring 기반 서버 렌더링(JS 없이 동작).
export default async function CasesPage({
  searchParams,
}: {
  searchParams: Promise<{ filter?: string; q?: string; sort?: string }>;
}) {
  const sp = await searchParams;
  const filter = (FILTERS.includes(sp.filter as CaseListFilter) ? sp.filter : "all") as CaseListFilter;
  const q = sp.q ?? "";
  const sort = sp.sort ?? "default";

  const { data: cases } = await listCases({ filter, q, sort });

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-[23px] font-extrabold tracking-[-0.5px]">케이스 목록</h1>
        <Button render={<Link href="/cases/new" />} nativeButton={false} className="gap-1.5">
          <Plus className="size-4" />
          새 케이스 접수
        </Button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1.5 rounded-[var(--radius-chip)] bg-[var(--soft)] p-1">
          {FILTERS.map((f) => (
            <Link
              key={f}
              href={`/cases?filter=${f}${q ? `&q=${encodeURIComponent(q)}` : ""}${sort !== "default" ? `&sort=${sort}` : ""}`}
              className={cn(
                "rounded-[9px] px-3.5 py-1.5 text-[12.5px] font-semibold transition-colors",
                filter === f ? "bg-card shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {caseStatusFilterLabel[f]}
            </Link>
          ))}
        </div>

        <form className="flex items-center gap-2" action="/cases" method="GET">
          <input type="hidden" name="filter" value={filter} />
          <input
            name="q"
            defaultValue={q}
            placeholder="대상자 이름 검색"
            className="h-8 w-44 rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring"
          />
          <select
            name="sort"
            defaultValue={sort}
            className="h-8 rounded-lg border border-input bg-transparent px-2 text-sm outline-none"
          >
            <option value="default">최신순</option>
            <option value="deadline">기한순</option>
            <option value="risk">리스크순</option>
            <option value="completion">완료율순</option>
            <option value="name">이름순</option>
          </select>
          <Button type="submit" variant="outline" size="sm">
            검색
          </Button>
        </form>
      </div>

      <div className="flex flex-col gap-3">
        {cases.length === 0 ? (
          <p className="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-muted-foreground">
            조건에 맞는 케이스가 없습니다.
          </p>
        ) : (
          cases.map((c) => <CaseCard key={c.id} item={c} />)
        )}
      </div>
    </div>
  );
}
