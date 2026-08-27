import React from "react";
import clsx from "clsx";

type Props = {
  label: string;
  value: string;
  hint?: string;
  tone?: "success" | "danger" | "warning" | "default";
};

const TONE_TEXT: Record<NonNullable<Props["tone"]>, string> = {
  success: "text-success",
  danger: "text-danger",
  warning: "text-warning",
  default: "text-foreground",
};

export const MetricCard: React.FC<Props> = ({ label, value, hint, tone = "default" }) => (
  <div className="bg-card p-4 rounded-lg border border-border">
    <div className="text-xs font-medium text-muted-foreground">{label}</div>
    <div className={clsx("mt-1.5 text-xl font-semibold tabular-nums", TONE_TEXT[tone])}>{value}</div>
    {hint && <div className="text-[11px] text-muted-foreground mt-1">{hint}</div>}
  </div>
);
