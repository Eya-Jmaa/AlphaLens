import React from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ZAxis,
} from "recharts";
import { EfficientFrontierPoint } from "../../types";

type Marker = { label: string; return_rate: number; volatility: number };

type Props = {
  frontier: EfficientFrontierPoint[];
  current?: { return: number; volatility: number };
  recommended?: { return: number; volatility: number };
  height?: number;
};

/** Volatility (x) vs. expected return (y) scatter of the real efficient frontier
 * returned by POST /api/v1/portfolio/optimize, with the current and recommended
 * portfolios marked - all backend-computed (PyPortfolioOpt), nothing invented. */
export const EfficientFrontier: React.FC<Props> = ({ frontier, current, recommended, height = 320 }) => {
  const frontierPoints = frontier.map((p) => ({ x: p.volatility * 100, y: p.return_rate * 100, sharpe: p.sharpe }));

  const markers: Marker[] = [];
  if (current) markers.push({ label: "Current", volatility: current.volatility, return_rate: current.return });
  if (recommended) markers.push({ label: "Recommended", volatility: recommended.volatility, return_rate: recommended.return });

  return (
    <div className="viz-root">
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid stroke="var(--viz-grid)" />
          <XAxis
            type="number"
            dataKey="x"
            name="Volatility"
            unit="%"
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
            tickLine={false}
            label={{ value: "Volatility (annualized)", position: "insideBottom", offset: -2, fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Expected Return"
            unit="%"
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            axisLine={false}
            tickLine={false}
            width={48}
            label={{ value: "Expected return", angle: -90, position: "insideLeft", fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          />
          <ZAxis range={[40, 40]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 6, fontSize: 12 }}
            formatter={(value) => `${Number(value).toFixed(2)}%`}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Scatter name="Efficient frontier" data={frontierPoints} fill="var(--viz-series-1)" opacity={0.65} />
          {current && (
            <Scatter
              name="Current portfolio"
              data={[{ x: current.volatility * 100, y: current.return * 100 }]}
              fill="var(--viz-series-3)"
              shape="diamond"
              legendType="diamond"
            />
          )}
          {recommended && (
            <Scatter
              name="Recommended"
              data={[{ x: recommended.volatility * 100, y: recommended.return * 100 }]}
              fill="var(--viz-series-2)"
              shape="star"
              legendType="star"
            />
          )}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};
