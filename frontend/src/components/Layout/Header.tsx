import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Moon, Sun, Search, Circle, Command, Bell, HelpCircle } from "lucide-react";
import { searchCompanies } from "../../api/client";
import { CompanySearchResult } from "../../types";
import { useMarketHours } from "../../hooks/useMarketHours";
import { AlphaLensLogo } from "./Sidebar";

type HeaderProps = {
  darkMode: boolean;
  onToggleDarkMode: () => void;
  title: string;
  subtitle?: string;
};

export const Header: React.FC<HeaderProps> = ({ darkMode, onToggleDarkMode, title, subtitle }) => {
  const navigate = useNavigate();
  const marketOpen = useMarketHours();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CompanySearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const timer = setTimeout(() => {
      searchCompanies(query)
        .then(setResults)
        .catch(() => setResults([]));
    }, 180);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function selectCompany(result: CompanySearchResult) {
    setQuery("");
    setResults([]);
    setOpen(false);
    navigate("/analyze", { state: { query: `Analyze ${result.ticker} fundamentals, news, and SEC filings` } });
  }

  return (
    <header className="w-full bg-background/80 backdrop-blur-md sticky top-0 z-20 px-4 md:px-8 py-3 select-none">
      <div className="flex items-center justify-between gap-4 max-w-[1600px] mx-auto">
        {/* Title & Page context */}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="md:hidden w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0 shadow-sm dark:bg-card dark:text-foreground">
            <AlphaLensLogo className="w-5 h-5 text-white dark:text-foreground" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg md:text-xl font-extrabold tracking-tight text-foreground">
              {title}
            </h1>
            {subtitle && (
              <p className="text-xs text-muted-foreground font-medium hidden sm:block">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        {/* Search Bar - Reference Rounded Pill */}
        <div ref={containerRef} className="relative flex-1 max-w-md hidden sm:block">
          <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            placeholder="Search assets, tickers, or companies..."
            aria-label="Search company or ticker"
            className="w-full h-10 pl-11 pr-12 rounded-full border border-border/80 bg-card text-xs md:text-sm font-medium placeholder:text-subtle focus:outline-none focus:border-foreground focus:ring-1 focus:ring-foreground/20 transition shadow-sm"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-0.5 pointer-events-none text-subtle text-[10px] font-semibold border border-border px-1.5 py-0.5 rounded-full bg-background">
            <Command size={10} />K
          </div>

          {open && results.length > 0 && (
            <div className="absolute top-full mt-2 w-full rounded-2xl border border-border bg-card shadow-2xl overflow-hidden z-30 divide-y divide-border/60">
              <div className="px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-subtle bg-muted/30">
                Matching Assets
              </div>
              <div className="max-h-64 overflow-y-auto p-1">
                {results.map((r) => (
                  <button
                    key={r.ticker}
                    onClick={() => selectCompany(r)}
                    className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-xl text-xs text-left hover:bg-background-secondary transition"
                  >
                    <div className="min-w-0">
                      <div className="font-bold text-foreground truncate">{r.name}</div>
                      <div className="text-[10px] text-muted-foreground">US Equities</div>
                    </div>
                    <span className="text-xs font-bold text-foreground px-2 py-0.5 rounded-full bg-background border border-border shrink-0">
                      {r.ticker}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Status & Controls */}
        <div className="flex items-center gap-3 shrink-0">
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border/80 bg-card text-xs font-semibold text-foreground shadow-sm"
            title="NYSE / NASDAQ Regular Session"
          >
            <Circle
              size={7}
              className={marketOpen ? "fill-success text-success animate-pulse" : "fill-subtle text-subtle"}
              strokeWidth={0}
            />
            <span className="hidden md:inline text-muted-foreground font-normal">US Market</span>
            <span className={marketOpen ? "text-success font-bold" : "text-subtle"}>
              {marketOpen ? "Open" : "Closed"}
            </span>
          </div>

          <button
            onClick={onToggleDarkMode}
            aria-label="Toggle theme"
            className="w-10 h-10 flex items-center justify-center rounded-full border border-border/80 bg-card text-foreground hover:bg-background-secondary transition shadow-sm"
            title="Toggle theme"
          >
            {darkMode ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </div>
    </header>
  );
};
