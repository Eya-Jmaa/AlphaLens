/**
 * Composite risk score, derived entirely from real backend-computed risk
 * metrics (volatility, max drawdown, VaR, Sharpe, concentration) - never
 * invented. Each factor is normalized to a 0-100 "risk contribution" against
 * reasonable real-world bands for public equities, then weight-averaged.
 * There is no "regulatory risk" factor - no data source backs one.
 */

function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n));
}

export interface RiskFactor {
  label: string;
  score: number; // 0-100, higher = riskier
  detail: string;
}

export interface RiskMetricsInput {
  volatility: number;
  max_drawdown: number;
  var_95: number;
  sharpe_ratio: number;
  herfindahl_index?: number | null;
}

export interface CompositeRisk {
  score: number; // 0-100
  band: "Low" | "Moderate" | "Elevated" | "High";
  factors: RiskFactor[];
}

export function computeCompositeRisk(metrics: RiskMetricsInput, avgPeRatio?: number | null): CompositeRisk {
  const volatilityRisk = clamp01(metrics.volatility / 0.6) * 100;
  const drawdownRisk = clamp01(Math.abs(metrics.max_drawdown) / 0.6) * 100;
  const varRisk = clamp01(Math.abs(metrics.var_95) / 0.5) * 100;
  const sharpeRisk = clamp01((1.5 - metrics.sharpe_ratio) / 3) * 100;

  const factors: RiskFactor[] = [
    { label: "Market volatility", score: volatilityRisk, detail: `Annualized volatility ${(metrics.volatility * 100).toFixed(1)}%` },
    { label: "Drawdown / tail risk", score: (drawdownRisk + varRisk) / 2, detail: `Max drawdown ${(metrics.max_drawdown * 100).toFixed(1)}%, VaR 95% ${(metrics.var_95 * 100).toFixed(1)}%` },
    { label: "Risk-adjusted return", score: sharpeRisk, detail: `Sharpe ratio ${metrics.sharpe_ratio.toFixed(2)}` },
  ];

  const weights = [0.35, 0.35, 0.2];

  if (metrics.herfindahl_index !== null && metrics.herfindahl_index !== undefined) {
    factors.push({
      label: "Concentration",
      score: clamp01(metrics.herfindahl_index) * 100,
      detail: `Herfindahl index ${metrics.herfindahl_index.toFixed(2)} (1.0 = single holding)`,
    });
    weights.push(0.1);
  }

  if (avgPeRatio !== null && avgPeRatio !== undefined && avgPeRatio > 0) {
    const valuationRisk = clamp01((avgPeRatio - 10) / 35) * 100;
    factors.push({ label: "Valuation", score: valuationRisk, detail: `Avg. P/E ratio ${avgPeRatio.toFixed(1)}` });
    weights.push(0.15);
  }

  const weightSum = weights.reduce((a, b) => a + b, 0);
  const score = factors.reduce((sum, f, i) => sum + f.score * weights[i], 0) / weightSum;

  let band: CompositeRisk["band"] = "Low";
  if (score >= 70) band = "High";
  else if (score >= 50) band = "Elevated";
  else if (score >= 30) band = "Moderate";

  return { score: Math.round(score), band, factors };
}
