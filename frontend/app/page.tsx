import { redirect } from "next/navigation";

// 루트는 케이스 목록(CM-03)으로 — 세로절단 시나리오의 시작점.
export default function Home() {
  redirect("/cases");
}
