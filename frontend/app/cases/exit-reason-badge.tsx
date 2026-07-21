// 퇴사 사유유형 배지 — 색은 tokens.css --status-*(DESIGN.md §2-4, 케이스유형 색)을 그대로 재사용.
// contract_expiry는 DESIGN.md 4색 표에 없어 중립색으로 대체(디자인 갭 — 도비 보고).
import type { ExitReason } from "@/lib/api";
import { exitReasonLabel } from "@/lib/labels";

const REASON_VAR: Record<ExitReason, string> = {
  dismissal: "--status-danger",
  recommended_resignation: "--status-warn",
  voluntary: "--status-info",
  contract_expiry: "--muted-1",
};

export function ExitReasonBadge({ reason }: { reason: ExitReason }) {
  const v = REASON_VAR[reason];
  const soft = v === "--muted-1" ? "--soft" : `${v}-soft`;
  return (
    <span
      className="inline-flex items-center rounded-[var(--radius-badge)] px-2.5 py-1 text-[11.5px] font-semibold whitespace-nowrap"
      style={{ color: `var(${v})`, background: `var(${soft})` }}
    >
      {exitReasonLabel[reason]}
    </span>
  );
}
