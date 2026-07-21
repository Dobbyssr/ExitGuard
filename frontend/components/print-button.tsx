"use client";

// 리포트 인쇄/PDF 저장 — 백엔드 format=pdf는 미구현(501)이라 브라우저 print로 대체한다
// (ponytail: 서버 PDF 렌더링 새로 붙이지 않는다 — 네이티브 print CSS로 충분).
import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";

export function PrintButton() {
  return (
    <Button variant="outline" size="sm" className="gap-1.5" onClick={() => window.print()}>
      <Printer className="size-3.5" />
      리포트 인쇄 / PDF 저장
    </Button>
  );
}
