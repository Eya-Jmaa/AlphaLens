import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

type Props = {
  current: { return: number; volatility: number; sharpe: number };
  recommended: { return: number; volatility: number; sharpe: number };
  height?: number;
};

export const ComparisonBarChart: React.FC<Props> = ({ current, recommended, height = 240 }) => {
  const data = [
    { metric: "Return", Current: current.return * 100, Recommended: recommended.return * 100 },
    { metric: "Volatility", Current: current.volatility * 100, Recommended: recommended.volatility * 100 },
    { metric: "Sharpe", Current: current.sharpe, Recommended: recommended.sharpe },
  ];

  return (
    <div className="viz-root">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }} barGap={4}>
          <CartesianGrid stroke="var(--viz-grid)" vertical={false} />
          <XAxis dataKey="metric" tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }} axisLine={{ stroke: "hsl(var(--border))" }} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} width={40} />
          <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Current" fill="var(--viz-series-3)" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Recommended" fill="var(--viz-series-1)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
