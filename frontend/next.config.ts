import type { NextConfig } from "next";
import path from "node:path";

const BACKEND_ORIGIN = (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1").replace(
  /\/api\/v1\/?$/,
  ""
);

const nextConfig: NextConfig = {
  // 모노레포 루트로 확장 — app/globals.css가 ../../docs/design/tokens.css(루나 SSOT)를 @import 하기 위함.
  turbopack: {
    root: path.join(__dirname, ".."),
  },
  // 브라우저(클라이언트 컴포넌트)의 상신/검토/승인 fetch를 동일 출처로 프록시한다.
  // 백엔드 CORS가 특정 포트(localhost:3000)만 허용하는데, dev 서버가 포트 충돌로
  // 다른 포트에 뜨면 클라이언트 fetch가 막힌다 — 프록시로 원천 회피(rung 4: 프레임워크 기본기).
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${BACKEND_ORIGIN}/api/v1/:path*` }];
  },
};

export default nextConfig;
