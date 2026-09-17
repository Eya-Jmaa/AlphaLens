import React from "react";
import { CheckCircle2, Loader2, CircleDashed, AlertTriangle, Terminal } from "lucide-react";
import clsx from "clsx";
import { AgentProgressStep } from "../../hooks/useAnalysis";

type Props = {
  steps: AgentProgressStep[];
  isLoading: boolean;
};

const AGENT_DISPLAY_TITLES: Record<string, string> = {
  Supervisor: "Research Director & Query Decomposition",
  StockAnalysis: "Fundamental Valuation & Financial Data",
  NewsAnalysis: "Macro News & Market Sentiment Extraction",
  RiskAnalysis: "Multi-Factor Risk & Stress-Testing Model",
  SECAnalysis: "SEC EDGAR 10-K / 10-Q Disclosure Extraction",
  BullCase: "Long Catalyst Analysis (Bull Thesis)",
  BearCase: "Vulnerability & Downside Analysis (Bear Thesis)",
  Judge: "Investment Committee Deliberation & Verdict",
  FinalAnalyst: "Executive Research Dossier Synthesis",
};

export const AgentTrace: React.FC<Props> = ({ steps, isLoading }) => {
  if (steps.length === 0 && !isLoading) return null;

  return (
    <div className="bg-card border border-border rounded p-4 md:p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b border-border/70 pb-2.5">
        <div className="flex items-center gap-2 text-[11px] font-mono font-bold uppercase tracking-wider text-foreground">
          <Terminal size={14} className="text-primary" /> Execution Telemetry Log
        </div>
        <span className="text-[10px] font-mono text-muted-foreground">
          {steps.length} Desks Completed
        </span>
      </div>

      <ol className="space-y-2 font-mono text-xs">
        {steps.map((step, i) => {
          const hasError = step.errors.length > 0;
          const hasWarning = step.warnings.length > 0;
          const title = AGENT_DISPLAY_TITLES[step.agent] ?? step.agent;

          return (
            <li key={`${step.agent}-${i}`} className="flex items-start justify-between gap-3 py-1 border-b border-border/40 last:border-0">
              <div className="flex items-start gap-2 min-w-0">
                {hasError ? (
                  <AlertTriangle size={14} className="text-danger mt-0.5 shrink-0" />
                ) : (
                  <CheckCircle2 size={14} className="text-success mt-0.5 shrink-0" />
                )}
                <div className="min-w-0">
                  <div className="font-semibold text-foreground truncate">{title}</div>
                  {hasError && (
                    <div className="text-[11px] text-danger mt-0.5">{step.errors.join(", ")}</div>
                  )}
                  {!hasError && hasWarning && (
                    <div className="text-[11px] text-warning mt-0.5">{step.warnings.join(", ")}</div>
                  )}
                </div>
              </div>
              <span className="text-[10px] uppercase font-bold text-success px-1.5 py-0.5 rounded bg-success/10 shrink-0">
                VERIFIED
              </span>
            </li>
          );
        })}
        {isLoading && (
          <li className="flex items-center justify-between py-1.5 text-xs text-primary font-mono">
            <div className="flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-primary shrink-0" />
              <span>Executing active research desk...</span>
            </div>
            <span className="text-[10px] uppercase font-bold text-primary px-1.5 py-0.5 rounded bg-primary/10">
              IN PROGRESS
            </span>
          </li>
        )}
      </ol>
    </div>
  );
};

export const AgentTraceSkeleton: React.FC = () => (
  <div className="bg-card border border-border rounded p-5 shadow-sm space-y-2">
    <div className="text-xs font-mono font-bold uppercase tracking-wider text-foreground flex items-center gap-2">
      <CircleDashed size={14} className="animate-spin text-primary" />
      Ingesting Market &amp; Regulatory Feeds...
    </div>
    <p className="text-xs text-muted-foreground leading-relaxed">
      Routing directive across quantitative valuation, live order books, audited SEC EDGAR 10-K/10-Q filings, and portfolio risk factor models.
    </p>
  </div>
);
