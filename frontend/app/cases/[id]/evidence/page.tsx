import Link from "next/link";
import { ChevronLeft, Lock } from "lucide-react";
import { ApiError, getEvidence } from "@/lib/api";
import { evidenceEventTypeLabel } from "@/lib/labels";

// 증적 아카이브(CM-12) — GET /cases/{id}/evidence. seq 순 체인 + head_hash(위변조 앵커) 표시.
export default async function EvidencePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const caseId = Number(id);

  let entries;
  let meta;
  try {
    const res = await getEvidence(caseId);
    entries = res.data;
    meta = res.meta;
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "증적을 불러오지 못했습니다.";
    return <div className="mx-auto max-w-2xl text-center text-sm text-muted-foreground">{message}</div>;
  }

  const sorted = [...entries].sort((a, b) => a.seq - b.seq);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div className="flex items-center gap-3">
        <Link href={`/cases/${caseId}`} className="text-muted-foreground hover:text-foreground">
          <ChevronLeft className="size-5" />
        </Link>
        <h1 className="text-[23px] font-extrabold tracking-[-0.5px]">증적 아카이브</h1>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-xl bg-card p-4 shadow-[var(--shadow-card)]">
        <span className="flex items-center gap-1.5 rounded-[var(--radius-badge)] bg-[var(--status-ok-soft)] px-3 py-1.5 text-[12px] font-bold text-[var(--status-ok)]">
          <Lock className="size-3.5" />
          {meta?.seal_status === "sealed" ? "봉인 완료" : "봉인 누적중"}
        </span>
        <span className="text-[12px] text-muted-foreground">기록 {meta?.total_count ?? sorted.length}건</span>
        {meta?.head_hash && (
          <span className="truncate rounded-[var(--radius-badge)] bg-[var(--soft)] px-2.5 py-1 font-mono text-[11px] text-muted-foreground">
            head_hash {meta.head_hash.slice(0, 16)}…
          </span>
        )}
      </div>

      {sorted.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-muted-foreground">
          아직 봉인된 증적이 없습니다. 항목을 상신·검토하면 자동으로 쌓입니다.
        </p>
      ) : (
        <ol className="flex flex-col gap-3">
          {sorted.map((e) => (
            <li key={e.id} className="rounded-xl bg-card p-4 shadow-[var(--shadow-card)]">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="rounded-[var(--radius-badge)] bg-[var(--soft)] px-2 py-0.5 text-[11px] font-bold text-muted-foreground">
                    #{e.seq}
                  </span>
                  <span className="text-[13px] font-bold">{evidenceEventTypeLabel[e.event_type]}</span>
                  <span className="rounded-[var(--radius-badge)] px-2 py-0.5 text-[10.5px] font-semibold text-muted-foreground">
                    {e.origin === "auto" ? "자동 봉인" : "수동 봉인"}
                  </span>
                </div>
                <span className="text-[11.5px] text-muted-foreground">
                  {new Date(e.occurred_at).toLocaleString("ko-KR")}
                </span>
              </div>
              <p className="mt-1.5 text-[12.5px] text-foreground/80">
                {e.action} · {e.actor}
              </p>
              <p className="mt-2 truncate font-mono text-[10.5px] text-muted-foreground">
                hash {e.integrity_hash.slice(0, 20)}… {e.prev_hash ? `← prev ${e.prev_hash.slice(0, 12)}…` : "(첫 기록)"}
              </p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
