// ExitGuard 백엔드(FastAPI) 연동 — 순수 fetch 래퍼.
// react-query 등 데이터 라이브러리 금지(ponytail) — 화면 수·호출 수가 적어 과함.
// 계약 SSOT: docs/spec/api-spec.md. 필드·엔드포인트를 여기서 창작하지 않는다.

const BACKEND_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

// 서버 컴포넌트(Node)는 상대경로 fetch가 안 되니 백엔드 절대 URL로 직접 호출한다(서버-서버라 CORS 무관).
// 브라우저(클라이언트 컴포넌트)는 동일 출처 상대경로로 호출 — next.config.ts의 rewrite가
// 백엔드로 프록시해준다. dev 서버가 어느 포트에 뜨든 CORS에 걸리지 않는다.
function apiBase() {
  return typeof window === "undefined" ? BACKEND_BASE : "/api/v1";
}

// ---- 공용 shape (api-spec §1) -------------------------------------------

export type Meta = {
  pagination?: { page: number; size: number; total: number; total_pages: number } | null;
  toast?: string | null;
  seal_status?: string | null;
  total_count?: number | null;
  last_sealed_at?: string | null;
  head_hash?: string | null;
};

export type Envelope<T> = { data: T; meta?: Meta | null };

export type ApiErrorBody = {
  code: string;
  message: string;
  fields?: Record<string, unknown> | null;
};

/** 백엔드 {"error":{code,message,fields}} 계약을 그대로 실어 나르는 예외. */
export class ApiError extends Error {
  code: string;
  fields?: Record<string, unknown> | null;
  status: number;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.status = status;
    this.code = body.code;
    this.fields = body.fields;
  }
}

// ---- 도메인 타입 (data-model 필드 그대로 — 창작 금지) ----------------------

export type Rail = "labor" | "trade_secret" | "security";
export type ItemStatus = "pending" | "submitted" | "approved" | "rejected" | "not_applicable";
export type ItemKind = "statutory" | "internal" | "recommended";
export type CaseStatus = "in_progress" | "review_waiting" | "completed";
export type ExitReason = "voluntary" | "recommended_resignation" | "dismissal" | "contract_expiry";
export type IntakeRoute = "groupware" | "dismissal" | "resignation";
export type StandardTier = "L1" | "L2" | "L3";

export type Badge = { tier: StandardTier; title: string; url?: string | null; version: string };

export type Item = {
  id: number;
  case_id: number;
  rail: Rail;
  code: string;
  name: string;
  kind: ItemKind;
  status: ItemStatus;
  blocking: boolean;
  sub: string | null;
  deadline: string | null;
  detail: Record<string, unknown> | null;
  badges: Badge[];
};

export type Gate = {
  case_id: number;
  rail_completion: Record<Rail, number>;
  overall_completion: number;
  risk_count: number;
  defensible: boolean;
};

export type RailSummary = { rail: Rail; completion: number; items: Item[] };

export type Case = {
  id: number;
  subject_name: string;
  subject_job: string;
  subject_rank: string;
  subject_role_title: string | null;
  exit_reason: ExitReason;
  reason_text: string | null;
  exit_date: string;
  intake_route: IntakeRoute;
  profile_id: number | null;
  status: CaseStatus;
  created_by: number;
  created_at: string;
  updated_at: string;
};

export type CaseSummary = {
  id: number;
  subject_name: string;
  subject_job: string;
  subject_rank: string;
  exit_reason: ExitReason;
  exit_date: string;
  status: CaseStatus;
  overall_completion: number;
  risk_count: number;
  dday: number;
};

export type CaseDetail = {
  case: Case;
  gate: Gate;
  rails: Record<string, RailSummary>;
  items: Item[];
};

export type Approval = {
  id: number;
  item_id: number;
  submitter_id: number;
  memo: string | null;
  attachments: Record<string, unknown>[] | null;
  signed: boolean;
  basis_note: string | null;
  reviewer_id: number | null;
  decision: "confirmed" | "rejected" | null;
  reviewed_at: string | null;
  submitted_at: string;
};

export type EvidenceEventType =
  | "item_submitted"
  | "item_confirmed"
  | "item_rejected"
  | "compare_recorded"
  | "recovery_confirmed"
  | "case_approved";

export type Evidence = {
  id: number;
  case_id: number;
  seq: number;
  occurred_at: string;
  actor: string;
  action: string;
  event_type: EvidenceEventType;
  origin: "auto" | "manual";
  document_ref: string | null;
  payload: Record<string, unknown>;
  integrity_hash: string;
  prev_hash: string | null;
  sealed_at: string;
};

// ---- fetch 코어 -----------------------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<Envelope<T>> {
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    // api-spec §1-3 계약: {"error":{code,message,fields}}.
    // FastAPI 기본 422(RequestValidationError)는 이 envelope를 안 타므로 폴백 처리.
    const errBody: ApiErrorBody = body?.error ?? {
      code: "UNKNOWN",
      message: body?.detail ? String(body.detail) : `요청 실패(HTTP ${res.status})`,
      fields: null,
    };
    throw new ApiError(res.status, errBody);
  }
  return body as Envelope<T>;
}

// ---- 케이스 (api-spec §2-1) ------------------------------------------------

export type CaseListFilter = "all" | "in_progress" | "review_waiting" | "completed";

export async function listCases(params: {
  filter?: CaseListFilter;
  q?: string;
  sort?: string;
} = {}): Promise<Envelope<CaseSummary[]>> {
  const qs = new URLSearchParams();
  qs.set("filter", params.filter ?? "all");
  if (params.q) qs.set("q", params.q);
  if (params.sort) qs.set("sort", params.sort);
  return request<CaseSummary[]>(`/cases?${qs.toString()}`);
}

export type CaseCreateInput = {
  subject_name: string;
  subject_job: string;
  subject_rank: string;
  subject_role_title?: string | null;
  exit_reason: ExitReason;
  reason_text?: string | null;
  exit_date: string;
  intake_route: IntakeRoute;
  profile_id?: number | null;
};

export async function createCase(payload: CaseCreateInput): Promise<Envelope<CaseDetail>> {
  return request<CaseDetail>("/cases", { method: "POST", body: JSON.stringify(payload) });
}

export async function getCase(id: number): Promise<Envelope<CaseDetail>> {
  return request<CaseDetail>(`/cases/${id}`);
}

export async function getGate(id: number): Promise<Envelope<Gate>> {
  return request<Gate>(`/cases/${id}/gate`);
}

export async function approveCase(
  id: number,
  memo?: string
): Promise<Envelope<{ case: Case; evidence: Evidence }>> {
  return request(`/cases/${id}/approve`, {
    method: "POST",
    body: JSON.stringify(memo ? { memo } : {}),
  });
}

// ---- 항목 · 상신-검토 (api-spec §2-4) ---------------------------------------

export async function submitItem(
  itemId: number,
  payload: { memo?: string; signed?: boolean }
): Promise<Envelope<Approval>> {
  return request<Approval>(`/items/${itemId}/submit`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reviewItem(
  itemId: number,
  payload: { decision: "confirmed" | "rejected"; memo?: string }
): Promise<Envelope<Approval>> {
  return request<Approval>(`/items/${itemId}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---- 증적 (api-spec §2-5) --------------------------------------------------

export async function getEvidence(caseId: number): Promise<Envelope<Evidence[]>> {
  return request<Evidence[]>(`/cases/${caseId}/evidence`);
}
