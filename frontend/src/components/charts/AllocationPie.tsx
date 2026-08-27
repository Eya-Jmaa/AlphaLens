import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

// Validated categorical order (see dataviz skill) - capped at 4 direct slots,
// anything past that folds into "Other" rather than generating new hues.
const SLOT_COLORS = ["var(--viz-series-1)", "var(--viz-series-2)", "var(--viz-series-3)", "var(--viz-series-4)"];
const OTHER_COLOR = "hsl(var(--muted-foreground))";
const MAX_SLICES = 4;

type Props = { weights: Record<string, number>; height?: number };

export const AllocationPie: React.FC<Props> = ({ weights, height = 240 }) => {
  const entries = Object.entries(weights)
    .filter(([, w]) => w > 0)
    .sort((a, b) => b[1] - a[1]);

  const top = entries.slice(0, MAX_SLICES);
  const rest = entries.slice(MAX_SLICES);
  const otherTotal = rest.reduce((sum, [, w]) => sum + w, 0);

  const data = [
    ...top.map(([ticker, weight]) => ({ name: ticker, value: weight })),
    ...(otherTotal > 0 ? [{ name: "Other", value: otherTotal }] : []),
  ];

  return (
    <div className="viz-root">
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius="55%" outerRadius="85%" paddingAngle={2}>
            {data.map((entry, i) => (
              <Cell
                key={entry.name}
                fill={i < top.length ? SLOT_COLORS[i] : OTHER_COLOR}
                stroke="hsl(var(--card))"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`}
            contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
