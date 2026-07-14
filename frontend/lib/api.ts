// 순수 fetch 래퍼. react-query/axios 금지 — API 계약이 아직 없으므로 최소로 유지.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error(`GET /health -> ${res.status}`);
  return res.json();
}
