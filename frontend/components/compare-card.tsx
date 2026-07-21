"use client";

// LB-04 판정례 대조 카드 — POST /cases/{id}/intake-compare 실연결(api-spec §2-3).
// 실행할 때마다 서버가 compare_recorded 증적을 봉인한다(증적 아카이브 1건 증가는 정상 동작).
import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CompareRows } from "@/components/compare-rows";
import { ApiError, intakeCompare, type CompareResult } from "@/lib/api";

export function CompareCard({ caseId }: { caseId: number }) {
  const [result, setResult] = useState<CompareResult | null>(null);
  const [running, setRunning] = useState(false);

  async function handleRun() {
    setRunning(true);
    try {
      const { data } = await intakeCompare(caseId);
      setResult(data);
      toast.success("판정례 대조를 실행했습니다 — 결과가 증적으로 봉인되었습니다");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "대조 실행 중 오류가 발생했습니다");
    } finally {
      setRunning(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>기준 대조</CardTitle>
        <Button size="sm" onClick={handleRun} disabled={running} className="shadow-[var(--shadow-glow)]">
          {running ? "대조 실행 중..." : "판정례 대조 실행"}
        </Button>
      </CardHeader>
      <CardContent>
        {result ? (
          <CompareRows
            rows={result.rows}
            badges={result.badges}
            unmetCount={result.unmet_count}
            boundaryNotice={result.boundary_notice}
            expertReferral={result.expert_referral}
          />
        ) : (
          <p className="rounded-lg border border-dashed border-border px-4 py-8 text-center text-[12.5px] text-muted-foreground">
            아직 대조를 실행하지 않았습니다. &ldquo;판정례 대조 실행&rdquo;을 누르면 공개 기준과 회사 입력 상태를
            대조한 결과가 표시됩니다.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
