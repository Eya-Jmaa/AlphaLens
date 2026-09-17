import { AnalysisResult } from "../types";

const STORAGE_KEY = "alphalens:report-history";
const MAX_ENTRIES = 25;

export interface ReportHistoryEntry {
  id: string;
  query: string;
  tickers: string[];
  outlook: string;
  generatedAt: string;
  result: AnalysisResult;
}

export function loadReportHistory(): ReportHistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveReportToHistory(result: AnalysisResult): ReportHistoryEntry {
  const entry: ReportHistoryEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    query: result.query,
    tickers: result.tickers,
    outlook: result.assessment?.overall_outlook ?? "Neutral",
    generatedAt: result.generatedAt,
    result,
  };

  try {
    const history = loadReportHistory();
    const updated = [entry, ...history].slice(0, MAX_ENTRIES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // localStorage unavailable/full - the report is still shown in-session, just not persisted
  }

  return entry;
}

export function clearReportHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

export function deleteReportFromHistory(id: string): void {
  try {
    const updated = loadReportHistory().filter((e) => e.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // ignore
  }
}
