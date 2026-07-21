"use client";

// 케이스 접수 폼(CM-04) — POST /cases. 대화형 챗이 아니라 입력 폼이다(PRODUCT §3-1 결재사항).
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, createCase, type CaseCreateInput } from "@/lib/api";
import { exitReasonLabel, intakeRouteLabel } from "@/lib/labels";

const KIM_MINJUN_PRESET: CaseCreateInput = {
  subject_name: "김민준",
  subject_job: "개발",
  subject_rank: "시니어 책임",
  subject_role_title: "백엔드 개발자",
  exit_reason: "recommended_resignation",
  reason_text: "팀 개편에 따라 권고사직으로 처리하며, 통화가 어려워 문자로 통보함.",
  exit_date: "2026-08-06",
  intake_route: "groupware",
  profile_id: 1,
};

const EMPTY: CaseCreateInput = {
  subject_name: "",
  subject_job: "",
  subject_rank: "",
  subject_role_title: "",
  exit_reason: "voluntary",
  reason_text: "",
  exit_date: "",
  intake_route: "groupware",
  profile_id: undefined,
};

export default function NewCasePage() {
  const router = useRouter();
  const [form, setForm] = useState<CaseCreateInput>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof CaseCreateInput>(key: K, value: CaseCreateInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { data, meta } = await createCase(form);
      toast.success(meta?.toast ?? `${data.case.subject_name} 케이스가 등록되었습니다`);
      router.push(`/cases/${data.case.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("접수 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-[23px] font-extrabold tracking-[-0.5px]">케이스 접수</h1>
        <Button type="button" variant="outline" size="sm" onClick={() => setForm(KIM_MINJUN_PRESET)}>
          김민준 프리셋 채우기
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4 rounded-xl bg-card p-6 shadow-[var(--shadow-card)]">
        <div className="grid grid-cols-2 gap-4">
          <Field label="대상자 이름">
            <Input value={form.subject_name} onChange={(e) => set("subject_name", e.target.value)} required />
          </Field>
          <Field label="퇴사일">
            <Input type="date" value={form.exit_date} onChange={(e) => set("exit_date", e.target.value)} required />
          </Field>
          <Field label="직무">
            <Input value={form.subject_job} onChange={(e) => set("subject_job", e.target.value)} required />
          </Field>
          <Field label="직급">
            <Input value={form.subject_rank} onChange={(e) => set("subject_rank", e.target.value)} required />
          </Field>
        </div>

        <Field label="역할(선택)">
          <Input
            value={form.subject_role_title ?? ""}
            onChange={(e) => set("subject_role_title", e.target.value)}
          />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="퇴사 사유유형">
            <select
              value={form.exit_reason}
              onChange={(e) => set("exit_reason", e.target.value as CaseCreateInput["exit_reason"])}
              className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none"
            >
              {Object.entries(exitReasonLabel).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="접수 경로">
            <select
              value={form.intake_route}
              onChange={(e) => set("intake_route", e.target.value as CaseCreateInput["intake_route"])}
              className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none"
            >
              {Object.entries(intakeRouteLabel).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="회사 사유(선택) — AI가 공개 기준과 대조합니다">
          <Textarea
            value={form.reason_text ?? ""}
            onChange={(e) => set("reason_text", e.target.value)}
            rows={3}
          />
        </Field>

        <Field label="프로파일 ID(선택 — 레일 템플릿 적용, 시드 기본값 1=개발직·시니어 이상)">
          <Input
            type="number"
            value={form.profile_id ?? ""}
            onChange={(e) => set("profile_id", e.target.value ? Number(e.target.value) : undefined)}
          />
        </Field>

        {error && (
          <p className="rounded-lg bg-[var(--status-danger-soft)] px-3 py-2 text-[12.5px] font-medium text-[var(--status-danger)]">
            {error}
          </p>
        )}

        <Button type="submit" disabled={submitting} className="mt-2 shadow-[var(--shadow-glow)]">
          {submitting ? "접수 중..." : "케이스 접수"}
        </Button>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Label className="flex flex-col items-stretch gap-1.5 text-[12.5px] font-semibold text-foreground/80">
      {label}
      {children}
    </Label>
  );
}
