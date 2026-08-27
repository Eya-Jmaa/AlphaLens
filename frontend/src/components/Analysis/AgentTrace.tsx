import React from "react";
import { CheckCircle2, Loader2, CircleDashed, AlertTriangle } from "lucide-react";
import clsx from "clsx";
import { AGENT_LABELS } from "../../types";
import { AgentProgressStep } from "../../hooks/useAnalysis";

type Props = {
  steps: AgentProgressStep[];
  isLoading: boolean;
};

/** Live trace of which agents have run, in completion order, while the workflow streams. */
export const AgentTrace: React.FC<Props> = ({ steps, isLoading }) => {
  if (steps.length === 0 && !isLoading) return null;

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <div className="text-sm font-semibold mb-3">Agent Execution</div>
      <ol className="space-y-2.5">
        {steps.map((step, i) => {
          const hasError = step.errors.length > 0;
          const hasWarning = step.warnings.length > 0;
          return (
            <li key={`${step.agent}-${i}`} className="flex items-start gap-2.5 text-sm">
              {hasError ? (
                <AlertTriangle size={16} className="text-danger mt-0.5 shrink-0" />
              ) : (
                <CheckCircle2 size={16} className="text-success mt-0.5 shrink-0" />
              )}
              <div className="min-w-0">
                <span className="font-medium">{AGENT_LABELS[step.agent] ?? step.agent}</span>
                <span className="text-muted-foreground"> completed</span>
                {hasError && (
                  <div className="text-xs text-danger mt-0.5">{step.errors.join(", ")}</div>
                )}
                {!hasError && hasWarning && (
                  <div className="text-xs text-warning mt-0.5">{step.warnings.join(", ")}</div>
                )}
              </div>
            </li>
          );
        })}
        {isLoading && (
          <li className="flex items-center gap-2.5 text-sm text-muted-foreground">
            <Loader2 size={16} className="animate-spin shrink-0" />
            Working...
          </li>
        )}
      </ol>
    </div>
  );
};

export const AgentTraceSkeleton: React.FC = () => (
  <div className="bg-card border border-border rounded-xl p-5">
    <div className="text-sm font-semibold mb-3 flex items-center gap-2">
      <CircleDashed size={16} className={clsx("animate-spin text-muted-foreground")} />
      FinAgent is working on your request...
    </div>
    <p className="text-xs text-muted-foreground">
      The supervisor is routing your query to the relevant specialized agents. This can take up to a
      minute for multi-agent queries (news, risk, and SEC filings each involve real data lookups and an
      LLM call).
    </p>
  </div>
);
