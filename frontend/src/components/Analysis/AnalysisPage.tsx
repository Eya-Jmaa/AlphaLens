import React, { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { X, RefreshCw } from "lucide-react";
import { QueryInput } from "./QueryInput";
import { AgentTrace, AgentTraceSkeleton } from "./AgentTrace";
import { AgentGraph } from "./AgentGraph";
import { ReportView } from "./ReportView";
import { useAnalysis } from "../../hooks/useAnalysis";
import { usePageMeta } from "../Layout/AppShell";

const EXAMPLES = [
  "Analyze NVIDIA fundamental valuation, news sentiment, and SEC risk factors",
  "Compare AAPL, MSFT, and GOOGL balance sheet strength and multiples",
  "What are the principal risk factors in Tesla's latest 10-K SEC filing?",
  "Stress-test portfolio with AAPL 30%, MSFT 30%, NVDA 40% against drawdown",
];

export const AnalysisPage: React.FC = () => {
  usePageMeta({ title: "Equity Research Desk", subtitle: "Autonomous Fundamental, SEC & Risk Ingestion" });
  const { isLoading, progress, result, error, runAnalysis, cancel, clearResults } = useAnalysis();

  const location = useLocation();
  const prefillQuery = (location.state as { query?: string } | null)?.query;
  const autoRunRef = useRef(false);

  useEffect(() => {
    if (prefillQuery && !autoRunRef.current) {
      autoRunRef.current = true;
      runAnalysis(prefillQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillQuery]);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Research Command Launcher */}
      <QueryInput onSubmit={runAnalysis} isLoading={isLoading} examples={EXAMPLES} initialValue={prefillQuery} />

      {/* Live Pipeline Execution State */}
      {isLoading && (
        <div className="space-y-4">
          <AgentTraceSkeleton />
          <AgentGraph steps={progress} isLoading={isLoading} />
          <AgentTrace steps={progress} isLoading={isLoading} />
          <div className="flex justify-center">
            <button
              onClick={cancel}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-border bg-card text-xs font-mono text-muted-foreground hover:text-danger hover:border-danger/40 transition shadow-sm"
            >
              <X size={13} /> Abort Execution
            </button>
          </div>
        </div>
      )}

      {/* Execution Error State */}
      {!isLoading && error && !result && (
        <div className="bg-danger/10 border border-danger/30 rounded p-6 text-center space-y-2">
          <p className="text-sm font-bold text-danger font-mono uppercase tracking-wide">
            Execution Interrupted
          </p>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">{error}</p>
          <button
            onClick={() => clearResults()}
            className="mt-2 inline-flex items-center gap-1.5 text-xs text-foreground underline font-mono"
          >
            Reset Command Terminal
          </button>
        </div>
      )}

      {/* Completed Pipeline Trace (Foldable/Visible before report) */}
      {!isLoading && progress.length > 0 && result && (
        <details className="bg-card border border-border rounded p-4 shadow-sm group">
          <summary className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground cursor-pointer select-none flex items-center justify-between hover:text-foreground">
            <span>Execution Telemetry &middot; {progress.length} Desks Verified</span>
            <span className="text-[10px] text-primary">Click to Toggle</span>
          </summary>
          <div className="mt-4 space-y-4 pt-3 border-t border-border/60">
            <AgentGraph steps={progress} isLoading={false} />
            <AgentTrace steps={progress} isLoading={false} />
          </div>
        </details>
      )}

      {/* Primary Executive Equity Research Dossier */}
      {result && (
        <div className="space-y-6">
          <ReportView result={result} />
          <div className="flex justify-center pb-8">
            <button
              onClick={clearResults}
              className="inline-flex items-center gap-2 px-4 py-2 rounded border border-border bg-card text-xs font-mono font-semibold text-muted-foreground hover:text-foreground hover:bg-elevated transition shadow-sm"
            >
              <RefreshCw size={13} /> Start New Research Directive
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
