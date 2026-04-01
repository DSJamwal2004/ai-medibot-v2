import clsx from "clsx";

interface Props {
  score: number; // 0–1
  label?: string;
  size?: "sm" | "md";
}

export function ConfidenceBar({ score, label, size = "md" }: Props) {
  const pct = Math.round(score * 100);

  const color =
    pct >= 70 ? "bg-emerald-500" :
    pct >= 45 ? "bg-amber-500" :
    "bg-slate-500";

  return (
    <div className={clsx("flex items-center gap-2", size === "sm" ? "text-xs" : "text-sm")}>
      {label && <span className="text-slate-400 shrink-0">{label}</span>}
      <div className="flex-1 h-1.5 rounded-full bg-[#1e2535] overflow-hidden">
        <div
          className={clsx("h-full rounded-full transition-all duration-700 ease-out", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-slate-400 tabular-nums shrink-0 font-mono text-xs">{pct}%</span>
    </div>
  );
}
