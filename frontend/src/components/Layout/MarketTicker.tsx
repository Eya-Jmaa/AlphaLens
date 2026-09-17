import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import clsx from "clsx";
import { TrendingUp, TrendingDown } from "lucide-react";
import { getMarketQuotes } from "../../api/client";
import { MarketQuote } from "../../types";
import { formatNumber } from "../../utils/formatters";

const SYMBOLS = ["SPY", "QQQ", "DIA", "^VIX", "NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"];

const DISPLAY_NAMES: Record<string, string> = {
  SPY: "S&P 500",
  QQQ: "NASDAQ 100",
  DIA: "DOW JONES",
  "^VIX": "CBOE VIX",
  NVDA: "NVIDIA",
  AAPL: "APPLE",
  MSFT: "MICROSOFT",
  TSLA: "TESLA",
  AMZN: "AMAZON",
  GOOGL: "ALPHABET",
};

const FALLBACK_QUOTES: MarketQuote[] = [
  { symbol: "SPY", name: "S&P 500", price: 563.85, change: 4.80, change_percent: 0.86 },
  { symbol: "QQQ", name: "NASDAQ 100", price: 489.10, change: 6.90, change_percent: 1.43 },
  { symbol: "DIA", name: "DOW JONES", price: 418.30, change: -0.95, change_percent: -0.23 },
  { symbol: "NVDA", name: "NVIDIA", price: 124.50, change: 3.90, change_percent: 3.24 },
  { symbol: "AAPL", name: "APPLE", price: 228.10, change: 2.60, change_percent: 1.15 },
  { symbol: "MSFT", name: "MICROSOFT", price: 448.20, change: -1.80, change_percent: -0.40 },
  { symbol: "TSLA", name: "TESLA", price: 245.80, change: 11.20, change_percent: 4.78 },
  { symbol: "AMZN", name: "AMAZON", price: 186.50, change: 2.10, change_percent: 1.14 },
  { symbol: "^VIX", name: "CBOE VIX", price: 15.20, change: -0.75, change_percent: -4.70 },
  { symbol: "GOOGL", name: "ALPHABET", price: 168.30, change: 1.20, change_percent: 0.72 },
];

export const MarketTicker: React.FC = () => {
  const navigate = useNavigate();
  const [quotes, setQuotes] = useState<MarketQuote[]>(FALLBACK_QUOTES);

  useEffect(() => {
    let cancelled = false;
    getMarketQuotes(SYMBOLS)
      .then((res) => {
        if (!cancelled && res.length > 0) {
          const valid = res.filter((q) => !q.error && q.price !== null);
          if (valid.length > 0) setQuotes(valid);
        }
      })
      .catch(() => {
        // Fallback quotes continue seamlessly
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Duplicate for seamless infinite loop
  const items = [...quotes, ...quotes];

  function handleSelectStock(symbol: string) {
    const cleanSym = symbol.replace("^", "");
    navigate("/analyze", {
      state: { query: `Analyze ${cleanSym} fundamentals, valuation, and news` },
    });
  }

  return (
    <div className="bg-card/90 backdrop-blur-sm border-b border-border/70 overflow-hidden py-2 select-none">
      <div className="animate-ticker flex w-max items-center">
        {items.map((q, i) => {
          const positive = (q.change_percent ?? 0) >= 0;
          return (
            <button
              key={`${q.symbol}-${i}`}
              onClick={() => handleSelectStock(q.symbol)}
              className="flex items-center gap-2.5 px-4 border-r border-border/60 shrink-0 text-xs hover:bg-muted/40 transition-colors py-1 focus:outline-none cursor-pointer"
              title={`Analyze ${DISPLAY_NAMES[q.symbol] ?? q.symbol}`}
            >
              <span className="font-bold text-foreground tracking-tight">
                {DISPLAY_NAMES[q.symbol] ?? q.symbol}
              </span>
              <span className="font-semibold text-muted-foreground font-tabular">
                ${formatNumber(q.price, 2)}
              </span>
              <span
                className={clsx(
                  "font-bold font-tabular flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10.5px]",
                  positive
                    ? "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-400"
                    : "text-rose-600 bg-rose-50 dark:bg-rose-950/40 dark:text-rose-400"
                )}
              >
                {positive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                {positive ? "+" : ""}
                {formatNumber(q.change_percent, 2)}%
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
