// 대조결과 5행 렌더 — CompareCard(케이스 상세)와 DefenseReport(compare_findings)가 공유한다.
// data-model §6-2 shape 그대로: kind 순서 고정 · boundary_notice 항상 노출(§6-3 · 직역법 §4).
import { Lock } from "lucide-react";
import { SourceBadge } from "@/components/source-badge";
import { ExpertLink } from "@/components/expert-link";
import type { Badge, CompareRow } from "@/lib/api";
import { compareRowKindLabel } from "@/lib/labels";

export function CompareRows({
  rows,
  badges,
  unmetCount,
  boundaryNotice,
  expertReferral,
  sealedSeq,
}: {
  rows: CompareRow[];
  badges: Badge[];
  unmetCount: number;
  boundaryNotice: string;
  expertReferral?: boolean | null;
  sealedSeq?: number;
}) {
  return (
    <div className="flex flex-col gap-0 divide-y divide-border">
      <div className="flex flex-wrap items-center justify-between gap-2 py-2.5">
        <span className="text-[12px] font-semibold text-muted-foreground">기준 대비 미충족 {unmetCount}건</span>
        <div className="flex items-center gap-1.5">
          {badges.map((b, i) => (
            <SourceBadge key={i} tier={b.tier} />
          ))}
          {sealedSeq != null && (
            <span className="flex items-center gap-1 rounded-[var(--radius-badge)] bg-[var(--soft)] px-2 py-0.5 text-[10.5px] font-semibold text-muted-foreground">
              <Lock className="size-3" />
              봉인된 기록 #{sealedSeq}
            </span>
          )}
        </div>
      </div>

      {rows.map((row) => (
        <div key={row.kind} className="flex items-start justify-between gap-3 py-2.5 text-sm">
          <span className="w-20 shrink-0 text-[11.5px] font-semibold text-muted-foreground">
            {compareRowKindLabel[row.kind]}
          </span>
          <span className="flex-1 text-[12.5px] leading-relaxed">
            {row.text}
            {row.kind === "source" && row.url && (
              <a
                href={row.url}
                target="_blank"
                rel="noreferrer"
                className="ml-1.5 font-semibold text-[var(--src-l1)] underline underline-offset-2"
              >
                원문 보기
              </a>
            )}
          </span>
        </div>
      ))}

      <p className="pt-3 text-[11px] leading-relaxed text-muted-foreground">{boundaryNotice}</p>
      {expertReferral && (
        <div className="flex justify-end pt-2">
          <ExpertLink />
        </div>
      )}
    </div>
  );
}
