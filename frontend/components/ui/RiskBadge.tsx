import { ShieldCheck, ShieldAlert, ShieldX, Siren } from "lucide-react";
import type { RiskLevel, Urgency } from "@/lib/api";
import clsx from "clsx";

interface Props {
  riskLevel: RiskLevel;
  urgency: Urgency;
}

const CONFIG = {
  low: {
    label: "Low Risk",
    icon: ShieldCheck,
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/25",
    text: "text-emerald-400",
    dot: "bg-emerald-400",
  },
  medium: {
    label: "Medium Risk",
    icon: ShieldAlert,
    bg: "bg-amber-500/10",
    border: "border-amber-500/25",
    text: "text-amber-400",
    dot: "bg-amber-400",
  },
  high: {
    label: "High Risk",
    icon: ShieldX,
    bg: "bg-red-500/10",
    border: "border-red-500/25",
    text: "text-red-400",
    dot: "bg-red-400",
  },
};

export function RiskBadge({ riskLevel, urgency }: Props) {
  const isEmergency = urgency === "emergency";
  const cfg = CONFIG[riskLevel];
  const Icon = cfg.icon;

  if (isEmergency) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/20 border border-red-500/40 text-red-300 glow-emergency">
        <Siren className="w-3.5 h-3.5" />
        EMERGENCY
      </span>
    );
  }

  return (
    <span className={clsx(
      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
      cfg.bg, cfg.border, cfg.text
    )}>
      <span className={clsx("w-1.5 h-1.5 rounded-full", cfg.dot)} />
      {cfg.label}
    </span>
  );
}
