// 검사항목 상태 칩 — 색은 tokens.css --status-*(DESIGN.md §2-4)를 상태 의미대로 재사용.
// 판단 단정이 아니라 "상태"만 표시한다(§4).
import type { ItemStatus } from "@/lib/api";
import { itemStatusLabel } from "@/lib/labels";
import { cn } from "@/lib/utils";

const STATUS_VAR: Record<ItemStatus, string> = {
  pending: "--muted-1",
  submitted: "--status-warn",
  approved: "--status-ok",
  rejected: "--status-danger",
  not_applicable: "--muted-2",
};

export function ItemStatusBadge({ status, className }: { status: ItemStatus; className?: string }) {
  const v = STATUS_VAR[status];
  const soft = v === "--muted-1" || v === "--muted-2" ? "--soft" : `${v}-soft`;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-[var(--radius-badge)] px-2.5 py-1 text-[11.5px] font-semibold whitespace-nowrap",
        className
      )}
      style={{ color: `var(${v})`, background: `var(${soft})` }}
    >
      {itemStatusLabel[status]}
    </span>
  );
}
