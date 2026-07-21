import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { CaseSummary } from "@/lib/api";
import { caseStatusLabel } from "@/lib/labels";
import { ExitReasonBadge } from "./exit-reason-badge";

export function CaseCard({ item }: { item: CaseSummary }) {
  const ddayLabel = item.dday >= 0 ? `D-${item.dday}` : `D+${-item.dday}`;
  return (
    <Link href={`/cases/${item.id}`}>
      <Card className="transition-shadow hover:shadow-[var(--shadow-card)]">
        <CardContent className="flex flex-wrap items-center gap-3 py-2 sm:flex-nowrap sm:gap-4">
          <div className="w-full min-w-0 sm:w-auto sm:flex-1">
            <div className="flex items-center gap-2">
              <span className="text-[16px] font-extrabold">{item.subject_name}</span>
              <ExitReasonBadge reason={item.exit_reason} />
            </div>
            <p className="mt-0.5 text-[12.5px] text-muted-foreground">
              {item.subject_job} · {item.subject_rank}
            </p>
          </div>

          <div className="flex w-32 flex-col gap-1">
            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
              <span>완료율</span>
              <span className="font-bold text-foreground">{item.overall_completion}%</span>
            </div>
            <div className="h-[7px] overflow-hidden rounded-full bg-[var(--soft)]">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${item.overall_completion}%`,
                  background: "linear-gradient(90deg, var(--eg-1), var(--eg-3))",
                }}
              />
            </div>
          </div>

          {item.risk_count > 0 ? (
            <span className="flex items-center gap-1 rounded-[var(--radius-badge)] bg-[var(--status-danger-soft)] px-2.5 py-1 text-[11.5px] font-semibold text-[var(--status-danger)]">
              <AlertTriangle className="size-3.5" />
              리스크 알림 {item.risk_count}건
            </span>
          ) : (
            <span className="rounded-[var(--radius-badge)] bg-[var(--status-ok-soft)] px-2.5 py-1 text-[11.5px] font-semibold text-[var(--status-ok)]">
              리스크 없음
            </span>
          )}

          <span className="w-14 shrink-0 text-right text-[12.5px] font-bold text-muted-foreground">
            {ddayLabel}
          </span>

          <span className="w-20 shrink-0 rounded-[var(--radius-badge)] bg-[var(--soft)] px-2.5 py-1 text-center text-[11.5px] font-semibold text-foreground/70">
            {caseStatusLabel[item.status]}
          </span>
        </CardContent>
      </Card>
    </Link>
  );
}
