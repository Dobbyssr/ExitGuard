// LB-04 판례대조 카드 — 뼈대만(api-spec §2-3 CompareResult shape). compare 엔진(task4) 병렬개발 중.
// 데이터는 스텁 — 실제 연동 시 이 컴포넌트에 rows/badges/boundary_notice props만 꽂으면 된다.
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExpertLink } from "@/components/expert-link";

const STUB_ROWS: { label: string }[] = [
  { label: "절차(procedure)" },
  { label: "기준(standard)" },
  { label: "리스크 알림(risk)" },
  { label: "상태(status)" },
  { label: "출처(source)" },
];

// ⚖️ §4 고정 경계문구 — compare/리포트 응답엔 boundary_notice가 필수(api-spec §1-7).
// 엔진 연동 전까지는 프론트에 동일 취지 문구를 고정 표기한다.
const BOUNDARY_NOTICE =
  "이 화면은 공개 기준과 회사 상태의 대조 결과만 보여줍니다. 법적 판단이 아니며, 최종 확인은 전문가 확인을 권장합니다.";

export function CompareStub() {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>기준 대조 (준비중)</CardTitle>
        <ExpertLink />
      </CardHeader>
      <CardContent className="flex flex-col gap-0 divide-y divide-border">
        {STUB_ROWS.map((row) => (
          <div key={row.label} className="flex items-center justify-between py-2.5 text-sm">
            <span className="text-muted-foreground">{row.label}</span>
            <span className="text-xs font-medium text-muted-foreground">대조 준비중</span>
          </div>
        ))}
        <p className="pt-3 text-xs leading-relaxed text-muted-foreground">{BOUNDARY_NOTICE}</p>
      </CardContent>
    </Card>
  );
}
