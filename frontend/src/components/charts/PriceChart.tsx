import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { ChartPoint } from "../../api/client";

type Props = { data: ChartPoint[]; height?: number };

function tickEveryN<T>(data: T[], maxTicks = 6): T[] {
  if (data.length <= maxTicks) return data;
  const step = Math.ceil(data.length / maxTicks);
  return data.filter((_, i) => i % step === 0);
}

export const PriceChart: React.FC<Props> = ({ data, height = 260 }) => {
  const tickDates = new Set(tickEveryN(data).map((d) => d.date));

  return (
    <div className="viz-root">
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--viz-grid)" vertical={false} />
          <XAxis
            dataKey="date"
            ticks={Array.from(tickDates)}
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            axisLine={{ stroke: "hsl(var(--border))" }}
            tickLine={false}
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="close" name="Close" stroke="var(--viz-series-1)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="sma_20" name="SMA 20" stroke="var(--viz-series-2)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="sma_50" name="SMA 50" stroke="var(--viz-series-3)" strokeWidth={2} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export const RsiChart: React.FC<Props> = ({ data, height = 140 }) => {
  const tickDates = new Set(tickEveryN(data).map((d) => d.date));
  return (
    <div className="viz-root">
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--viz-grid)" vertical={false} />
          <XAxis dataKey="date" ticks={Array.from(tickDates)} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} axisLine={{ stroke: "hsl(var(--border))" }} tickLine={false} />
          <YAxis domain={[0, 100]} ticks={[30, 50, 70]} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} axisLine={false} tickLine={false} width={32} />
          <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
          <Line type="monotone" dataKey="rsi" name="RSI (14)" stroke="var(--viz-series-4)" strokeWidth={2} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
