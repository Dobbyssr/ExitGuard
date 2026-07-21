"use client";

// 통합 게이트(CM-08) — GET /cases/{id}/gate 실호출 + 승인(POST /cases/{id}/approve, 409 처리).
// ⚖️ "방어 가능 상태"는 적법·승소 보증이 아니다(§4) — 항상 경계문구를 함께 표기한다.
import { useState } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw, AlertTriangle, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { GateDonut } from "@/components/gate-donut";
import { ExpertLink } from "@/components/expert-link";
import { ApiError, approveCase, getGate, type CaseStatus, type Gate, type Rail } from "@/lib/api";
import { railLabel } from "@/lib/labels";

const RAILS: Rail[] = ["labor", "trade_secret", "security"];
// Tailwind는 클래스명을 소스에서 문자열 그대로 스캔한다 — 템플릿 리터럴 조합(`bg-${x}`)은
// 안 잡힌다. 그래서 레일별 완성된 클래스명을 표로 고정해둔다.
const RAIL_BAR_CLASS: Record<Rail, { track: string; fill: string }> = {
  labor: { track: "bg-rail-labor-soft", fill: "bg-rail-labor" },
  trade_secret: { track: "bg-rail-secret-soft", fill: "bg-rail-secret" },
  security: { track: "bg-rail-security-soft", fill: "bg-rail-security" },
};

export function GatePanel({
  caseId,
  initialGate,
  caseStatus,
}: {
  caseId: number;
  initialGate: Gate;
  caseStatus: CaseStatus;
}) {
  const router = useRouter();
  const [gate, setGate] = useState(initialGate);
  // 서버 컴포넌트가 케이스 상세를 재조회(router.refresh)하면 새 initialGate가 내려온다 — 렌더 중 동기화.
  // (effect로 setState하면 리액트가 캐스케이딩 렌더로 경고한다 — "prop 변경 시 state 조정"의
  // 권장 패턴은 렌더 중 비교+setState. https://react.dev/learn/you-might-not-need-an-effect)
  const [prevInitialGate, setPrevInitialGate] = useState(initialGate);
  if (initialGate !== prevInitialGate) {
    setPrevInitialGate(initialGate);
    setGate(initialGate);
  }
  const [refreshing, setRefreshing] = useState(false);
  const [approving, setApproving] = useState(false);
  const [denyReason, setDenyReason] = useState<{ risk_count: number; submitted_count: number } | null>(null);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const { data } = await getGate(caseId);
      setGate(data);
    } catch {
      toast.error("게이트 새로고침에 실패했습니다");
    } finally {
      setRefreshing(false);
    }
  }

  async function handleApprove() {
    setApproving(true);
    setDenyReason(null);
    try {
      const { meta } = await approveCase(caseId);
      toast.success(meta?.toast ?? "방어 가능 상태로 승인되었습니다");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        const fields = (err.fields ?? {}) as { risk_count?: number; submitted_count?: number };
        setDenyReason({ risk_count: fields.risk_count ?? 0, submitted_count: fields.submitted_count ?? 0 });
        toast.error(err.message);
      } else {
        toast.error("승인 처리 중 오류가 발생했습니다");
      }
    } finally {
      setApproving(false);
    }
  }

  return (
    <div className="rounded-xl bg-card p-6 shadow-[var(--shadow-card)]">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-[14.5px] font-extrabold">통합 게이트</h2>
        <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={refreshing} className="gap-1.5 text-muted-foreground">
          <RefreshCw className={refreshing ? "size-3.5 animate-spin" : "size-3.5"} />
          게이트 새로고침
        </Button>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-8">
        <GateDonut percent={gate.overall_completion} />

        <div className="flex min-w-[220px] flex-1 flex-col gap-3">
          {RAILS.map((rail) => (
            <div key={rail} className="flex items-center gap-3">
              <span className="w-16 shrink-0 text-[12px] font-semibold text-muted-foreground">{railLabel[rail]}</span>
              <div className={`h-[8px] flex-1 overflow-hidden rounded-full ${RAIL_BAR_CLASS[rail].track}`}>
                <div
                  className={`h-full rounded-full ${RAIL_BAR_CLASS[rail].fill}`}
                  style={{ width: `${gate.rail_completion[rail]}%` }}
                />
              </div>
              <span className="w-9 shrink-0 text-right text-[12px] font-bold">{gate.rail_completion[rail]}%</span>
            </div>
          ))}
        </div>

        <div className="flex flex-col items-start gap-2">
          {gate.risk_count > 0 ? (
            <span className="flex items-center gap-1.5 rounded-[var(--radius-badge)] bg-[var(--status-danger-soft)] px-3 py-1.5 text-[12.5px] font-bold text-[var(--status-danger)]">
              <AlertTriangle className="size-4" />
              리스크 알림 {gate.risk_count}건
            </span>
          ) : (
            <span className="flex items-center gap-1.5 rounded-[var(--radius-badge)] bg-[var(--status-ok-soft)] px-3 py-1.5 text-[12.5px] font-bold text-[var(--status-ok)]">
              <ShieldCheck className="size-4" />
              방어 가능 상태
            </span>
          )}
          <p className="max-w-[220px] text-[11px] leading-relaxed text-muted-foreground">
            ※ &ldquo;방어 가능 상태&rdquo;는 봉인된 기록이 있다는 뜻이며, 적법·승소를 보증하지 않습니다.
          </p>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
        <div className="flex items-center gap-2">
          {denyReason && (
            <p className="text-[12px] font-medium text-[var(--status-danger)]">
              미충족 사유 — 리스크 알림 {denyReason.risk_count}건 · 검토 대기 상신 {denyReason.submitted_count}건
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ExpertLink />
          {caseStatus !== "completed" && (
            <Button onClick={handleApprove} disabled={approving} className="shadow-[var(--shadow-glow)]">
              {approving ? "승인 처리 중..." : "퇴사 승인 확정"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
