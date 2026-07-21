import Link from "next/link";
import { ChevronLeft, ShieldCheck, AlertTriangle, Lock } from "lucide-react";
import { ApiError, getDefenseReport, type Rail } from "@/lib/api";
import { railLabel, exitReasonLabel, caseStatusLabel, evidenceEventTypeLabel, sealStatusLabel } from "@/lib/labels";
import { SourceBadge } from "@/components/source-badge";
import { CompareRows } from "@/components/compare-rows";
import { GateDonut } from "@/components/gate-donut";
import { PrintButton } from "@/components/print-button";

const RAILS: Rail[] = ["labor", "trade_secret", "security"];

// 방어 리포트(CM-13, B1 머니샷) — GET /cases/{id}/evidence/export?format=json.
// PDF는 백엔드 미구현(501) → 브라우저 print(@media print, ponytail)로 대체.
export default async function DefenseReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const caseId = Number(id);

  let report;
  try {
    report = (await getDefenseReport(caseId)).data;
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "방어 리포트를 불러오지 못했습니다.";
    return <div className="mx-auto max-w-2xl text-center text-sm text-muted-foreground">{message}</div>;
  }

  const { case: c, kpi, rails, compare_findings, evidence_chain, boundary_notice } = report;
  const cardClass = "rounded-xl bg-card p-6 shadow-[var(--shadow-card)] print:border print:border-border print:shadow-none";

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 print:max-w-none">
      <div className="flex items-center justify-between gap-3 print:hidden">
        <div className="flex items-center gap-3">
          <Link href={`/cases/${caseId}`} className="text-muted-foreground hover:text-foreground">
            <ChevronLeft className="size-5" />
          </Link>
          <h1 className="text-[23px] font-extrabold tracking-[-0.5px]">방어 가능 상태 리포트</h1>
        </div>
        <PrintButton />
      </div>

      {/* 표지 — 대상자 정보 + 생성시각 + 경계고지(§10 필수, 리포트 표지엔 반드시 노출) */}
      <div className={cardClass}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-[19px] font-extrabold">{c.subject_name}</h2>
            <p className="mt-1 text-[12.5px] text-muted-foreground">
              {c.subject_job} · {c.subject_rank} · {exitReasonLabel[c.exit_reason]} · 퇴사일 {c.exit_date}
            </p>
          </div>
          <div className="text-right text-[11.5px] text-muted-foreground">
            <p>{caseStatusLabel[c.status]}</p>
            <p>생성 {new Date(report.generated_at).toLocaleString("ko-KR")}</p>
          </div>
        </div>
        <div className="mt-4 rounded-lg bg-[var(--soft)] px-4 py-3">
          <p className="text-[11.5px] leading-relaxed text-foreground/80">{boundary_notice}</p>
        </div>
      </div>

      {/* KPI — 종합 게이트(§5) 파생, "방어 가능 상태" 경계 동반 */}
      <div className={cardClass}>
        <h3 className="text-[14.5px] font-extrabold">종합 현황</h3>
        <div className="mt-4 flex flex-wrap items-center gap-8">
          <GateDonut percent={kpi.overall_completion} />
          <div className="flex min-w-[220px] flex-1 flex-col gap-3">
            {RAILS.map((rail) => (
              <div key={rail} className="flex items-center gap-3">
                <span className="w-16 shrink-0 text-[12px] font-semibold text-muted-foreground">
                  {railLabel[rail]}
                </span>
                <span className="text-[13px] font-bold">{kpi.rail_completion[rail]}%</span>
              </div>
            ))}
          </div>
          <div className="flex flex-col items-start gap-2">
            {kpi.defensible ? (
              <span className="flex items-center gap-1.5 rounded-[var(--radius-badge)] bg-[var(--status-ok-soft)] px-3 py-1.5 text-[12.5px] font-bold text-[var(--status-ok)]">
                <ShieldCheck className="size-4" />
                방어 가능 상태
              </span>
            ) : (
              <span className="flex items-center gap-1.5 rounded-[var(--radius-badge)] bg-[var(--status-danger-soft)] px-3 py-1.5 text-[12.5px] font-bold text-[var(--status-danger)]">
                <AlertTriangle className="size-4" />
                리스크 알림 {kpi.risk_count}건
              </span>
            )}
            <p className="max-w-[220px] text-[11px] leading-relaxed text-muted-foreground">
              ※ &ldquo;방어 가능 상태&rdquo;는 공개 기준 대비 항목 충족 상태를 뜻하며, 적법·승소를 보증하지
              않습니다.
            </p>
          </div>
        </div>
      </div>

      {/* 3레일 요약 */}
      <div className={cardClass}>
        <h3 className="text-[14.5px] font-extrabold">레일별 요약</h3>
        <div className="mt-4 flex flex-col gap-3">
          {rails.map((r) => (
            <div
              key={r.rail}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border px-4 py-3"
            >
              <span className="text-[13px] font-semibold">{railLabel[r.rail]}</span>
              <div className="flex items-center gap-3">
                <span className="text-[12px] text-muted-foreground">완료율 {r.completion}%</span>
                <span className="text-[12px] text-muted-foreground">미충족 {r.unmet_count}건</span>
                <div className="flex items-center gap-1">
                  {r.badges.map((b, i) => (
                    <SourceBadge key={i} tier={b.tier} />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* compare_findings — 봉인된 compare_recorded 스냅샷 인용(재계산·환각 없음, §10) */}
      {compare_findings.length > 0 && (
        <div className={cardClass}>
          <h3 className="text-[14.5px] font-extrabold">판정례 대조 기록 (봉인된 기록)</h3>
          <div className="mt-4 flex flex-col gap-5 divide-y divide-border">
            {compare_findings.map((f, i) => (
              <div key={i} className={i > 0 ? "pt-5" : undefined}>
                <p className="mb-2 text-[12.5px] font-semibold text-muted-foreground">
                  {railLabel[f.rail]} · {f.subject}
                </p>
                <CompareRows
                  rows={f.rows}
                  badges={f.badges}
                  unmetCount={f.unmet_count}
                  boundaryNotice={f.boundary_notice}
                  sealedSeq={f.sealed_seq}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* evidence_chain — head_hash가 위변조 검증 앵커("봉인된 방어 문서"의 핵심) */}
      <div className={cardClass}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-[14.5px] font-extrabold">증적 체인</h3>
          <span className="flex items-center gap-1.5 rounded-[var(--radius-badge)] bg-[var(--status-ok-soft)] px-3 py-1.5 text-[12px] font-bold text-[var(--status-ok)]">
            <Lock className="size-3.5" />
            {sealStatusLabel[evidence_chain.seal_status]}
          </span>
        </div>
        <p className="mt-2 text-[12px] text-muted-foreground">
          기록 {evidence_chain.total_count}건 · seq {evidence_chain.first_seq}~{evidence_chain.last_seq}
        </p>
        {evidence_chain.head_hash && (
          <div className="mt-3 rounded-lg bg-[var(--soft)] px-4 py-3">
            <p className="text-[11px] font-semibold text-muted-foreground">head_hash (위변조 검증 앵커)</p>
            <p className="mt-1 break-all font-mono text-[11.5px]">{evidence_chain.head_hash}</p>
          </div>
        )}
        <ol className="mt-4 flex flex-col gap-2">
          {evidence_chain.entries.map((e) => (
            <li
              key={e.seq}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border px-3 py-2 text-[11.5px]"
            >
              <div className="flex items-center gap-2">
                <span className="rounded-[var(--radius-badge)] bg-[var(--soft)] px-2 py-0.5 font-bold text-muted-foreground">
                  #{e.seq}
                </span>
                <span className="font-semibold">{evidenceEventTypeLabel[e.event_type]}</span>
                <span className="text-muted-foreground">{e.actor}</span>
              </div>
              <span className="text-muted-foreground">{new Date(e.occurred_at).toLocaleString("ko-KR")}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* 하단 경계 고지 반복 — 외부 제출 가능 문서라 표지+본문 양쪽에 승계(§10) */}
      <p className="rounded-xl border border-dashed border-border px-4 py-3 text-[11px] leading-relaxed text-muted-foreground print:border-solid">
        {boundary_notice}
      </p>
    </div>
  );
}
