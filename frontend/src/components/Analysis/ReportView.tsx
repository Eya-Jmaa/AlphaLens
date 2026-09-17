import React, { useMemo, useState } from "react";
import clsx from "clsx";
import {
  AlertTriangle,
  FileText,
  Gavel,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
  BarChart2,
  Printer,
  Copy,
  Check,
  CheckCircle2,
  Scale,
  FileCheck2,
  LucideIcon,
  Sparkles,
} from "lucide-react";
import toast from "react-hot-toast";
import { AnalysisResult } from "../../types";
import { Badge } from "../Common/Badge";
import { MetricCard } from "../Common/MetricCard";
import { MarkdownLite } from "./MarkdownLite";
import { TickerChartCard } from "./TickerChartCard";
import { computeCompositeRisk } from "../../utils/riskScore";
import {
  formatCurrency,
  formatDate,
  formatNumber,
  numberToPercent,
  outlookTone,
} from "../../utils/formatters";

type TabId = "memo" | "fundamentals" | "technical" | "sec" | "risk" | "debate" | "full_report";

export const ReportView: React.FC<{ result: AnalysisResult }> = ({ result }) => {
  const [copied, setCopied] = useState(false);

  const assessment = result.assessment ?? {
    tickers: [],
    overall_outlook: "Neutral",
    confidence: 0,
    strengths: [],
    risks: [],
    key_uncertainties: [],
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

  const hasRisk = risk_analysis && "portfolio_metrics" in risk_analysis;
  const hasDebate = !!(debate && (debate.bull_case || debate.bear_case));

  const TABS: { id: TabId; label: string; icon: LucideIcon; show: boolean }[] = [
    { id: "memo", label: "Executive Memo", icon: FileText, show: true },
    { id: "fundamentals", label: "Fundamentals & Valuation", icon: BarChart2, show: stock_analysis.length > 0 },
    { id: "technical", label: "Price & Technicals", icon: TrendingUp, show: tickers.length > 0 && Object.keys(technical_analysis).length > 0 },
    { id: "sec", label: "SEC EDGAR Audit", icon: FileCheck2, show: sec_analysis.length > 0 },
    { id: "risk", label: "Risk & Stress Test", icon: ShieldAlert, show: hasRisk },
    { id: "debate", label: "Bull vs. Bear Debate", icon: Scale, show: hasDebate },
    { id: "full_report", label: "Full Report", icon: FileText, show: Boolean(result.report) },
  ];
  const visibleTabs = TABS.filter((t) => t.show);
  const [tab, setTab] = useState<TabId>("memo");
  const activeTab = visibleTabs.some((t) => t.id === tab) ? tab : "memo";

  const primaryStock = stock_analysis[0]?.company_data ?? {};
  const companyTitle = primaryStock.name || (tickers.length > 0 ? tickers.join(", ") : "Equities Research");

  const avgPeRatio = useMemo(() => {
    const values = stock_analysis
      .map((s) => (s.company_data ?? {}).pe_ratio)
      .filter((v): v is number => typeof v === "number" && v > 0);
    if (values.length === 0) return null;
    return values.reduce((a, b) => a + b, 0) / values.length;
  }, [stock_analysis]);

  const composite = hasRisk
    ? computeCompositeRisk(
        {
          volatility: risk_analysis.portfolio_metrics.volatility,
          max_drawdown: risk_analysis.portfolio_metrics.max_drawdown,
          var_95: risk_analysis.portfolio_metrics.var_95,
          sharpe_ratio: risk_analysis.portfolio_metrics.sharpe_ratio,
          herfindahl_index: risk_analysis.portfolio_metrics.herfindahl_index,
        },
        avgPeRatio
      )
    : null;

  function copyThesis() {
    const text = `EQUITY RESEARCH MEMO: ${companyTitle} (${tickers.join(", ")})\nOutlook: ${assessment.overall_outlook} (Conviction: ${numberToPercent(assessment.confidence, 0)})\n\nKey Strengths:\n${assessment.strengths.map((s) => `- ${s}`).join("\n")}\n\nKey Risks:\n${assessment.risks.map((r) => `- ${r}`).join("\n")}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Executive summary copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  }

  function printDossier() {
    window.print();
  }

  return (
    <article className="space-y-6">
      {/* Dossier Header Card */}
      <div className="card space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border/60 pb-5">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                Equity Research Dossier
              </span>
              <span className="text-xs text-muted-foreground">
                Verified {formatDate(result.generatedAt)}
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2.5">
              {companyTitle}
              {tickers.map((t) => (
                <span
                  key={t}
                  className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-background-secondary text-foreground border border-border"
                >
                  {t}
                </span>
              ))}
            </h2>
            <div className="text-xs text-muted-foreground font-medium">
              Directive: <span className="text-foreground">{result.query}</span>
            </div>
          </div>

          {/* Stance & Action Capsule */}
          <div className="flex flex-col sm:items-end gap-2.5 shrink-0">
            <div className="flex items-center gap-2">
              <Badge tone={outlookTone(assessment.overall_outlook)} className="text-xs py-1 px-3.5">
                {assessment.overall_outlook}
              </Badge>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-background-secondary border border-border text-xs font-bold font-tabular">
                <span className="text-muted-foreground font-normal">Conviction:</span>
                <span>{numberToPercent(assessment.confidence, 0)}</span>
              </div>
            </div>

            <div className="no-print flex items-center gap-2 pt-1">
              <button
                onClick={copyThesis}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border bg-background text-xs font-semibold text-muted-foreground hover:text-foreground hover:bg-card transition shadow-sm"
              >
                {copied ? <Check size={13} className="text-emerald-500" /> : <Copy size={13} />}
                {copied ? "Copied" : "Copy Thesis"}
              </button>
              <button
                onClick={printDossier}
                className="btn-pill-dark text-xs py-1.5 px-4 inline-flex items-center gap-1.5 shadow-sm"
              >
                <Printer size={13} /> Print Dossier
              </button>
            </div>
          </div>
        </div>

        {/* Warnings & Errors */}
        {(errors.length > 0 || warnings.length > 0) && (
          <div className="space-y-2">
            {errors.map((e, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-rose-600 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 rounded-2xl px-4 py-2.5">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                {e}
              </div>
            ))}
            {warnings.map((w, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-2xl px-4 py-2.5">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                {w}
              </div>
            ))}
          </div>
        )}

        {/* Highlights Ribbon */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
          <div className="p-4 rounded-2xl bg-background-secondary/60 border border-border/60">
            <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Consensus Stance</div>
            <div className="text-lg font-extrabold text-foreground mt-1">{assessment.overall_outlook}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">Analyst Consensus</div>
          </div>

          <div className="p-4 rounded-2xl bg-background-secondary/60 border border-border/60">
            <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Conviction Rating</div>
            <div className="text-lg font-extrabold text-foreground font-tabular mt-1">{numberToPercent(assessment.confidence, 0)}</div>
            <div className="w-full bg-border h-1.5 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(5, assessment.confidence * 100))}%` }}
              />
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-background-secondary/60 border border-border/60">
            <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Catalysts vs. Risks</div>
            <div className="text-lg font-extrabold font-tabular text-foreground mt-1">
              <span className="text-emerald-500">{assessment.strengths.length}</span>
              <span className="text-subtle mx-1.5 font-normal">/</span>
              <span className="text-rose-500">{assessment.risks.length}</span>
            </div>
            <div className="text-[11px] text-muted-foreground mt-0.5">Identified Drivers</div>
          </div>

          <div className="p-4 rounded-2xl bg-background-secondary/60 border border-border/60">
            <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Composite Risk</div>
            <div className="text-lg font-extrabold font-tabular text-foreground mt-1">
              {composite ? `${composite.score}/100` : "Normal"}
            </div>
            <div className="text-[11px] text-muted-foreground mt-0.5">
              {composite ? `${composite.band} Risk Band` : "Stress-Tested"}
            </div>
          </div>
        </div>
      </div>

      {/* Modern Pill Tabs (Reference Style) */}
      <div className="no-print inline-flex p-1.5 rounded-full bg-card border border-border/80 shadow-sm gap-1 overflow-x-auto max-w-full">
        {visibleTabs.map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-full whitespace-nowrap transition-all",
                isActive
                  ? "bg-foreground text-background shadow-md"
                  : "text-muted-foreground hover:text-foreground hover:bg-background-secondary"
              )}
            >
              <Icon size={14} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Executive Memo */}
      {activeTab === "memo" && (
        <div className="space-y-5">
          {(assessment.strengths.length > 0 || assessment.risks.length > 0 || assessment.key_uncertainties.length > 0) && (
            <div className="grid md:grid-cols-3 gap-4">
              <ModernFactorCard
                title="Primary Upside Catalysts"
                items={assessment.strengths}
                tone="success"
              />
              <ModernFactorCard
                title="Critical Vulnerabilities & Risks"
                items={assessment.risks}
                tone="danger"
              />
              <ModernFactorCard
                title="Strategic Uncertainties"
                items={assessment.key_uncertainties}
                tone="warning"
              />
            </div>
          )}

          <div className="card space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                <FileText size={16} className="text-foreground" />
                Executive Research Findings
              </h3>
              <span className="text-xs text-muted-foreground font-medium">Consolidated Synthesis</span>
            </div>
            <div className="prose dark:prose-invert max-w-none text-xs md:text-sm leading-relaxed">
              <MarkdownLite text={result.report} />
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Fundamentals & Valuation */}
      {activeTab === "fundamentals" && (
        <div className="grid md:grid-cols-2 gap-5">
          {stock_analysis.map((s) => {
            const info = s.company_data ?? {};

            return (
              <div key={s.ticker} className="card space-y-4">
                <div className="flex items-center justify-between border-b border-border/60 pb-3">
                  <div>
                    <div className="text-base font-extrabold text-foreground">{info.name ?? s.ticker}</div>
                    <div className="text-xs text-muted-foreground">{info.sector ?? "Equities"} &middot; {info.industry ?? "General"}</div>
                  </div>
                  <span className="text-xs font-extrabold px-3 py-1 rounded-full bg-foreground text-background">
                    {s.ticker}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3.5 rounded-2xl bg-background-secondary/60 border border-border/60">
                    <div className="text-[10px] font-bold text-muted-foreground uppercase">Last Price</div>
                    <div className="text-base font-extrabold font-tabular text-foreground mt-1">
                      {info.price ? `$${formatNumber(info.price, 2)}` : "--"}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-2xl bg-background-secondary/60 border border-border/60">
                    <div className="text-[10px] font-bold text-muted-foreground uppercase">Market Cap</div>
                    <div className="text-base font-extrabold font-tabular text-foreground mt-1">
                      {formatCurrency(info.market_cap)}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-2xl bg-background-secondary/60 border border-border/60">
                    <div className="text-[10px] font-bold text-muted-foreground uppercase">P/E Ratio</div>
                    <div className="text-base font-extrabold font-tabular text-foreground mt-1">
                      {info.pe_ratio ? `${formatNumber(info.pe_ratio, 1)}x` : "--"}
                    </div>
                  </div>
                </div>

                {typeof s.analysis === "string" && s.analysis && (
                  <div className="pt-2 text-xs md:text-sm text-muted-foreground leading-relaxed border-t border-border/60">
                    <MarkdownLite text={s.analysis} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Tab 3: Technical & Price Action */}
      {activeTab === "technical" && (
        <div className="grid md:grid-cols-2 gap-5">
          {tickers.map((t) => (
            <TickerChartCard key={t} ticker={t} />
          ))}
        </div>
      )}

      {/* Tab 4: SEC EDGAR Audit */}
      {activeTab === "sec" && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <FileCheck2 size={18} className="text-foreground" />
              <h3 className="text-sm font-bold text-foreground">
                SEC EDGAR Regulatory Disclosures
              </h3>
            </div>
            <span className="text-xs text-muted-foreground font-medium">
              10-K &amp; 10-Q Extraction
            </span>
          </div>

          <div className="space-y-5">
            {sec_analysis.map((s) => (
              <div key={s.ticker} className="space-y-3 border-b border-border/60 pb-5 last:border-0 last:pb-0">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold px-3 py-1 rounded-full bg-foreground text-background">
                      {s.ticker}
                    </span>
                    <span className="text-xs font-bold text-foreground">
                      Regulatory Risk Factor Assessment
                    </span>
                  </div>
                  {s.is_live_edgar_data === true ? (
                    <span className="text-[11px] font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900 flex items-center gap-1">
                      <CheckCircle2 size={12} /> Verified SEC EDGAR
                    </span>
                  ) : (
                    <span className="text-[11px] font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-600 border border-amber-200">
                      Sample Data (EDGAR Offline)
                    </span>
                  )}
                </div>

                {s.status === "insufficient_evidence" ? (
                  <p className="text-xs text-muted-foreground">{s.message}</p>
                ) : (
                  <>
                    <div className="text-xs md:text-sm text-foreground/90 leading-relaxed bg-background-secondary/50 p-4 rounded-2xl border border-border/60">
                      <MarkdownLite text={s.analysis ?? ""} />
                    </div>
                    {s.sources && s.sources.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {s.sources.map((src, i) => (
                          <span
                            key={i}
                            className="text-[11px] font-semibold px-3 py-1 rounded-full bg-card border border-border text-muted-foreground"
                          >
                            {src.filing_type} &middot; {src.filing_date} &middot; {src.section}
                          </span>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 5: Risk & Factor Model */}
      {activeTab === "risk" && hasRisk && composite && (
        <div className="space-y-5">
          <div className="card space-y-4">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <ShieldAlert size={16} className="text-foreground" />
              Factor Risk Stress-Test
            </h3>

            <div className="flex items-center gap-6 flex-wrap">
              <div className="p-5 rounded-2xl bg-background-secondary/60 border border-border text-center min-w-[150px]">
                <div className="text-4xl font-extrabold text-foreground font-tabular">{composite.score}</div>
                <div className="text-[11px] font-bold text-muted-foreground uppercase mt-1">Score / 100</div>
                <Badge
                  tone={composite.band === "Low" ? "success" : composite.band === "Moderate" ? "warning" : "danger"}
                  className="mt-2 text-[11px]"
                >
                  {composite.band} Risk
                </Badge>
              </div>

              <div className="flex-1 min-w-[260px] space-y-3">
                {composite.factors.map((f) => (
                  <div key={f.label}>
                    <div className="flex items-center justify-between text-xs mb-1.5 font-semibold">
                      <span className="text-muted-foreground">{f.label}</span>
                      <span className="text-foreground font-bold font-tabular">{f.detail}</span>
                    </div>
                    <div className="h-2 rounded-full bg-border overflow-hidden">
                      <div
                        className={clsx(
                          "h-full rounded-full transition-all duration-500",
                          f.score >= 70 ? "bg-rose-500" : f.score >= 40 ? "bg-amber-500" : "bg-emerald-500"
                        )}
                        style={{ width: `${Math.max(5, f.score)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
              <MetricCard label="Annual Volatility" value={numberToPercent(risk_analysis.portfolio_metrics.volatility)} />
              <MetricCard label="Sharpe Ratio" value={formatNumber(risk_analysis.portfolio_metrics.sharpe_ratio, 2)} />
              <MetricCard label="Peak Drawdown" value={numberToPercent(risk_analysis.portfolio_metrics.max_drawdown)} tone="danger" />
              <MetricCard label="VaR (95% Daily)" value={numberToPercent(risk_analysis.portfolio_metrics.var_95)} tone="warning" />
            </div>

            {risk_analysis.llm_analysis && (
              <div className="text-xs md:text-sm text-muted-foreground pt-4 border-t border-border/60 leading-relaxed">
                <MarkdownLite text={risk_analysis.llm_analysis} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 6: Bull vs Bear Debate */}
      {activeTab === "debate" && hasDebate && (
        <div className="space-y-5">
          <div className="grid md:grid-cols-2 gap-5">
            <div className="card space-y-3 border-emerald-500/30 bg-emerald-50/20 dark:bg-emerald-950/10">
              <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2.5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                  <TrendingUp size={15} /> Long Thesis (Bull Desk)
                </div>
                <span className="text-[10px] font-bold text-emerald-600 uppercase">Catalysts</span>
              </div>
              <div className="text-xs md:text-sm text-foreground/90 leading-relaxed">
                <MarkdownLite text={debate!.bull_case ?? "No bull thesis available."} />
              </div>
            </div>

            <div className="card space-y-3 border-rose-500/30 bg-rose-50/20 dark:bg-rose-950/10">
              <div className="flex items-center justify-between border-b border-rose-500/20 pb-2.5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
                  <TrendingDown size={15} /> Short Thesis (Bear Desk)
                </div>
                <span className="text-[10px] font-bold text-rose-600 uppercase">Downside Risks</span>
              </div>
              <div className="text-xs md:text-sm text-foreground/90 leading-relaxed">
                <MarkdownLite text={debate!.bear_case ?? "No bear thesis available."} />
              </div>
            </div>
          </div>

          {debate!.verdict && (
            <div className="card space-y-3">
              <div className="flex items-center justify-between border-b border-border/60 pb-3">
                <div className="flex items-center gap-2 text-sm font-bold text-foreground">
                  <Gavel size={16} className="text-foreground" /> Investment Committee Verdict
                </div>
                <Badge
                  tone={debate!.verdict.stronger_case === "bull" ? "success" : debate!.verdict.stronger_case === "bear" ? "danger" : "muted"}
                  className="text-xs"
                >
                  {debate!.verdict.stronger_case === "even" ? "Evenly Balanced" : `${debate!.verdict.stronger_case} Thesis Prevails`}
                </Badge>
              </div>
              <p className="text-xs md:text-sm text-foreground/90 leading-relaxed">
                {debate!.verdict.reasoning}
              </p>

              {debate!.verdict.unresolved_uncertainty.length > 0 && (
                <div className="pt-2">
                  <div className="text-[11px] font-bold text-muted-foreground mb-1.5">
                    Unresolved Factor Uncertainties:
                  </div>
                  <ul className="space-y-1.5">
                    {debate!.verdict.unresolved_uncertainty.map((u, i) => (
                      <li key={i} className="text-xs text-muted-foreground flex items-start gap-2">
                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-foreground shrink-0" />
                        {u}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 7: Full Report */}
      {activeTab === "full_report" && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-sm font-bold text-foreground">Complete Equity Research Memo</h3>
            <span className="text-xs text-muted-foreground">Unabridged</span>
          </div>
          <div className="prose dark:prose-invert max-w-none text-xs md:text-sm leading-relaxed">
            <MarkdownLite text={result.report} />
          </div>
        </div>
      )}
    </article>
  );
};

const DOT_TONE_CLASSES: Record<"success" | "danger" | "warning", string> = {
  success: "bg-emerald-500",
  danger: "bg-rose-500",
  warning: "bg-amber-500",
};

const ModernFactorCard: React.FC<{
  title: string;
  items: string[];
  tone: "success" | "danger" | "warning";
}> = ({ title, items, tone }) => (
  <div className="card space-y-3">
    <div className="text-xs font-bold uppercase tracking-wider text-foreground flex items-center justify-between">
      <span>{title}</span>
      <span className="text-[11px] font-semibold text-muted-foreground font-tabular">({items.length})</span>
    </div>
    {items.length === 0 ? (
      <p className="text-xs text-muted-foreground">None isolated in coverage.</p>
    ) : (
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="text-xs flex items-start gap-2.5 leading-snug">
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${DOT_TONE_CLASSES[tone]}`} />
            <span className="text-foreground/90 font-medium">{item}</span>
          </li>
        ))}
      </ul>
    )}
  </div>
);
