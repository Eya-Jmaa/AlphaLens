// Types mirroring backend/app/api/routes.py response shapes.
// Keep these in sync with app/models/schemas.py and the /analyze/agent payload.

export type Outlook =
  | "Strongly Positive"
  | "Positive"
  | "Neutral"
  | "Negative"
  | "Strongly Negative"
  | "Insufficient Evidence";

export interface OverallAssessment {
  tickers: string[];
  overall_outlook: Outlook;
  confidence: number;
  strengths: string[];
  risks: string[];
  key_uncertainties: string[];
  disclaimer?: string;
}

export interface StockAnalysisResult {
  ticker: string;
  company_data: Record<string, any>;
  market_data: Record<string, any>;
  analysis: Record<string, any> | string;
}

export interface TechnicalSummary {
  latest_price?: number;
  sma_20?: number | null;
  sma_50?: number | null;
  sma_200?: number | null;
  rsi?: number | null;
  macd?: { macd: number | null; signal: number | null; histogram: number | null };
  bollinger_bands?: { upper: number | null; middle: number | null; lower: number | null };
  atr?: number | null;
  price_change?: Record<string, number | null>;
  high_low?: Record<string, number | null>;
  error?: string;
}

export interface NewsAnalysisResult {
  ticker: string;
  articles?: any[];
  sentiment_summary: {
    overall_sentiment: "positive" | "neutral" | "negative";
    average_score: number;
    total_articles: number;
    sentiment_distribution?: Record<string, string>;
  };
  key_events?: { type: string; title: string; source: string; sentiment: string }[];
  llm_analysis?: { analysis: string };
  status?: string;
}

export interface PortfolioRiskMetrics {
  volatility: number;
  downside_volatility: number | null;
  max_drawdown: number;
  avg_drawdown: number | null;
  var_95: number;
  var_99: number | null;
  cvar_95: number | null;
  cvar_99: number | null;
  sharpe_ratio: number;
  sortino_ratio: number | null;
  calmar_ratio: number | null;
  herfindahl_index: number;
  effective_number: number;
}

export interface RiskAnalysisResult {
  stock_risks: Record<string, { volatility: number; var_95: number; max_drawdown: number; beta: number }>;
  portfolio_metrics: PortfolioRiskMetrics;
  simulation: Record<string, any>;
  llm_analysis: string;
  tickers: string[];
}

export interface SecSource {
  filing_type: string | null;
  filing_date: string | null;
  section: string | null;
  url: string | null;
  source: "sec_edgar" | "sample_data";
}

export interface SecAnalysisResult {
  ticker: string;
  status: "ok" | "insufficient_evidence";
  analysis?: string;
  is_live_edgar_data?: boolean;
  sources?: SecSource[];
  message?: string;
}

export interface AgentExecution {
  completed_agents: string[];
  agent_timings: Record<string, number>;
}

export interface DebateVerdict {
  stronger_case: "bull" | "bear" | "even";
  reasoning: string;
  key_disagreements: string[];
  unresolved_uncertainty: string[];
  confidence: number;
}

export interface DebateResult {
  bull_case?: string;
  bear_case?: string;
  verdict?: DebateVerdict;
}

export interface AnalysisResult {
  id?: string | null;
  query: string;
  report: string;
  assessment: OverallAssessment;
  tickers: string[];
  stock_analysis: StockAnalysisResult[];
  technical_analysis: Record<string, TechnicalSummary>;
  news_analysis: NewsAnalysisResult[];
  risk_analysis: RiskAnalysisResult | Record<string, never>;
  sec_analysis: SecAnalysisResult[];
  debate?: DebateResult | null;
  execution: AgentExecution;
  errors: string[];
  warnings: string[];
  generatedAt: string;
}

export interface AgentProgressEvent {
  type: "agent_started" | "agent_completed" | "done" | "error";
  agent?: string;
  errors?: string[];
  warnings?: string[];
  message?: string;
  result?: AnalysisResult;
}

export const AGENT_LABELS: Record<string, string> = {
  Supervisor: "Supervisor",
  StockAnalysis: "Stock & Fundamentals",
  NewsAnalysis: "News & Sentiment",
  RiskAnalysis: "Risk Analysis",
  SECAnalysis: "SEC Filings",
  BullCase: "Bull Case",
  BearCase: "Bear Case",
  Judge: "Judge",
  FinalAnalyst: "Final Analyst",
};

// ---- Portfolio ----

export interface PortfolioPosition {
  ticker: string;
  weight: number;
}

export interface PortfolioRiskResponse {
  weights: Record<string, number>;
  metrics: {
    volatility: number;
    downside_volatility: number | null;
    max_drawdown: number;
    avg_drawdown: number | null;
    var_95: number;
    var_99: number | null;
    cvar_95: number | null;
    sharpe_ratio: number;
    sortino_ratio: number | null;
    calmar_ratio: number | null;
    correlation_matrix: number[][] | null;
    herfindahl_index: number;
    effective_number: number;
    risk_contributions: Record<string, number> | null;
  };
  simulation: {
    final_value_percentiles: Record<string, number>;
    var_percent: number;
    mean_final_value: number;
  };
}

export interface EfficientFrontierPoint {
  return_rate: number;
  volatility: number;
  weights: Record<string, number>;
  sharpe?: number | null;
}

export interface PortfolioOptimizeResponse {
  optimization: {
    recommended_weights: Record<string, number>;
    expected_return: number;
    expected_volatility: number;
    expected_sharpe: number;
    method: string;
    warnings: string[];
  };
  comparison: {
    current?: { return: number; volatility: number; sharpe: number };
    recommended?: { return: number; volatility: number; sharpe: number };
    improvement?: { return: number; volatility: number; sharpe: number };
    turnover?: number;
    error?: string;
  };
  efficient_frontier: EfficientFrontierPoint[];
}

// ---- Persisted reports & saved portfolios (backend, requires DATABASE_URL) ----

export interface SavedReportSummary {
  id: string;
  query: string;
  tickers: string[];
  overall_outlook: string;
  created_at: string;
}

export interface SavedPortfolio {
  id: string;
  name: string;
  cash: number;
  positions: PortfolioPosition[];
  created_at: string;
}

// ---- Market quotes & company search (top bar / ticker strip) ----

export interface MarketQuote {
  symbol: string;
  name: string | null;
  price: number | null;
  change: number | null;
  change_percent: number | null;
  error?: string | null;
}

export interface CompanySearchResult {
  ticker: string;
  name: string;
}

export interface HealthCheck {
  status: string;
  service: string;
  version: string;
  checks: {
    api: string;
    groq: string;
    database: string;
    redis: string;
    qdrant: string;
  };
}
