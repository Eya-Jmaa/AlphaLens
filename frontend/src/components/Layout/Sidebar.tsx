import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  PieChart,
  FileClock,
  Settings,
  HelpCircle,
  Activity,
  ArrowUpRight,
} from "lucide-react";
import clsx from "clsx";
import { useSystemHealth } from "../../hooks/useSystemHealth";

export const AlphaLensLogo: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
  <svg
    viewBox="0 0 32 32"
    className={clsx("shrink-0", className)}
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    {/* Rising financial chart bars */}
    <rect x="5.5" y="17" width="4.5" height="9.5" rx="1.8" fill="currentColor" fillOpacity="0.45" />
    <rect x="12.5" y="12" width="4.5" height="14.5" rx="1.8" fill="currentColor" fillOpacity="0.75" />
    <rect x="19.5" y="7" width="4.5" height="19.5" rx="1.8" fill="#1FC16B" />
    {/* Ascending growth vector / breakout arrow */}
    <path
      d="M6.5 15L13 9L18 12L25.5 4.5"
      stroke="#1FC16B"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M20.5 4.5H25.5V9.5"
      stroke="#1FC16B"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/analyze", label: "Research", icon: TrendingUp },
  { to: "/portfolio", label: "Portfolio", icon: PieChart },
  { to: "/reports", label: "Reports", icon: FileClock },
];

const WATCHLIST_STOCKS = [
  { ticker: "NVDA", name: "Nvidia", price: "$124.50", change: "+3.2%", positive: true },
  { ticker: "AAPL", name: "Apple", price: "$228.10", change: "+1.1%", positive: true },
  { ticker: "MSFT", name: "Microsoft", price: "$448.20", change: "-0.4%", positive: false },
  { ticker: "TSLA", name: "Tesla", price: "$245.80", change: "+4.8%", positive: true },
];

export const Sidebar: React.FC = () => {
  const { health, error } = useSystemHealth();
  const navigate = useNavigate();

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-border/70 bg-sidebar/80 backdrop-blur-md h-screen sticky top-0 select-none p-4 justify-between">
      <div className="space-y-6">
        {/* Brand Header with Financial Emblem */}
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-3 px-2 pt-1 text-left group focus:outline-none"
        >
          <div className="w-10 h-10 rounded-2xl bg-slate-900 text-white flex items-center justify-center shadow-md dark:bg-card dark:text-foreground dark:border dark:border-border transition-transform group-hover:scale-105">
            <AlphaLensLogo className="w-6 h-6 text-white dark:text-foreground" />
          </div>
          <div>
            <div className="text-base font-extrabold tracking-tight text-foreground leading-tight flex items-center gap-1">
              AlphaLens
            </div>
            <div className="text-[11px] font-medium text-muted-foreground leading-tight">
              Financial Intelligence
            </div>
          </div>
        </button>

        {/* Navigation - Reference High-Contrast Pills */}
        <div className="space-y-1">
          <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-subtle">
            Menu
          </div>
          <nav className="space-y-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold tracking-tight transition-all",
                    isActive
                      ? "bg-foreground text-background shadow-sm"
                      : "text-muted-foreground hover:bg-card hover:text-foreground"
                  )
                }
              >
                <Icon size={16} strokeWidth={2.2} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Watchlist Section - Reference Style */}
        <div className="space-y-2 pt-2">
          <div className="flex items-center justify-between px-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-subtle">
              Watchlist
            </span>
            <span className="text-[10px] text-muted-foreground font-semibold">Live</span>
          </div>

          <div className="space-y-1.5">
            {WATCHLIST_STOCKS.map((stock) => (
              <button
                key={stock.ticker}
                onClick={() =>
                  navigate("/analyze", {
                    state: { query: `Analyze ${stock.ticker} fundamental valuation and news` },
                  })
                }
                className="w-full flex items-center justify-between p-2 rounded-xl bg-card/60 hover:bg-card border border-border/40 hover:border-border transition-all shadow-[0_2px_8px_-2px_rgba(0,0,0,0.02)] group text-left"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-7 h-7 rounded-lg bg-background-secondary flex items-center justify-center font-bold text-[10px] text-foreground shrink-0 border border-border/60">
                    {stock.ticker.slice(0, 3)}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-foreground leading-tight group-hover:text-primary transition-colors">
                      {stock.ticker}
                    </div>
                    <div className="text-[10px] text-muted-foreground truncate leading-tight">
                      {stock.name}
                    </div>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-xs font-bold font-tabular text-foreground">
                    {stock.price}
                  </div>
                  <div
                    className={clsx(
                      "text-[10px] font-bold font-tabular flex items-center justify-end gap-0.5",
                      stock.positive ? "text-success" : "text-danger"
                    )}
                  >
                    {stock.positive ? "▲" : "▼"} {stock.change}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer System Status & Settings */}
      <div className="space-y-3 pt-4 border-t border-border/60">
        <div className="flex items-center justify-between px-2 text-xs">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Activity size={13} className="text-success" />
            <span className="text-[11px] font-medium">Market Data Feed</span>
          </div>
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
        </div>

        <div className="flex items-center justify-between px-1 text-muted-foreground pt-1">
          <button
            onClick={() => navigate("/")}
            className="p-2 rounded-xl hover:bg-card hover:text-foreground transition text-xs flex items-center gap-2 font-medium"
          >
            <Settings size={15} />
            <span>Preferences</span>
          </button>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="p-2 rounded-xl hover:bg-card hover:text-foreground transition"
            title="Documentation"
          >
            <HelpCircle size={15} />
          </a>
        </div>
      </div>
    </aside>
  );
};
