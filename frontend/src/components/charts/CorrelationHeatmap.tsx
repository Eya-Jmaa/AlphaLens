import React from "react";

type Props = { tickers: string[]; matrix: number[][] };

// Diverging blue (positive) <-> red (negative) around a neutral gray midpoint at 0,
// per the dataviz skill's diverging-pair rule for polarity data.
function colorFor(value: number): string {
  const clamped = Math.max(-1, Math.min(1, value));
  if (Math.abs(clamped) < 0.02) return "var(--viz-diverging-mid)";
  const alpha = Math.abs(clamped) * 0.85 + 0.1;
  const color = clamped >= 0 ? "var(--viz-diverging-pos)" : "var(--viz-diverging-neg)";
  return `color-mix(in srgb, ${color} ${Math.round(alpha * 100)}%, var(--viz-diverging-mid))`;
}

export const CorrelationHeatmap: React.FC<Props> = ({ tickers, matrix }) => {
  if (!tickers.length || !matrix.length) return null;

  return (
    <div className="viz-root overflow-x-auto">
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-1" />
            {tickers.map((t) => (
              <th key={t} className="p-1.5 font-medium text-muted-foreground text-center min-w-[52px]">
                {t}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={tickers[i]}>
              <th className="p-1.5 font-medium text-muted-foreground text-right pr-2">{tickers[i]}</th>
              {row.map((value, j) => (
                <td key={j} className="p-0.5 text-center">
                  <div
                    title={`${tickers[i]} vs ${tickers[j]}: ${value.toFixed(2)}`}
                    className="w-12 h-9 flex items-center justify-center rounded-sm text-[11px] font-medium tabular-nums"
                    style={{
                      backgroundColor: colorFor(value),
                      color: Math.abs(value) > 0.55 ? "white" : "hsl(var(--foreground))",
                    }}
                  >
                    {value.toFixed(2)}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
