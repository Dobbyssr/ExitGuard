// 통합 게이트 도넛 — overall_completion(%) 시각화. 차트 라이브러리 불필요, SVG 1개로 충분(ponytail).
export function GateDonut({ percent, size = 96 }: { percent: number; size?: number }) {
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, percent));
  const dash = (clamped / 100) * c;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--soft)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--eg-3)"
          strokeWidth={stroke}
          strokeDasharray={`${dash} ${c - dash}`}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 200ms ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[22px] font-extrabold tracking-[-0.5px] text-foreground">{clamped}%</span>
      </div>
    </div>
  );
}
