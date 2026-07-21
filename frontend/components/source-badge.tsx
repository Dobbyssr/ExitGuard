// 근거 출처 배지 — L1(법령)/L2(판례·판정례)/L3(정부가이드).
// ⚖️ §4 필수 시각요소: "GPT 래퍼 아니냐" 방어 — 모든 근거 문장에 출처를 붙인다.
// 색은 tokens.css --src-l1/2/3(-bg) 그대로(DESIGN.md §5). 새 색 창작 금지.
import type { StandardTier } from "@/lib/api";
import { cn } from "@/lib/utils";

const TIER_VAR: Record<StandardTier, string> = {
  L1: "--src-l1",
  L2: "--src-l2",
  L3: "--src-l3",
};

export function SourceBadge({ tier, className }: { tier: StandardTier; className?: string }) {
  const v = TIER_VAR[tier];
  return (
    <span
      className={cn(
        "inline-flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-[var(--radius-xs)] text-[10px] font-bold",
        className
      )}
      style={{ color: `var(${v})`, background: `var(${v}-bg)` }}
      title={`${tier} 출처 근거`}
    >
      {tier}
    </span>
  );
}
