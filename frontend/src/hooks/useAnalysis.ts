import { useCallback, useRef, useState } from "react";
import toast from "react-hot-toast";
import { analyzeStream, ApiError } from "../api/client";
import { AnalysisResult } from "../types";
import { saveReportToHistory } from "../utils/reportHistory";

export interface AgentProgressStep {
  agent: string;
  errors: string[];
  warnings: string[];
  timestamp: number;
}

export function useAnalysis() {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<AgentProgressStep[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const runAnalysis = useCallback(async (query: string, debate = false) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress([]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await analyzeStream(
        query,
        (event) => {
          if (event.type === "agent_completed" && event.agent) {
            setProgress((prev) => [
              ...prev,
              { agent: event.agent!, errors: event.errors ?? [], warnings: event.warnings ?? [], timestamp: Date.now() },
            ]);
          } else if (event.type === "done" && event.result) {
            const finalResult = { ...event.result, generatedAt: new Date().toISOString() };
            setResult(finalResult);
            saveReportToHistory(finalResult);
          } else if (event.type === "error") {
            const message = event.message ?? "Analysis failed";
            setError(message);
            toast.error(message);
          }
        },
        controller.signal,
        debate
      );
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      const message = err instanceof ApiError ? err.message : "Could not reach the FinAgent backend.";
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
  }, []);

  const clearResults = useCallback(() => {
    setResult(null);
    setProgress([]);
    setError(null);
  }, []);

  return { isLoading, progress, result, error, runAnalysis, cancel, clearResults };
}
