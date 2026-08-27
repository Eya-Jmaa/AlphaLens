import React from "react";
import { AlertTriangle, FileText, Gavel, Newspaper, ShieldAlert, TrendingDown, TrendingUp } from "lucide-react";
import { AnalysisResult } from "../../types";
import { Badge } from "../Common/Badge";
import { MetricCard } from "../Common/MetricCard";
import { MarkdownLite } from "./MarkdownLite";
import { TickerChartCard } from "./TickerChartCard";
import {
  formatCurrency,
  formatDate,
  formatNumber,
  numberToPercent,
  outlookTone,
  sentimentTone,
} from "../../utils/formatters";

export const ReportView: React.FC<{ result: AnalysisResult }> = ({ result }) => {
  // Saved/historical reports (loaded via GET /api/v1/reports/{id}) only persist the
  // synthesized report + assessment, not each agent's raw sub-results - those fields
  // are absent rather than empty, so every one needs a fallback here.
  const assessment = result.assessment ?? {
    tickers: [], overall_outlook: "Neutral", confidence: 0, strengths: [], risks: [],
    key_uncertainties: [], disclaimer: "",
  };
  const stock_analysis = result.stock_analysis ?? [];
  const technical_analysis = result.technical_analysis ?? {};
  const news_analysis = result.news_analysis ?? [];
  const risk_analysis = result.risk_analysis ?? {};
  const sec_analysis = result.sec_analysis ?? [];
  const debate = result.debate;
  const errors = result.errors ?? [];
  const warnings = result.warnings ?? [];
  const tickers = result.tickers ?? [];
  const executionAgents = result.execution?.completed_agents ?? [];

  return (
    <article className="space-y-6">
      {/* Header */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs text-muted-foreground">Query</div>
            <h2 className="text-xl font-semibold mt-0.5">{result.query}</h2>
            <div className="text-xs text-muted-foreground mt-1">Generated {formatDate(result.generatedAt)}</div>
          </div>
          <div className="flex items-center gap-2">
            {tickers.map((t) => (
              <Badge key={t} tone="primary">
                {t}
              </Badge>
            ))}
            <Badge tone={outlookTone(assessment.overall_outlook)}>{assessment.overall_outlook}</Badge>
          </div>
        </div>

        {(errors.length > 0 || warnings.length > 0) && (
          <div className="mt-4 space-y-1.5">
            {errors.map((e, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-danger bg-danger/10 border border-danger/20 rounded-md px-3 py-2">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                {e}
              </div>
            ))}
            {warnings.map((w, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-warning bg-warning/10 border border-warning/20 rounded-md px-3 py-2">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                {w}
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
          <MetricCard label="Confidence" value={numberToPercent(assessment.confidence, 0)} />
          <MetricCard label="Strengths identified" value={String(assessment.strengths.length)} tone="success" />
          <MetricCard label="Risks identified" value={String(assessment.risks.length)} tone="danger" />
          <MetricCard label="Agents run" value={String(executionAgents.length)} />
        </div>
      </div>

      {/* Fundamentals */}
      {stock_analysis.length > 0 && (
        <section className="grid md:grid-cols-2 gap-4">
          {stock_analysis.map((s) => {
            const info = s.company_data ?? {};
            return (
              <div key={s.ticker} className="bg-card border border-border rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-semibold">{info.name ?? s.ticker}</div>
                  <Badge tone="muted">{info.sector ?? "N/A"}</Badge>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <MetricCard label="Price" value={info.price ? `$${formatNumber(info.price)}` : "N/A"} />
                  <MetricCard label="Market Cap" value={formatCurrency(info.market_cap)} />
                  <MetricCard label="P/E Ratio" value={formatNumber(info.pe_ratio)} />
                </div>
              </div>
            );
          })}
        </section>
      )}

      {/* Technical charts */}
      {tickers.length > 0 && Object.keys(technical_analysis).length > 0 && (
        <section className="grid md:grid-cols-2 gap-4">
          {tickers.map((t) => (
            <TickerChartCard key={t} ticker={t} />
          ))}
        </section>
      )}

      {/* News & Sentiment */}
      {news_analysis.length > 0 && (
        <section className="bg-card border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 text-sm font-semibold mb-3">
            <Newspaper size={16} /> News &amp; Sentiment
          </div>
          <div className="space-y-4">
            {news_analysis.map((n) => (
              <div key={n.ticker} className="border-t border-border pt-3 first:border-0 first:pt-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="font-medium text-sm">{n.ticker}</span>
                  <Badge tone={sentimentTone(n.sentiment_summary.overall_sentiment)}>
                    {n.sentiment_summary.overall_sentiment} ({n.sentiment_summary.total_articles} articles)
                  </Badge>
                </div>
                {n.llm_analysis?.analysis && (
                  <div className="text-sm text-muted-foreground">
                    <MarkdownLite text={n.llm_analysis.analysis} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Risk */}
      {risk_analysis && "portfolio_metrics" in risk_analysis && (
        <section className="bg-card border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 text-sm font-semibold mb-3">
            <ShieldAlert size={16} /> Risk Analysis
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <MetricCard label="Volatility (annual)" value={numberToPercent(risk_analysis.portfolio_metrics.volatility)} />
            <MetricCard label="Sharpe Ratio" value={formatNumber(risk_analysis.portfolio_metrics.sharpe_ratio)} />
            <MetricCard
              label="Max Drawdown"
              value={numberToPercent(risk_analysis.portfolio_metrics.max_drawdown)}
              tone="danger"
            />
            <MetricCard label="VaR (95%)" value={numberToPercent(risk_analysis.portfolio_metrics.var_95)} tone="warning" />
          </div>
          {risk_analysis.llm_analysis && (
            <div className="text-sm text-muted-foreground">
              <MarkdownLite text={risk_analysis.llm_analysis} />
            </div>
          )}
        </section>
      )}

      {/* SEC evidence */}
      {sec_analysis.length > 0 && (
        <section className="bg-card border border-border rounded-xl p-5">
          <div className="flex items-center gap-2 text-sm font-semibold mb-3">
            <FileText size={16} /> SEC Filing Evidence
          </div>
          <div className="space-y-4">
            {sec_analysis.map((s) => (
              <div key={s.ticker} className="border-t border-border pt-3 first:border-0 first:pt-0">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <span className="font-medium text-sm">{s.ticker}</span>
                  {s.is_live_edgar_data === false && (
                    <Badge tone="warning">Sample data (EDGAR unavailable)</Badge>
                  )}
                  {s.is_live_edgar_data === true && <Badge tone="success">Live SEC EDGAR</Badge>}
                </div>
                {s.status === "insufficient_evidence" ? (
                  <p className="text-sm text-muted-foreground">{s.message}</p>
                ) : (
                  <>
                    <div className="text-sm text-muted-foreground">
                      <MarkdownLite text={s.analysis ?? ""} />
                    </div>
                    {s.sources && s.sources.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {s.sources.map((src, i) => (
                          <Badge key={i} tone="muted">
                            {src.filing_type} &middot; {src.filing_date} &middot; {src.section}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Bull vs. Bear debate */}
      {debate && (debate.bull_case || debate.bear_case) && (
        <section className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-card border border-success/30 rounded-xl p-5">
              <div className="flex items-center gap-2 text-sm font-semibold mb-3 text-success">
                <TrendingUp size={16} /> Bull Case
              </div>
              <div className="text-sm text-muted-foreground">
                <MarkdownLite text={debate.bull_case ?? "No bull case available."} />
              </div>
            </div>
            <div className="bg-card border border-danger/30 rounded-xl p-5">
              <div className="flex items-center gap-2 text-sm font-semibold mb-3 text-danger">
                <TrendingDown size={16} /> Bear Case
              </div>
              <div className="text-sm text-muted-foreground">
                <MarkdownLite text={debate.bear_case ?? "No bear case available."} />
              </div>
            </div>
          </div>

          {debate.verdict && (
            <div className="bg-card border border-border rounded-xl p-5">
              <div className="flex items-center gap-2 text-sm font-semibold mb-2">
                <Gavel size={16} /> Judge's Verdict
                <Badge tone={debate.verdict.stronger_case === "bull" ? "success" : debate.verdict.stronger_case === "bear" ? "danger" : "muted"}>
                  {debate.verdict.stronger_case === "even" ? "Evenly matched" : `${debate.verdict.stronger_case} case stronger`}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{debate.verdict.reasoning}</p>
              {debate.verdict.unresolved_uncertainty.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs font-semibold text-muted-foreground mb-1.5">Unresolved uncertainty</div>
                  <ul className="space-y-1">
                    {debate.verdict.unresolved_uncertainty.map((u, i) => (
                      <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                        <span className="mt-1 w-1 h-1 rounded-full bg-muted-foreground shrink-0" />
                        {u}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Strengths / Risks / Uncertainties */}
      {(assessment.strengths.length > 0 || assessment.risks.length > 0 || assessment.key_uncertainties.length > 0) && (
        <section className="grid md:grid-cols-3 gap-4">
          <BulletCard title="Strengths" items={assessment.strengths} tone="success" />
          <BulletCard title="Risks" items={assessment.risks} tone="danger" />
          <BulletCard title="Key Uncertainties" items={assessment.key_uncertainties} tone="warning" />
        </section>
      )}

      {/* Full narrative report */}
      <details className="bg-card border border-border rounded-xl p-5" open>
        <summary className="text-sm font-semibold cursor-pointer select-none">Full Report</summary>
        <div className="mt-3">
          <MarkdownLite text={result.report} />
        </div>
      </details>

      <p className="text-xs text-muted-foreground text-center px-4">{assessment.disclaimer}</p>
    </article>
  );
};

const DOT_TONE_CLASSES: Record<"success" | "danger" | "warning", string> = {
  success: "bg-success",
  danger: "bg-danger",
  warning: "bg-warning",
};

const BulletCard: React.FC<{ title: string; items: string[]; tone: "success" | "danger" | "warning" }> = ({
  title,
  items,
  tone,
}) => (
  <div className="bg-card border border-border rounded-xl p-5">
    <div className="text-sm font-semibold mb-2.5">{title}</div>
    {items.length === 0 ? (
      <p className="text-xs text-muted-foreground">None identified.</p>
    ) : (
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-sm flex items-start gap-2">
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${DOT_TONE_CLASSES[tone]}`} />
            <span className="text-foreground/90">{item}</span>
          </li>
        ))}
      </ul>
    )}
  </div>
);
