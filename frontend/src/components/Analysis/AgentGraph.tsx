import React from "react";
import { Check, AlertTriangle, Loader2 } from "lucide-react";
import clsx from "clsx";
import { AgentProgressStep } from "../../hooks/useAnalysis";

type NodeState = "pending" | "running" | "complete" | "failed";

const DESK_NAMES: Record<string, { label: string; desk: string }> = {
  Supervisor: { label: "Research Director", desk: "Orchestration" },
  StockAnalysis: { label: "Fundamental Valuation", desk: "Multiples & DCF" },
  NewsAnalysis: { label: "Market Sentiment", desk: "Macro & News" },
  RiskAnalysis: { label: "Factor Risk Engine", desk: "VaR & Stress" },
  SECAnalysis: { label: "SEC EDGAR Audit", desk: "10-K/10-Q" },
  BullCase: { label: "Long Analyst Desk", desk: "Upside Catalysts" },
  BearCase: { label: "Short Analyst Desk", desk: "Downside Risks" },
  Judge: { label: "Investment Committee", desk: "Conviction" },
  FinalAnalyst: { label: "Executive Synthesis", desk: "Final Dossier" },
};

const NodeBadge: React.FC<{ name: string; state: NodeState }> = ({ name, state }) => {
  const info = DESK_NAMES[name] ?? { label: name, desk: "Desk" };

  return (
    <div
      className={clsx(
        "flex flex-col gap-0.5 px-4 py-2 rounded-2xl border text-left transition-all min-w-[140px] shadow-sm",
        state === "complete" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
        state === "failed" && "border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-400",
        state === "running" && "border-slate-800 bg-slate-100 dark:border-white dark:bg-slate-800 text-foreground animate-pulse",
        state === "pending" && "border-border/60 bg-background/50 text-muted-foreground opacity-60"
      )}
    >
      <div className="flex items-center justify-between text-[10px] uppercase font-bold text-muted-foreground">
        <span>{info.desk}</span>
        {state === "complete" && <Check size={12} className="text-emerald-600" />}
        {state === "failed" && <AlertTriangle size={12} className="text-rose-600" />}
        {state === "running" && <Loader2 size={12} className="animate-spin text-foreground" />}
        {state === "pending" && <span className="w-1.5 h-1.5 rounded-full bg-border" />}
      </div>
      <div className="text-xs font-bold truncate text-foreground">{info.label}</div>
    </div>
  );
};

export const AgentGraph: React.FC<{ steps: AgentProgressStep[]; isLoading: boolean }> = ({ steps, isLoading }) => {
  if (steps.length === 0 && !isLoading) return null;

  const finalAnalystStep = steps.find((s) => s.agent === "FinalAnalyst");
  const branchSteps = steps.filter((s) => s.agent !== "FinalAnalyst" && s.agent !== "Supervisor");

  const supervisorState: NodeState = steps.length > 0 || isLoading ? "complete" : "pending";
  const finalState: NodeState = finalAnalystStep
    ? finalAnalystStep.errors.length > 0
      ? "failed"
      : "complete"
    : isLoading
    ? "running"
    : "pending";

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-foreground animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-wider text-foreground">
            Quantitative Execution Pipeline
          </span>
        </div>
        <span className="text-xs text-muted-foreground font-semibold">
          {isLoading ? "Executing Desks..." : "Pipeline Verified"}
        </span>
      </div>

      <div className="flex flex-col items-center gap-2.5">
        <NodeBadge name="Supervisor" state={supervisorState} />

        <div className="w-px h-3 bg-border" />

        <div className="flex flex-wrap items-center justify-center gap-2.5 max-w-3xl">
          {branchSteps.length === 0 && isLoading && (
            <NodeBadge name="StockAnalysis" state="running" />
          )}
          {branchSteps.map((step, i) => (
            <NodeBadge
              key={`${step.agent}-${i}`}
              name={step.agent}
              state={step.errors.length > 0 ? "failed" : "complete"}
            />
          ))}
        </div>

        <div className="w-px h-3 bg-border" />

        <NodeBadge name="FinalAnalyst" state={finalState} />
      </div>
    </div>
  );
};
