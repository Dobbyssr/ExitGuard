// [전문가 연결] — 판단이 필요한 분기마다 세우는 상시 버튼(PRODUCT §4 · harry.md).
// 실제 노무법인 제휴 연동은 상용화 단계(§4) — MVP는 mailto: 링크로 "판단 주체=전문가,
// 우리=도구" 구조만 UI로 못박는다(백엔드/새 라우트 불필요 — 네이티브 mailto로 충분, ponytail).
import { Button } from "@/components/ui/button";
import { Users } from "lucide-react";
import { cn } from "@/lib/utils";

export function ExpertLink({ className, label = "전문가 연결" }: { className?: string; label?: string }) {
  return (
    <Button
      variant="outline"
      size="sm"
      nativeButton={false}
      className={cn("gap-1.5", className)}
      render={
        <a href="mailto:expert@exitguard.example?subject=ExitGuard%20전문가%20확인%20요청" />
      }
    >
      <Users className="size-3.5" />
      {label}
    </Button>
  );
}
