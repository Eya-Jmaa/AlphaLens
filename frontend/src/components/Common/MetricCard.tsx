import React from "react";
import clsx from "clsx";

type Props = {
  label: string;
  value: string;
  hint?: string;
  tone?: "success" | "danger" | "warning" | "default";
};

const TONE_TEXT: Record<NonNullable<Props["tone"]>, string> = {
  success: "text-emerald-600 dark:text-emerald-400",
  danger: "text-rose-600 dark:text-rose-400",
  warning: "text-amber-600 dark:text-amber-400",
  default: "text-foreground",
};

export const MetricCard: React.FC<Props> = ({ label, value, hint, tone = "default" }) => (
  <div className="bg-background-secondary/60 p-4 rounded-2xl border border-border/60">
    <div className="text-xs font-semibold text-muted-foreground">{label}</div>
    <div className={clsx("mt-1.5 text-xl font-extrabold tracking-tight font-tabular", TONE_TEXT[tone])}>
      {value}
    </div>
    {hint && <div className="text-[11px] text-muted-foreground mt-1">{hint}</div>}
  </div>
);
