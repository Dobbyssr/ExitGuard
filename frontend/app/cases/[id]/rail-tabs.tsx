"use client";

// 레일별 항목 리스트(CM-07) — 케이스 상세 응답의 rails.<rail> 그대로 렌더(추가 fetch 없음).
import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { CompareCard } from "@/components/compare-card";
import { ItemStatusBadge } from "@/components/item-status-badge";
import { SourceBadge } from "@/components/source-badge";
import { ItemDrawer } from "./item-drawer";
import type { CaseDetail, Item, Rail } from "@/lib/api";
import { railLabel, itemKindLabel } from "@/lib/labels";
import { cn } from "@/lib/utils";

const RAILS: Rail[] = ["labor", "trade_secret", "security"];
// 완성된 클래스명 고정(Tailwind 스캐너가 동적 문자열 조합을 못 잡는다 — gate-panel과 동일 이유).
const DOT_CLASS: Record<Rail, string> = {
  labor: "bg-rail-labor",
  trade_secret: "bg-rail-secret",
  security: "bg-rail-security",
};

export function RailTabs({ caseId, rails }: { caseId: number; rails: CaseDetail["rails"] }) {
  const [selected, setSelected] = useState<Item | null>(null);

  return (
    <div className="rounded-xl bg-card p-6 shadow-[var(--shadow-card)]">
      <Tabs defaultValue="labor">
        <TabsList className="h-auto bg-[var(--soft)] p-1">
          {RAILS.map((rail) => (
            <TabsTrigger key={rail} value={rail} className="gap-2 rounded-[var(--radius-chip)] px-4 py-1.5">
              <span className={cn("size-2 rounded-full", DOT_CLASS[rail])} />
              {railLabel[rail]}
              <span className="text-muted-foreground">{rails[rail]?.completion ?? 0}%</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {RAILS.map((rail) => {
          const summary = rails[rail];
          return (
            <TabsContent key={rail} value={rail} className="mt-4 flex flex-col gap-3">
              {rail === "labor" && <CompareCard caseId={caseId} />}
              {!summary || summary.items.length === 0 ? (
                <p className="rounded-lg border border-dashed border-border px-4 py-8 text-center text-[12.5px] text-muted-foreground">
                  이 케이스엔 {railLabel[rail]} 레일 항목이 없습니다(프로파일 미매핑).
                </p>
              ) : (
                summary.items.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelected(item)}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border px-4 py-3 text-left transition-colors hover:bg-secondary"
                  >
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="shrink-0 rounded-[var(--radius-badge)] bg-[var(--soft)] px-2 py-0.5 text-[11px] font-semibold text-muted-foreground">
                        {item.code}
                      </span>
                      <span className="truncate text-[13px] font-semibold">{item.name}</span>
                      <span className="shrink-0 text-[11px] text-muted-foreground">{itemKindLabel[item.kind]}</span>
                      {item.blocking && (
                        <span className="shrink-0 text-[10px] font-bold text-[var(--status-danger)]">필수</span>
                      )}
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {item.badges.map((b, i) => (
                        <SourceBadge key={i} tier={b.tier} />
                      ))}
                      <ItemStatusBadge status={item.status} />
                    </div>
                  </button>
                ))
              )}
            </TabsContent>
          );
        })}
      </Tabs>

      <ItemDrawer item={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
