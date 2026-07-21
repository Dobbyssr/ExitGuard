"use client";

// 항목 드로어 + 상신/검토(CM-09/10) — POST /items/{id}/submit · POST /items/{id}/review.
// GET /items/{id}(승인이력 상세) 백엔드 미구현 — 케이스 상세에 이미 실린 item 데이터로 그린다.
import { useState } from "react";
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
import { ApiError, reviewItem, submitItem, type Item } from "@/lib/api";
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
