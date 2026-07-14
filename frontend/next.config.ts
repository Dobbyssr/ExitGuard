import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // 모노레포 루트로 확장 — app/globals.css가 ../../docs/design/tokens.css(루나 SSOT)를 @import 하기 위함.
  turbopack: {
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
