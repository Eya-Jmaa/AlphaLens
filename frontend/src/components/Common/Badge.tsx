import React from "react";
import clsx from "clsx";

type Tone = "success" | "danger" | "warning" | "muted" | "primary" | "info";

const TONE_CLASSES: Record<Tone, string> = {
  success: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800",
  danger: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800",
  warning: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800",
  muted: "bg-background-secondary text-muted-foreground border-border/80",
  primary: "bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-transparent shadow-sm",
  info: "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-400 dark:border-sky-800",
};

export const Badge: React.FC<{ tone?: Tone; children: React.ReactNode; className?: string }> = ({
  tone = "muted",
  children,
  className,
}) => (
  <span
    className={clsx(
      "inline-flex items-center gap-1 rounded-full border px-3 py-0.5 text-xs font-bold tracking-tight whitespace-nowrap shadow-sm",
      TONE_CLASSES[tone],
      className
    )}
  >
    {children}
  </span>
);
