import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Plus, Trash2, Loader2, Save, FolderOpen } from "lucide-react";
import {
  analyzePortfolio,
  ApiError,
  listSavedPortfolios,
  optimizePortfolio,
  savePortfolio,
} from "../../api/client";
import { PortfolioOptimizeResponse, PortfolioRiskResponse, SavedPortfolio } from "../../types";
import { MetricCard } from "../Common/MetricCard";
import { Badge } from "../Common/Badge";
import { AllocationPie } from "../charts/AllocationPie";
import { CorrelationHeatmap } from "../charts/CorrelationHeatmap";
import { ComparisonBarChart } from "../charts/ComparisonBarChart";
import { numberToPercent, formatNumber } from "../../utils/formatters";
import { usePageMeta } from "../Layout/AppShell";

type Row = { ticker: string; weight: string };

const DEFAULT_ROWS: Row[] = [
  { ticker: "AAPL", weight: "30" },
  { ticker: "MSFT", weight: "30" },
  { ticker: "NVDA", weight: "40" },
];

export const PortfolioPage: React.FC = () => {
  usePageMeta({ title: "Portfolio", subtitle: "Risk analysis and allocation optimization" });

  const [name, setName] = useState("My Portfolio");
  const [rows, setRows] = useState<Row[]>(DEFAULT_ROWS);
  const [busy, setBusy] = useState<"analyze" | "optimize" | "save" | null>(null);
  const [risk, setRisk] = useState<PortfolioRiskResponse | null>(null);
  const [optimization, setOptimization] = useState<PortfolioOptimizeResponse | null>(null);
  const [method, setMethod] = useState<"max_sharpe" | "min_volatility">("max_sharpe");
  const [saved, setSaved] = useState<SavedPortfolio[] | null>(null);

  useEffect(() => {
    listSavedPortfolios()
      .then(setSaved)
      .catch(() => setSaved([])); // no database configured - saving/loading just won't be offered
  }, []);

  const totalWeight = rows.reduce((sum, r) => sum + (parseFloat(r.weight) || 0), 0);

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
      toast.error("Add at least one position with a ticker and weight.");
      return;
    }
    setBusy("analyze");
    setRisk(null);
    try {
      const result = await analyzePortfolio(positions);
      setRisk(result);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Failed to analyze portfolio.");
    } finally {
      setBusy(null);
    }
  }

  async function handleOptimize() {
    const positions = toPositions();
    if (positions.length < 2) {
      toast.error("Add at least two positions to optimize across.");
      return;
    }
    setBusy("optimize");
    setOptimization(null);
    try {
      const result = await optimizePortfolio(positions, method);
      setOptimization(result);
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
      toast.success("Portfolio saved.");
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4 gap-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Portfolio name"
            className="text-sm font-semibold bg-transparent border-none focus:outline-none focus:ring-0 min-w-0"
          />
          <span className={`text-xs shrink-0 ${Math.abs(totalWeight - 100) > 0.5 ? "text-warning" : "text-muted-foreground"}`}>
            Total: {totalWeight.toFixed(0)}%
          </span>
        </div>

        <div className="space-y-2">
          {rows.map((row, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                value={row.ticker}
                onChange={(e) => updateRow(i, "ticker", e.target.value)}
                placeholder="Ticker (e.g. AAPL)"
                className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <div className="relative w-28">
                <input
                  value={row.weight}
                  onChange={(e) => updateRow(i, "weight", e.target.value)}
                  placeholder="Weight"
                  inputMode="decimal"
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">%</span>
              </div>
              <button
                onClick={() => removeRow(i)}
                aria-label="Remove position"
                className="p-2 text-muted-foreground hover:text-danger transition"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>

        <button
          onClick={addRow}
          className="mt-3 flex items-center gap-1.5 text-xs font-medium text-primary hover:opacity-80 transition"
        >
          <Plus size={14} /> Add position
        </button>

        <div className="flex flex-wrap items-center gap-3 mt-5">
          <button
            onClick={handleAnalyze}
            disabled={busy !== null}
            className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-semibold hover:opacity-95 disabled:opacity-60 flex items-center gap-2"
          >
            {busy === "analyze" && <Loader2 size={14} className="animate-spin" />}
            Analyze Risk
          </button>

          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as "max_sharpe" | "min_volatility")}
            className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          >
            <option value="max_sharpe">Maximize Sharpe Ratio</option>
            <option value="min_volatility">Minimize Volatility</option>
          </select>

          <button
            onClick={handleOptimize}
            disabled={busy !== null}
            className="px-4 py-2 rounded-md border border-border text-sm font-semibold hover:bg-secondary disabled:opacity-60 flex items-center gap-2"
          >
            {busy === "optimize" && <Loader2 size={14} className="animate-spin" />}
            Optimize
          </button>

          {saved !== null && (
            <button
              onClick={handleSave}
              disabled={busy !== null}
              className="px-4 py-2 rounded-md border border-border text-sm font-semibold hover:bg-secondary disabled:opacity-60 flex items-center gap-2 ml-auto"
            >
              {busy === "save" ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              Save
            </button>
          )}
        </div>
      </div>

      {saved && saved.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-5">
          <div className="text-sm font-semibold mb-3 flex items-center gap-2">
            <FolderOpen size={15} /> Saved Portfolios
          </div>
          <div className="flex flex-wrap gap-2">
            {saved.map((p) => (
              <button
                key={p.id}
                onClick={() => loadSaved(p)}
                className="px-3 py-1.5 rounded-md border border-border text-sm hover:border-primary/50 hover:bg-secondary/40 transition"
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {risk && (
        <section className="bg-card border border-border rounded-xl p-5">
          <div className="text-sm font-semibold mb-4">Risk Metrics</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            <MetricCard label="Volatility" value={numberToPercent(risk.metrics.volatility)} />
            <MetricCard label="Sharpe Ratio" value={formatNumber(risk.metrics.sharpe_ratio)} />
            <MetricCard label="Max Drawdown" value={numberToPercent(risk.metrics.max_drawdown)} tone="danger" />
            <MetricCard label="VaR (95%)" value={numberToPercent(risk.metrics.var_95)} tone="warning" />
          </div>
          <div className="grid md:grid-cols-2 gap-6 items-center">
            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-2">Allocation</div>
              <AllocationPie weights={risk.weights} />
            </div>
            {risk.metrics.correlation_matrix && (
              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-2">Correlation Matrix</div>
                <CorrelationHeatmap tickers={Object.keys(risk.weights)} matrix={risk.metrics.correlation_matrix} />
              </div>
            )}
          </div>
        </section>
      )}

      {optimization && (
        <section className="bg-card border border-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold">Optimization Result</div>
            <Badge tone="muted">{optimization.optimization.method}</Badge>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-5">
            <MetricCard label="Expected Return" value={numberToPercent(optimization.optimization.expected_return)} />
            <MetricCard label="Expected Volatility" value={numberToPercent(optimization.optimization.expected_volatility)} />
            <MetricCard label="Expected Sharpe" value={formatNumber(optimization.optimization.expected_sharpe)} />
          </div>

          <div className="grid md:grid-cols-2 gap-6 items-start">
            <div>
              <div className="text-xs font-semibold text-muted-foreground mb-2">Recommended Allocation</div>
              <AllocationPie weights={optimization.optimization.recommended_weights} />
            </div>
            {optimization.comparison.current && optimization.comparison.recommended && (
              <div>
                <div className="text-xs font-semibold text-muted-foreground mb-2">Current vs. Recommended</div>
                <ComparisonBarChart
                  current={optimization.comparison.current}
                  recommended={optimization.comparison.recommended}
                />
              </div>
            )}
          </div>

          {optimization.optimization.warnings.length > 0 && (
            <div className="mt-4 text-xs text-warning">{optimization.optimization.warnings.join(", ")}</div>
          )}
        </section>
      )}

      <p className="text-xs text-muted-foreground text-center px-4">
        This is an analytical scenario based on historical data, not personalized financial advice.
      </p>
    </div>
  );
};
