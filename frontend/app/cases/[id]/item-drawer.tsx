"use client";

// 항목 드로어 + 상신/검토(CM-09/10) — POST /items/{id}/submit · POST /items/{id}/review.
// 이력·근거(CM-09)는 GET /items/{id} 실연결 — 드로어가 열릴 때 승인이력·basis를 따로 조회한다.
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { SourceBadge } from "@/components/source-badge";
import { ItemStatusBadge } from "@/components/item-status-badge";
import { ExpertLink } from "@/components/expert-link";
import { getItem, ApiError, reviewItem, submitItem, type Item, type ItemDetail } from "@/lib/api";
import { itemKindLabel } from "@/lib/labels";

export function ItemDrawer({
  item,
  onClose,
}: {
  item: Item | null;
  onClose: () => void;
}) {
  const router = useRouter();
  const [memo, setMemo] = useState("");
  const [signed, setSigned] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<ItemDetail | null>(null);

  // 드로어가 열릴 때(=item 바뀔 때)만 이력·근거를 따로 조회 — 목록 렌더엔 필요 없는 데이터라
  // 케이스 상세 응답에 얹지 않고 여기서만 fetch한다(불필요한 조기 로딩 방지).
  useEffect(() => {
    if (!item) return;
    let cancelled = false;
    getItem(item.id)
      .then(({ data }) => {
        if (!cancelled) setDetail(data);
      })
      .catch(() => {
        // 조회 실패 시 "이력 없음"으로 취급(빈 배열) — id로 로딩완료를 구분하기 위해 item을 그대로 씀.
        if (!cancelled) setDetail({ ...item, approvals: [], basis: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [item]);

  // 이전 항목의 이력이 다음 항목 렌더에 잠깐 새는 것을 막는 파생값(effect에서 setState하지 않음).
  const currentDetail = item && detail?.id === item.id ? detail : null;
  const detailLoading = !!item && !currentDetail;

  function reset() {
    setMemo("");
    setSigned(false);
    setRejecting(false);
  }

  function afterSuccess(toastMessage: string) {
    toast.success(toastMessage);
    reset();
    onClose();
    router.refresh();
  }

  async function handleSubmit() {
    if (!item) return;
    setBusy(true);
    try {
      await submitItem(item.id, { memo: memo || undefined, signed });
      afterSuccess(`${item.name} 상신을 완료했습니다`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "상신 중 오류가 발생했습니다");
    } finally {
      setBusy(false);
    }
  }

  async function handleReview(decision: "confirmed" | "rejected") {
    if (!item) return;
    setBusy(true);
    try {
      await reviewItem(item.id, { decision, memo: memo || undefined });
      afterSuccess(decision === "confirmed" ? `${item.name} 확인을 완료했습니다` : `${item.name}을 반려했습니다`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "검토 중 오류가 발생했습니다");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Sheet
      open={!!item}
      onOpenChange={(open) => {
        if (!open) {
          reset();
          onClose();
        }
      }}
    >
      <SheetContent className="w-full gap-0 overflow-y-auto sm:max-w-md">
        {item && (
          <>
            <SheetHeader>
              <SheetTitle>
                {item.code} · {item.name}
              </SheetTitle>
              <SheetDescription>
                {itemKindLabel[item.kind]} 항목{item.blocking ? " · 필수(게이트 반영)" : ""}
                {item.deadline ? ` · 법정 기한 ${item.deadline}` : ""}
              </SheetDescription>
            </SheetHeader>

            <div className="flex flex-col gap-4 px-4">
              <div className="flex items-center justify-between">
                <span className="text-[12px] font-semibold text-muted-foreground">현재 상태</span>
                <ItemStatusBadge status={item.status} />
              </div>

              {item.badges.length > 0 && (
                <div className="flex flex-col gap-2">
                  <span className="text-[12px] font-semibold text-muted-foreground">근거</span>
                  {item.badges.map((b, i) => (
                    <div key={i} className="flex items-center gap-2 text-[12px]">
                      <SourceBadge tier={b.tier} />
                      <span className="truncate">{b.title}</span>
                    </div>
                  ))}
                </div>
              )}

              {currentDetail && currentDetail.basis.length > 0 && (
                <div className="flex flex-col gap-2">
                  <span className="text-[12px] font-semibold text-muted-foreground">확인요건 근거</span>
                  {currentDetail.basis.map((b, i) => (
                    <div key={i} className="rounded-lg bg-[var(--soft)] px-3 py-2 text-[11.5px] leading-relaxed">
                      <p className="font-semibold">{b.title}</p>
                      {b.article && <p className="mt-0.5 text-muted-foreground">{b.article}</p>}
                      {b.body && <p className="mt-1 text-foreground/80">{b.body}</p>}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex flex-col gap-2">
                <span className="text-[12px] font-semibold text-muted-foreground">상신·검토 이력</span>
                {detailLoading && !currentDetail ? (
                  <p className="text-[11.5px] text-muted-foreground">불러오는 중...</p>
                ) : currentDetail && currentDetail.approvals.length > 0 ? (
                  <ul className="flex flex-col gap-2">
                    {currentDetail.approvals.map((a) => (
                      <li key={a.id} className="rounded-lg border border-border px-3 py-2 text-[11.5px]">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">담당자 #{a.submitter_id} 상신</span>
                          <span className="text-muted-foreground">
                            {new Date(a.submitted_at).toLocaleString("ko-KR")}
                          </span>
                        </div>
                        {a.memo && <p className="mt-1 text-foreground/80">{a.memo}</p>}
                        {a.decision && (
                          <p className="mt-1 text-muted-foreground">
                            검토자 #{a.reviewer_id} ·{" "}
                            {a.decision === "confirmed" ? "확인 완료" : "반려"}
                            {a.reviewed_at ? ` · ${new Date(a.reviewed_at).toLocaleString("ko-KR")}` : ""}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[11.5px] text-muted-foreground">아직 상신 이력이 없습니다.</p>
                )}
              </div>

              {item.blocking && item.status !== "approved" && item.status !== "not_applicable" && (
                <div className="flex items-center justify-between rounded-lg bg-[var(--status-danger-soft)] px-3 py-2">
                  <span className="text-[12px] font-medium text-[var(--status-danger)]">
                    기준 대비 미충족 항목입니다
                  </span>
                  <ExpertLink />
                </div>
              )}

              {(item.status === "pending" || item.status === "rejected") && (
                <div className="flex flex-col gap-2">
                  <Label className="text-[12.5px] font-semibold">상신 메모</Label>
                  <Textarea value={memo} onChange={(e) => setMemo(e.target.value)} rows={3} />
                  <label className="flex items-center gap-2 text-[12px] text-muted-foreground">
                    <input type="checkbox" checked={signed} onChange={(e) => setSigned(e.target.checked)} />
                    전자서명 확인함
                  </label>
                </div>
              )}

              {item.status === "submitted" && (
                <div className="flex flex-col gap-2">
                  <Label className="text-[12.5px] font-semibold">
                    {rejecting ? "반려 사유" : "검토 메모(선택)"}
                  </Label>
                  <Textarea value={memo} onChange={(e) => setMemo(e.target.value)} rows={3} />
                </div>
              )}
            </div>

            <SheetFooter>
              {(item.status === "pending" || item.status === "rejected") && (
                <Button onClick={handleSubmit} disabled={busy} className="shadow-[var(--shadow-glow)]">
                  {busy ? "상신 중..." : "상신"}
                </Button>
              )}
              {item.status === "submitted" && !rejecting && (
                <div className="flex gap-2">
                  <Button onClick={() => handleReview("confirmed")} disabled={busy} className="flex-1">
                    확인
                  </Button>
                  <Button variant="outline" onClick={() => setRejecting(true)} disabled={busy} className="flex-1">
                    반려
                  </Button>
                </div>
              )}
              {item.status === "submitted" && rejecting && (
                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    onClick={() => handleReview("rejected")}
                    disabled={busy}
                    className="flex-1"
                  >
                    {busy ? "처리 중..." : "반려 확정"}
                  </Button>
                  <Button variant="ghost" onClick={() => setRejecting(false)} className="flex-1">
                    취소
                  </Button>
                </div>
              )}
              {(item.status === "approved" || item.status === "not_applicable") && (
                <p className="w-full text-center text-[12px] text-muted-foreground">
                  이 항목은 더 이상 처리할 작업이 없습니다.
                </p>
              )}
            </SheetFooter>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
