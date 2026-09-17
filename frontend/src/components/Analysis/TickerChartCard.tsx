import React, { useEffect, useState } from "react";
import { ChartPoint, getChartSeries } from "../../api/client";
import { PriceChart, RsiChart } from "../charts/PriceChart";
import { Spinner } from "../Common/Spinner";

export const TickerChartCard: React.FC<{ ticker: string }> = ({ ticker }) => {
  const [series, setSeries] = useState<ChartPoint[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setSeries(null);
    setFailed(false);
    getChartSeries(ticker)
      .then((data) => {
        if (!cancelled) setSeries(data);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (failed) {
    return (
      <div className="bg-card border border-border rounded p-5 text-sm text-muted-foreground">
        Chart data unavailable for {ticker}.
      </div>
    );
  }

  if (!series) {
    return (
      <div className="bg-card border border-border rounded p-5 flex items-center justify-center h-72">
        <Spinner size={28} />
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded p-5">
      <div className="text-sm font-semibold mb-3">{ticker} &middot; Price &amp; Moving Averages</div>
      <PriceChart data={series} />
      <div className="text-xs font-semibold text-muted-foreground mt-4 mb-2">RSI (14)</div>
      <RsiChart data={series} />
    </div>
  );
};
