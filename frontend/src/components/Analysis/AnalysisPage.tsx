import React, { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { X } from "lucide-react";
import { QueryInput } from "./QueryInput";
import { AgentTrace, AgentTraceSkeleton } from "./AgentTrace";
import { ReportView } from "./ReportView";
import { useAnalysis } from "../../hooks/useAnalysis";
import { usePageMeta } from "../Layout/AppShell";

const EXAMPLES = [
  "Analyze NVIDIA including news and risk",
  "Compare AAPL, MSFT, and GOOGL",
  "What are Tesla's biggest risks?",
  "What are the biggest risks in Apple's latest 10-K filing?",
];

export const AnalysisPage: React.FC = () => {
  usePageMeta({ title: "Analysis", subtitle: "Ask about a company, sector, or portfolio" });
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
    <div className="max-w-4xl mx-auto space-y-6">
      <QueryInput onSubmit={runAnalysis} isLoading={isLoading} examples={EXAMPLES} initialValue={prefillQuery} />

      {isLoading && (
        <div className="space-y-3">
          <AgentTraceSkeleton />
          <AgentTrace steps={progress} isLoading={isLoading} />
          <button
            onClick={cancel}
            className="mx-auto flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition"
          >
            <X size={13} /> Cancel
          </button>
        </div>
      )}

      {!isLoading && error && !result && (
        <div className="bg-danger/10 border border-danger/30 rounded-xl p-6 text-center">
          <p className="text-sm font-medium text-danger">Analysis failed</p>
          <p className="text-xs text-muted-foreground mt-1">{error}</p>
        </div>
      )}

      {!isLoading && progress.length > 0 && result && <AgentTrace steps={progress} isLoading={false} />}

      {result && (
        <>
          <ReportView result={result} />
          <div className="text-center">
            <button onClick={clearResults} className="text-sm text-muted-foreground hover:text-foreground transition">
              Clear &amp; start a new analysis
            </button>
          </div>
        </>
      )}
    </div>
  );
};
