import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  TrendingUp,
  TrendingDown,
  Star,
  Plus,
  ArrowUpRight,
  ArrowDownLeft,
  ArrowLeftRight,
  MoreHorizontal,
  SlidersHorizontal,
  ChevronDown,
  Calendar,
  Layers,
  Search,
} from "lucide-react";
import clsx from "clsx";
import { getMarketQuotes, ChartPoint, getChartSeries } from "../../api/client";
import { MarketQuote } from "../../types";
import { formatNumber, formatCurrency } from "../../utils/formatters";
import { PriceChart, RsiChart } from "../charts/PriceChart";
import { usePageMeta } from "../Layout/AppShell";

interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  points: number[];
}

const DEFAULT_WATCHLIST: WatchlistItem[] = [
  { symbol: "NVDA", name: "Nvidia Corp", price: 124.5, change: 3.24, points: [118, 120, 119, 122, 121, 125, 124.5] },
  { symbol: "AAPL", name: "Apple Inc", price: 228.1, change: 1.15, points: [224, 225, 226, 225, 227, 228, 228.1] },
  { symbol: "BTC", name: "Bitcoin", price: 63942.0, change: -2.14, points: [66000, 65200, 65800, 64500, 64200, 63942] },
  { symbol: "MSFT", name: "Microsoft", price: 448.2, change: 0.85, points: [442, 444, 443, 446, 447, 448.2] },
];

export const Dashboard: React.FC = () => {
  usePageMeta({ title: "Dashboard", subtitle: "Financial intelligence, real-time charts & portfolio balance" });
  const navigate = useNavigate();

  const [activeTicker, setActiveTicker] = useState("NVDA");
  const [activeTimeframe, setActiveTimeframe] = useState("1D");
  const [chartData, setChartData] = useState<ChartPoint[] | null>(null);
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  const [swapAmount, setSwapAmount] = useState("4,582");
  const [selectedAsset, setSelectedAsset] = useState("NVDA");

  useEffect(() => {
    let cancelled = false;
    getChartSeries(activeTicker, "1mo")
      .then((data) => {
        if (!cancelled) setChartData(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [activeTicker]);

  useEffect(() => {
    let cancelled = false;
    getMarketQuotes(["NVDA", "AAPL", "MSFT", "TSLA", "SPY", "QQQ"])
      .then((res) => {
        if (!cancelled) {
          const map: Record<string, MarketQuote> = {};
          res.forEach((q) => {
            map[q.symbol] = q;
          });
          setQuotes(map);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const activeQuote = quotes[activeTicker] || { price: 124.5, change_percent: 3.24 };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Bento Row: My Wallet / Watchlist / Action Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* 1. Hero Financial Portfolio Balance Card (Reference Left Card) */}
        <div className="lg:col-span-4 card flex flex-col justify-between space-y-6 bg-card">
          <div className="text-center pt-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Market Portfolio Value
            </span>
            <div className="mt-2 text-3xl md:text-4xl font-extrabold tracking-tight text-foreground font-tabular">
              $142,745.80
            </div>
            <div className="mt-1.5 inline-flex items-center gap-1 text-xs font-bold text-success font-tabular">
              <TrendingUp size={13} />
              <span>+ $27,168 (21.4%) last month</span>
            </div>
          </div>

          {/* Pill Action Controls (Reference Pill Capsule) */}
          <div className="flex items-center justify-center gap-3 pt-2">
            <div className="inline-flex items-center rounded-full bg-background-secondary border border-border/80 p-1.5 shadow-sm">
              <button
                onClick={() => navigate("/analyze", { state: { query: "Analyze AAPL and NVDA portfolio risk" } })}
                className="w-12 h-12 rounded-full flex items-center justify-center text-foreground hover:bg-card transition"
                title="Deposit / Analyze"
              >
                <ArrowDownLeft size={20} />
              </button>
              <div className="w-px h-6 bg-border" />
              <button
                onClick={() => navigate("/portfolio")}
                className="w-12 h-12 rounded-full flex items-center justify-center text-foreground hover:bg-card transition"
                title="Send / Rebalance"
              >
                <ArrowUpRight size={20} />
              </button>
            </div>

            <button
              onClick={() => navigate("/analyze")}
              className="w-14 h-14 rounded-full bg-foreground text-background flex items-center justify-center hover:opacity-90 active:scale-95 transition shadow-md"
              title="Launch Research Directive"
            >
              <Plus size={24} strokeWidth={2.5} />
            </button>
          </div>
        </div>

        {/* 2. Watchlist Card with SVG Sparklines (Reference Middle Card) */}
        <div className="lg:col-span-4 card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground">Watchlist</h3>
            <button
              onClick={() => navigate("/analyze")}
              className="p-1.5 rounded-lg hover:bg-background-secondary text-muted-foreground transition"
            >
              <MoreHorizontal size={16} />
            </button>
          </div>

          <div className="space-y-2.5">
            {DEFAULT_WATCHLIST.map((item) => {
              const positive = item.change >= 0;
              return (
                <button
                  key={item.symbol}
                  onClick={() => setActiveTicker(item.symbol)}
                  className={clsx(
                    "w-full flex items-center justify-between p-2.5 rounded-2xl border transition-all text-left group",
                    activeTicker === item.symbol
                      ? "bg-background-secondary/80 border-border shadow-sm"
                      : "bg-background/40 hover:bg-background-secondary/50 border-transparent hover:border-border/60"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-foreground text-background flex items-center justify-center font-extrabold text-xs shrink-0 shadow-sm">
                      {item.symbol.slice(0, 3)}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                        {item.name}
                      </div>
                      <div className="text-[10px] text-muted-foreground uppercase font-semibold">
                        {item.symbol}
                      </div>
                    </div>
                  </div>

                  {/* Smooth Sparkline SVG */}
                  <div className="w-16 h-6 shrink-0 px-1">
                    <svg viewBox="0 0 60 24" className="w-full h-full overflow-visible">
                      <path
                        d={`M 0 ${positive ? 18 : 6} Q 15 ${positive ? 8 : 16}, 30 ${positive ? 14 : 10} T 60 ${positive ? 4 : 20}`}
                        fill="none"
                        stroke={positive ? "#1FC16B" : "#FA4D56"}
                        strokeWidth="2.2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="text-xs font-bold font-tabular text-foreground">
                      ${formatNumber(item.price, 2)}
                    </div>
                    <div
                      className={clsx(
                        "text-[10px] font-bold font-tabular flex items-center justify-end gap-0.5",
                        positive ? "text-success" : "text-danger"
                      )}
                    >
                      {positive ? "▲" : "▼"} {Math.abs(item.change)}%
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Deep Petrol Card (Reference Right Panel: Transfer / Research) */}
        <div className="lg:col-span-4 rounded-2xl md:rounded-3xl petrol-card p-5 md:p-6 flex flex-col justify-between space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="inline-flex rounded-full bg-white/10 p-1 backdrop-blur-sm border border-white/15">
              <button className="px-3.5 py-1 rounded-full text-xs font-bold bg-white text-slate-900 shadow-sm">
                Deep Research
              </button>
              <button
                onClick={() => navigate("/portfolio")}
                className="px-3.5 py-1 rounded-full text-xs font-semibold text-white/80 hover:text-white transition"
              >
                Rebalance
              </button>
            </div>
            <span className="text-[10px] font-mono uppercase text-white/70">Live Desk</span>
          </div>

          {/* Allocation Converter Panels */}
          <div className="space-y-2 relative">
            <div className="rounded-2xl bg-black/20 p-3.5 border border-white/10">
              <div className="flex justify-between text-[11px] text-white/70 mb-1">
                <span>Security Target</span>
                <span>Active Coverage</span>
              </div>
              <div className="flex items-center justify-between">
                <input
                  value={swapAmount}
                  onChange={(e) => setSwapAmount(e.target.value)}
                  className="bg-transparent text-xl font-extrabold text-white focus:outline-none w-32 font-tabular"
                />
                <span className="px-2.5 py-1 rounded-full bg-white/15 text-xs font-bold border border-white/20">
                  {selectedAsset}
                </span>
              </div>
            </div>

            {/* Middle Swap Button */}
            <div className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 top-1/2 z-10">
              <button
                onClick={() => setSelectedAsset(selectedAsset === "NVDA" ? "AAPL" : "NVDA")}
                className="w-8 h-8 rounded-full bg-white text-slate-900 flex items-center justify-center shadow-lg hover:rotate-180 transition-transform duration-300"
              >
                <ArrowLeftRight size={13} />
              </button>
            </div>

            <div className="rounded-2xl bg-black/20 p-3.5 border border-white/10">
              <div className="flex justify-between text-[11px] text-white/70 mb-1">
                <span>Benchmark Benchmark</span>
                <span>Market Ratio</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-xl font-extrabold text-white font-tabular">59.95</div>
                <span className="px-2.5 py-1 rounded-full bg-white/15 text-xs font-bold border border-white/20">
                  AAPL
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-1.5 text-[11px] text-white/80 pt-1 border-t border-white/15">
            <div className="flex justify-between">
              <span>Coverage Valuation</span>
              <span className="font-bold text-white font-tabular">1 NVDA = 0.54 AAPL</span>
            </div>
            <div className="flex justify-between">
              <span>SEC Filing Status</span>
              <span className="font-bold text-emerald-300">Audited 10-K Live</span>
            </div>
          </div>

          <button
            onClick={() =>
              navigate("/analyze", {
                state: { query: `Analyze ${activeTicker} valuation, news sentiment, and SEC filings` },
              })
            }
            className="w-full py-3 rounded-full bg-white text-slate-900 font-extrabold text-xs uppercase tracking-wider hover:bg-slate-100 transition shadow-lg text-center"
          >
            Launch Research Dossier ({activeTicker})
          </button>
        </div>
      </div>

      {/* Bottom Main Interactive Price & Candlestick Chart Card (Reference Bottom Card) */}
      <div className="card space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-4">
          <div className="flex items-center gap-3">
            <button className="w-8 h-8 rounded-full bg-background-secondary border border-border flex items-center justify-center text-amber-500">
              <Star size={14} className="fill-amber-500" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold text-foreground">{activeTicker}</span>
                <span className="text-xs font-semibold text-muted-foreground">US Equities</span>
              </div>
              <div className="text-xs text-muted-foreground">
                Marking Price: <span className="font-bold text-foreground font-tabular">${formatNumber(activeQuote.price ?? 124.5, 2)}</span>
                <span className="ml-2 font-bold text-success font-tabular">▲ 3.24% vs last week</span>
              </div>
            </div>
          </div>

          {/* Timeframe Buttons & Controls (Reference Middle-Right Controls) */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="inline-flex rounded-full bg-background-secondary border border-border/70 p-1">
              {["1M", "15M", "1H", "4H", "1D", "1W"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setActiveTimeframe(tf)}
                  className={clsx(
                    "px-3 py-1 rounded-full text-xs font-bold transition",
                    activeTimeframe === tf
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {tf}
                </button>
              ))}
            </div>

            <button
              onClick={() =>
                navigate("/analyze", {
                  state: { query: `Deep analysis on ${activeTicker} including news and risk` },
                })
              }
              className="px-4 py-2 rounded-full bg-foreground text-background text-xs font-bold hover:opacity-90 transition shadow-sm"
            >
              Analyze Security
            </button>
          </div>
        </div>

        {/* Chart Visualization */}
        <div className="pt-2">
          {chartData ? (
            <div className="space-y-4">
              <PriceChart data={chartData} height={280} />
              <div className="pt-2 border-t border-border/60">
                <div className="text-xs font-bold text-muted-foreground mb-2">
                  RSI Momentum Indicator (14-Period)
                </div>
                <RsiChart data={chartData} height={110} />
              </div>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-muted-foreground text-xs font-medium">
              Loading real-time price series for {activeTicker}...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
