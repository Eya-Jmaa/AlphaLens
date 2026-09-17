import {
  AgentProgressEvent,
  AnalysisResult,
  CompanySearchResult,
  HealthCheck,
  MarketQuote,
  PortfolioOptimizeResponse,
  PortfolioPosition,
  PortfolioRiskResponse,
  SavedPortfolio,
  SavedReportSummary,
} from "../types";

// In Vite (`npm run dev`) use same-origin URLs so the browser never calls :8000
// directly (Cursor's preview and some Windows localhost/IPv6 setups block that).
// vite.config.ts proxies /api and /health to local uvicorn.
const API_BASE =
  (import.meta as any).env?.DEV ? "" : ((import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000");

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail ?? JSON.stringify(data);
  } catch {
    return res.statusText || `Request failed with status ${res.status}`;
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ApiError(await parseErrorBody(res), res.status);
  }
  return res.json();
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new ApiError(await parseErrorBody(res), res.status);
  }
  return res.json();
}

/**
 * Run the full multi-agent analysis, streaming progress events as the
 * LangGraph workflow executes. Uses fetch + a manual SSE reader (not
 * EventSource, which can't send a POST body).
 */
export async function analyzeStream(
  query: string,
  onEvent: (event: AgentProgressEvent) => void,
  signal?: AbortSignal,
  debate = false
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/analyze/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, debate }),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new ApiError(await parseErrorBody(res), res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const raw of events) {
      const event = parseSseEvent(raw);
      if (event) onEvent(event);
    }
  }

  // Flush any trailing (unterminated) event left in the buffer.
  const trailing = parseSseEvent(buffer);
  if (trailing) onEvent(trailing);
}

function parseSseEvent(raw: string): AgentProgressEvent | null {
  if (!raw.trim()) return null;
  let eventType = "message";
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) eventType = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return null;
  try {
    const parsed = JSON.parse(data);
    return { type: eventType as AgentProgressEvent["type"], ...parsed };
  } catch {
    return null;
  }
}

/** Non-streaming variant of the same multi-agent workflow. */
export async function analyzeAgent(query: string): Promise<AnalysisResult> {
  const raw = await postJson<any>("/api/v1/analyze/agent", { query });
  return { ...raw, generatedAt: new Date().toISOString() };
}

export interface ChartPoint {
  date: string;
  close: number | null;
  sma_20: number | null;
  sma_50: number | null;
  rsi: number | null;
  macd_histogram: number | null;
}

export async function getChartSeries(ticker: string, period = "6mo"): Promise<ChartPoint[]> {
  const res = await getJson<{ series: ChartPoint[] }>(
    `/api/v1/market/${encodeURIComponent(ticker)}/chart?period=${period}`
  );
  return res.series;
}

export async function analyzePortfolio(
  positions: PortfolioPosition[],
  cash = 0
): Promise<PortfolioRiskResponse> {
  return postJson<PortfolioRiskResponse>("/api/v1/portfolio/analyze", { positions, cash });
}

export async function optimizePortfolio(
  positions: PortfolioPosition[],
  method: "max_sharpe" | "min_volatility" = "max_sharpe",
  maxWeight?: number
): Promise<PortfolioOptimizeResponse> {
  return postJson<PortfolioOptimizeResponse>("/api/v1/portfolio/optimize", {
    positions,
    method,
    max_weight: maxWeight,
  });
}

// ---- Persisted reports & saved portfolios (backend, requires DATABASE_URL) ----

export async function listReports(limit = 25): Promise<SavedReportSummary[]> {
  const res = await getJson<{ reports: SavedReportSummary[] }>(`/api/v1/reports?limit=${limit}`);
  return res.reports;
}

export async function getReport(id: string): Promise<AnalysisResult> {
  const raw = await getJson<any>(`/api/v1/reports/${encodeURIComponent(id)}`);
  return { ...raw, generatedAt: raw.created_at ?? new Date().toISOString() };
}

export async function deleteReport(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/reports/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (!res.ok) {
    throw new ApiError(await parseErrorBody(res), res.status);
  }
}

export async function savePortfolio(
  name: string,
  positions: PortfolioPosition[],
  cash = 0
): Promise<{ id: string }> {
  return postJson<{ id: string }>("/api/v1/portfolios", { name, positions, cash });
}

export async function listSavedPortfolios(): Promise<SavedPortfolio[]> {
  const res = await getJson<{ portfolios: SavedPortfolio[] }>("/api/v1/portfolios");
  return res.portfolios;
}

// ---- Market quotes, company search & system health ----

export async function getMarketQuotes(symbols: string[]): Promise<MarketQuote[]> {
  const res = await getJson<{ quotes: MarketQuote[] }>(
    `/api/v1/market/quotes?symbols=${encodeURIComponent(symbols.join(","))}`
  );
  return res.quotes;
}

export async function searchCompanies(query: string): Promise<CompanySearchResult[]> {
  if (!query.trim()) return [];
  const res = await getJson<{ results: CompanySearchResult[] }>(
    `/api/v1/companies/search?q=${encodeURIComponent(query)}`
  );
  return res.results;
}

export async function getHealth(): Promise<HealthCheck> {
  // Root-level, not under /api/v1 - see backend/app/main.py.
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new ApiError(await parseErrorBody(res), res.status);
  }
  return res.json();
}
