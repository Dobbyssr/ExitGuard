"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getHealth, type HealthResponse } from "@/lib/api";

type ConnState =
  | { status: "loading" }
  | { status: "ok"; data: HealthResponse }
  | { status: "error"; message: string };

export default function Home() {
  const [conn, setConn] = useState<ConnState>({ status: "loading" });

  useEffect(() => {
    getHealth()
      .then((data) => setConn({ status: "ok", data }))
      .catch((err) => setConn({ status: "error", message: String(err) }));
  }, []);

  return (
    <div className="flex flex-1 items-center justify-center bg-background p-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>ExitGuard — 백엔드 연결 확인</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">GET /health</span>
            {conn.status === "loading" && <Badge variant="secondary">확인 중</Badge>}
            {conn.status === "ok" && (
              <Badge className="bg-[var(--status-ok)] text-white">연결됨</Badge>
            )}
            {conn.status === "error" && (
              <Badge variant="destructive">연결 실패</Badge>
            )}
          </div>
          <pre className="rounded-md bg-muted p-3 text-xs text-muted-foreground overflow-x-auto">
            {conn.status === "ok" && JSON.stringify(conn.data, null, 2)}
            {conn.status === "error" && conn.message}
            {conn.status === "loading" && "요청 중..."}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
