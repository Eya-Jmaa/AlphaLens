import React from "react";
import clsx from "clsx";

type Tone = "success" | "danger" | "warning" | "muted" | "primary";

const TONE_CLASSES: Record<Tone, string> = {
  success: "bg-success/15 text-success border-success/30",
  danger: "bg-danger/15 text-danger border-danger/30",
  warning: "bg-warning/15 text-warning border-warning/30",
  muted: "bg-muted text-muted-foreground border-border",
  primary: "bg-primary/15 text-primary border-primary/30",
};

export const Badge: React.FC<{ tone?: Tone; children: React.ReactNode; className?: string }> = ({
  tone = "muted",
  children,
  className,
}) => (
  <span
    className={clsx(
      "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
      TONE_CLASSES[tone],
      className
    )}
  >
    {children}
  </span>
);
