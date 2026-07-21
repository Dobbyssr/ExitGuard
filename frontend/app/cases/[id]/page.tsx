import Link from "next/link";
import { ApiError, getCase } from "@/lib/api";
import { exitReasonLabel, intakeRouteLabel, caseStatusLabel } from "@/lib/labels";
import { GatePanel } from "./gate-panel";
import { RailTabs } from "./rail-tabs";

// 케이스 상세 + 통합 게이트(CM-07/08) — GET /cases/{id}.
export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const caseId = Number(id);

  let detail;
  try {
    detail = (await getCase(caseId)).data;
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "케이스를 불러오지 못했습니다.";
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-muted-foreground">
        {message}
      </div>
    );
  }

  const { case: c } = detail;
  const dday = Math.round((new Date(c.exit_date).getTime() - Date.now()) / 86_400_000);

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[23px] font-extrabold tracking-[-0.5px]">{c.subject_name}</h1>
            <span className="rounded-[var(--radius-badge)] bg-[var(--soft)] px-2.5 py-1 text-[11.5px] font-semibold text-foreground/70">
              {caseStatusLabel[c.status]}
            </span>
          </div>
          <p className="mt-1 text-[12.5px] text-muted-foreground">
            {c.subject_job} · {c.subject_rank}
            {c.subject_role_title ? ` · ${c.subject_role_title}` : ""} · {exitReasonLabel[c.exit_reason]} ·{" "}
            {intakeRouteLabel[c.intake_route]}
          </p>
          <p className="mt-0.5 text-[12.5px] font-semibold text-muted-foreground">
            퇴사일 {c.exit_date} · {dday >= 0 ? `D-${dday}` : `D+${-dday}`}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Link
            href={`/cases/${caseId}/evidence`}
            className="rounded-[var(--radius-btn)] border border-[var(--line2)] bg-card px-3.5 py-2 text-[12.5px] font-semibold text-foreground/80 hover:bg-secondary"
          >
            증적 아카이브 보기
          </Link>
          <Link
            href={`/cases/${caseId}/report`}
            className="rounded-[var(--radius-btn)] bg-primary px-3.5 py-2 text-[12.5px] font-semibold text-primary-foreground shadow-[var(--shadow-glow)] hover:bg-primary/90"
          >
            방어 리포트 보기
          </Link>
        </div>
      </div>

      <GatePanel caseId={caseId} initialGate={detail.gate} caseStatus={c.status} />
      <RailTabs caseId={caseId} rails={detail.rails} />
    </div>
  );
}
