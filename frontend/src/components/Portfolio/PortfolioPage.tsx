import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import clsx from "clsx";
import { Plus, Trash2, Loader2, Save, FolderOpen, ShieldAlert, BarChart3, Sliders, Layers } from "lucide-react";
import {
  analyzePortfolio,
  ApiError,
  getMarketQuotes,
  listSavedPortfolios,
  optimizePortfolio,
  savePortfolio,
} from "../../api/client";
import { MarketQuote, PortfolioOptimizeResponse, PortfolioRiskResponse, SavedPortfolio } from "../../types";
import { MetricCard } from "../Common/MetricCard";
import { Badge } from "../Common/Badge";
import { AllocationPie } from "../charts/AllocationPie";
import { CorrelationHeatmap } from "../charts/CorrelationHeatmap";
import { ComparisonBarChart } from "../charts/ComparisonBarChart";
import { EfficientFrontier } from "../charts/EfficientFrontier";
import { computeCompositeRisk } from "../../utils/riskScore";
import { numberToPercent, formatNumber } from "../../utils/formatters";
import { usePageMeta } from "../Layout/AppShell";

type Row = { ticker: string; weight: string };

const DEFAULT_ROWS: Row[] = [
  { ticker: "AAPL", weight: "30" },
  { ticker: "MSFT", weight: "30" },
  { ticker: "NVDA", weight: "40" },
];

export const PortfolioPage: React.FC = () => {
  usePageMeta({ title: "Portfolio & Risk Desk", subtitle: "Multi-Asset Stress Testing & Markowitz Efficient Allocation" });

  const [name, setName] = useState("Flagship Growth Portfolio");
  const [rows, setRows] = useState<Row[]>(DEFAULT_ROWS);
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  const [busy, setBusy] = useState<"analyze" | "optimize" | "save" | null>(null);
  const [risk, setRisk] = useState<PortfolioRiskResponse | null>(null);
  const [optimization, setOptimization] = useState<PortfolioOptimizeResponse | null>(null);
  const [method, setMethod] = useState<"max_sharpe" | "min_volatility">("max_sharpe");
  const [saved, setSaved] = useState<SavedPortfolio[] | null>(null);

  useEffect(() => {
    listSavedPortfolios()
      .then(setSaved)
      .catch(() => setSaved([]));
  }, []);

  const totalWeight = rows.reduce((sum, r) => sum + (parseFloat(r.weight) || 0), 0);

  useEffect(() => {
    const tickers = Array.from(new Set(rows.map((r) => r.ticker.trim().toUpperCase()).filter(Boolean)));
    if (tickers.length === 0) return;
    const timer = setTimeout(() => {
      getMarketQuotes(tickers)
        .then((res) => {
          setQuotes((prev) => {
            const next = { ...prev };
            for (const q of res) next[q.symbol] = q;
            return next;
          });
        })
        .catch(() => {});
    }, 500);
    return () => clearTimeout(timer);
  }, [rows.map((r) => r.ticker).join(",")]);

  function updateRow(i: number, field: keyof Row, value: string) {
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));
  }

  function addRow() {
    setRows((prev) => [...prev, { ticker: "", weight: "" }]);
  }

  function removeRow(i: number) {
    setRows((prev) => prev.filter((_, idx) => idx !== i));
  }

  function toPositions() {
    return rows
      .filter((r) => r.ticker.trim() && parseFloat(r.weight) > 0)
      .map((r) => ({ ticker: r.ticker.trim().toUpperCase(), weight: (parseFloat(r.weight) || 0) / 100 }));
  }

  async function handleAnalyze() {
    const positions = toPositions();
    if (positions.length === 0) {
      toast.error("Enter at least one position with a valid ticker and allocation.");
      return;
    }
    setBusy("analyze");
    setRisk(null);
    try {
      const result = await analyzePortfolio(positions);
      setRisk(result);
      toast.success("Portfolio risk analysis complete.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to analyze portfolio.");
    } finally {
      setBusy(null);
    }
  }

  async function handleOptimize() {
    const positions = toPositions();
    if (positions.length < 2) {
      toast.error("Add at least two securities to run portfolio optimization.");
      return;
    }
    setBusy("optimize");
    setOptimization(null);
    try {
      const result = await optimizePortfolio(positions, method);
      setOptimization(result);
      toast.success("Efficient frontier optimization complete.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to optimize portfolio.");
    } finally {
      setBusy(null);
    }
  }

  async function handleSave() {
    const positions = toPositions();
    if (positions.length === 0) {
      toast.error("Add at least one position before saving.");
      return;
    }
    setBusy("save");
    try {
      await savePortfolio(name, positions);
      toast.success("Portfolio saved to warehouse.");
      setSaved(await listSavedPortfolios());
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to save portfolio.");
    } finally {
      setBusy(null);
    }
  }

  function loadSaved(p: SavedPortfolio) {
    setName(p.name);
    setRows(p.positions.map((pos) => ({ ticker: pos.ticker, weight: String(Math.round(pos.weight * 100)) })));
    toast.success(`Loaded "${p.name}".`);
  }

  const composite = risk
    ? computeCompositeRisk({
        volatility: risk.metrics.volatility,
        max_drawdown: risk.metrics.max_drawdown,
        var_95: risk.metrics.var_95,
        sharpe_ratio: risk.metrics.sharpe_ratio,
        herfindahl_index: risk.metrics.herfindahl_index,
      })
    : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Portfolio Workbench Panel */}
      <div className="bg-card border border-border rounded p-5 md:p-6 shadow-sm space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 pb-3">
          <div className="flex items-center gap-2 flex-1 min-w-[240px]">
            <Layers size={16} className="text-primary shrink-0" />
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Portfolio Name"
              className="text-sm md:text-base font-bold text-foreground bg-transparent border-none focus:outline-none focus:ring-0 w-full"
            />
          </div>
          <div className="flex items-center gap-2">
            <span
              className={clsx(
                "text-xs font-mono font-bold px-2.5 py-1 rounded border",
                Math.abs(totalWeight - 100) < 0.1
                  ? "bg-success/10 border-success/30 text-success"
                  : "bg-warning/10 border-warning/30 text-warning"
              )}
            >
              Gross Weight: {totalWeight.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Positions Grid */}
        <div className="rounded border border-border overflow-x-auto">
          <table className="w-full text-xs min-w-[500px]">
            <thead>
              <tr className="bg-muted/40 text-[10px] uppercase font-mono tracking-wider text-subtle border-b border-border">
                <th className="text-left font-semibold px-4 py-2.5">Security Symbol</th>
                <th className="text-right font-semibold px-4 py-2.5">Target Weight</th>
                <th className="text-right font-semibold px-4 py-2.5">Live Price</th>
                <th className="text-right font-semibold px-4 py-2.5">24h Delta</th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 font-mono">
              {rows.map((row, i) => {
                const symbol = row.ticker.trim().toUpperCase();
                const quote = quotes[symbol];
                const positive = (quote?.change_percent ?? 0) >= 0;

                return (
                  <tr key={i} className="hover:bg-elevated/50 transition-colors">
                    <td className="px-3 py-2">
                      <input
                        value={row.ticker}
                        onChange={(e) => updateRow(i, "ticker", e.target.value)}
                        placeholder="e.g. AAPL"
                        className="w-32 uppercase font-bold rounded border border-border/80 bg-background px-2.5 py-1 text-xs focus:outline-none focus:border-primary"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex justify-end items-center gap-1">
                        <input
                          value={row.weight}
                          onChange={(e) => updateRow(i, "weight", e.target.value)}
                          placeholder="0"
                          inputMode="decimal"
                          className="w-20 text-right font-bold rounded border border-border/80 bg-background px-2.5 py-1 text-xs focus:outline-none focus:border-primary"
                        />
                        <span className="text-subtle font-mono text-xs">%</span>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-right text-muted-foreground font-semibold">
                      {quote && quote.price !== null ? `$${formatNumber(quote.price, 2)}` : "--"}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {quote && quote.change_percent !== null ? (
                        <span className={clsx("font-bold", positive ? "text-success" : "text-danger")}>
                          {positive ? "+" : ""}
                          {formatNumber(quote.change_percent, 2)}%
                        </span>
                      ) : (
                        "--"
                      )}
                    </td>
                    <td className="px-2 text-center">
                      <button
                        onClick={() => removeRow(i)}
                        aria-label="Remove position"
                        className="p-1.5 text-subtle hover:text-danger transition"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <button
          onClick={addRow}
          className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-primary hover:underline transition"
        >
          <Plus size={13} /> Add Position
        </button>

        {/* Action Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border/80">
          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={handleAnalyze}
              disabled={busy !== null}
              className="px-4 py-2 rounded bg-primary text-primary-foreground text-xs font-mono font-bold uppercase tracking-wider hover:opacity-90 disabled:opacity-60 flex items-center gap-1.5 transition"
            >
              {busy === "analyze" ? <Loader2 size={13} className="animate-spin" /> : <BarChart3 size={13} />}
              Stress-Test Risk
            </button>

            <div className="flex items-center gap-2 rounded border border-border bg-background px-2.5 py-1">
              <Sliders size={13} className="text-subtle" />
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as "max_sharpe" | "min_volatility")}
                className="bg-transparent text-xs font-mono font-medium text-foreground focus:outline-none cursor-pointer"
              >
                <option value="max_sharpe">Maximize Sharpe Ratio</option>
                <option value="min_volatility">Minimize Volatility</option>
              </select>
            </div>

            <button
              onClick={handleOptimize}
              disabled={busy !== null}
              className="px-3.5 py-2 rounded border border-border text-xs font-mono font-bold uppercase tracking-wider hover:bg-elevated disabled:opacity-60 flex items-center gap-1.5 transition"
            >
              {busy === "optimize" && <Loader2 size={13} className="animate-spin" />}
              Rebalance Weights
            </button>
          </div>

          {saved !== null && (
            <button
              onClick={handleSave}
              disabled={busy !== null}
              className="px-3.5 py-2 rounded border border-border text-xs font-mono font-semibold text-muted-foreground hover:text-foreground hover:bg-elevated disabled:opacity-60 flex items-center gap-1.5 transition"
            >
              {busy === "save" ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
              Save Configuration
            </button>
          )}
        </div>
      </div>

      {/* Saved Portfolios Strip */}
      {saved && saved.length > 0 && (
        <div className="bg-card border border-border rounded p-4 shadow-sm space-y-2.5">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
            <FolderOpen size={13} className="text-primary" /> Stored Portfolios
          </div>
          <div className="flex flex-wrap gap-2">
            {saved.map((p) => (
              <button
                key={p.id}
                onClick={() => loadSaved(p)}
                className="px-3 py-1.5 rounded border border-border bg-background text-xs font-mono hover:border-primary/50 hover:text-primary transition"
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Risk Analysis Results */}
      {risk && (
        <section className="bg-card border border-border rounded p-5 md:p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-border/80 pb-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-foreground">
              Factor Risk Decomposition &middot; Historical Backtest
            </h3>
            {composite && (
              <Badge tone={composite.band === "Low" ? "success" : composite.band === "Moderate" ? "warning" : "danger"}>
                Composite Risk: {composite.score}/100 ({composite.band})
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="Annual Volatility" value={numberToPercent(risk.metrics.volatility)} />
            <MetricCard label="Sharpe Ratio" value={formatNumber(risk.metrics.sharpe_ratio, 2)} />
            <MetricCard label="Max Drawdown" value={numberToPercent(risk.metrics.max_drawdown)} tone="danger" />
            <MetricCard label="VaR (95% Daily)" value={numberToPercent(risk.metrics.var_95)} tone="warning" />
          </div>

          <div className="grid md:grid-cols-2 gap-6 items-start border-t border-border/80 pt-5">
            <div className="space-y-2">
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground">
                Current Asset Allocation
              </div>
              <AllocationPie weights={risk.weights} />
            </div>
            {risk.metrics.correlation_matrix && (
              <div className="space-y-2">
                <div className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground">
                  Cross-Asset Correlation Matrix
                </div>
                <CorrelationHeatmap tickers={Object.keys(risk.weights)} matrix={risk.metrics.correlation_matrix} />
              </div>
            )}
          </div>
        </section>
      )}

      {/* Optimization Results */}
      {optimization && (
        <section className="bg-card border border-border rounded p-5 md:p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-border/80 pb-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-foreground">
              Markowitz Mean-Variance Optimization
            </h3>
            <span className="text-xs font-mono text-muted-foreground uppercase">
              Target: {optimization.optimization.method}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <MetricCard label="Target Expected Return" value={numberToPercent(optimization.optimization.expected_return)} />
            <MetricCard label="Expected Volatility" value={numberToPercent(optimization.optimization.expected_volatility)} />
            <MetricCard label="Optimized Sharpe Ratio" value={formatNumber(optimization.optimization.expected_sharpe, 2)} />
          </div>

          <div className="grid md:grid-cols-2 gap-6 items-start border-t border-border/80 pt-5">
            <div className="space-y-2">
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground">
                Optimized Weight Target
              </div>
              <AllocationPie weights={optimization.optimization.recommended_weights} />
            </div>
            {optimization.comparison.current && optimization.comparison.recommended && (
              <div className="space-y-2">
                <div className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground">
                  Current vs. Rebalanced Delta
                </div>
                <ComparisonBarChart
                  current={optimization.comparison.current}
                  recommended={optimization.comparison.recommended}
                />
              </div>
            )}
          </div>

          {optimization.efficient_frontier.length > 0 && (
            <div className="border-t border-border/80 pt-5 space-y-2">
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground">
                Efficient Frontier Curve
              </div>
              <EfficientFrontier
                frontier={optimization.efficient_frontier}
                current={optimization.comparison.current}
                recommended={optimization.comparison.recommended}
              />
            </div>
          )}
        </section>
      )}
    </div>
  );
};
