import React, { useEffect, useState } from "react";
import { ArrowRight, Scale, Search, Sparkles } from "lucide-react";
import clsx from "clsx";

type Props = {
  onSubmit: (q: string, debate: boolean) => void;
  isLoading?: boolean;
  examples?: string[];
  initialValue?: string;
};

const QUICK_TICKERS = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META"];

export const QueryInput: React.FC<Props> = ({ onSubmit, isLoading = false, examples = [], initialValue }) => {
  const [text, setText] = useState(initialValue ?? "");
  const [debate, setDebate] = useState(true);

  useEffect(() => {
    if (initialValue) setText(initialValue);
  }, [initialValue]);

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const q = text.trim();
    if (!q) return;
    onSubmit(q, debate);
  };

  function selectTicker(ticker: string) {
    setText(`Analyze ${ticker} valuation, growth catalysts, news, and SEC risk factors`);
  }

  return (
    <form onSubmit={submit} className="card space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/60 pb-3">
        <div>
          <h2 className="text-sm font-bold text-foreground">Equity Research &amp; Decision Desk</h2>
          <p className="text-xs text-muted-foreground">Multi-desk fundamental, risk, and SEC filing analysis</p>
        </div>
        <span className="text-[11px] font-semibold text-muted-foreground px-2.5 py-1 rounded-full bg-background-secondary">
          Live Data
        </span>
      </div>

      {/* Main Search Input */}
      <div className="space-y-3">
        <div className="relative flex items-center">
          <Search size={16} className="absolute left-4 text-muted-foreground pointer-events-none" />
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={isLoading}
            placeholder="Enter security ticker (e.g. NVDA, AAPL) or specific investment thesis to stress-test..."
            className="w-full rounded-2xl border border-border/80 bg-background/60 pl-11 pr-4 py-3.5 text-xs md:text-sm font-medium focus:outline-none focus:border-foreground focus:ring-1 focus:ring-foreground/20 disabled:opacity-60 transition shadow-inner"
          />
        </div>

        {/* Quick Tickers */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-semibold text-muted-foreground mr-1">Quick Select:</span>
          {QUICK_TICKERS.map((t) => (
            <button
              key={t}
              type="button"
              disabled={isLoading}
              onClick={() => selectTicker(t)}
              className="px-3 py-1 rounded-full text-xs font-bold bg-background-secondary hover:bg-foreground hover:text-background text-foreground transition-all disabled:opacity-60 shadow-sm"
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between flex-wrap gap-3 pt-2 border-t border-border/60">
        <label className="flex items-center gap-2 text-xs font-semibold text-foreground cursor-pointer select-none">
          <input
            type="checkbox"
            checked={debate}
            onChange={(e) => setDebate(e.target.checked)}
            disabled={isLoading}
            className="rounded-full border-border accent-foreground cursor-pointer w-4 h-4"
          />
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <Scale size={13} className="text-foreground" />
            Adversarial Investment Committee (Bull vs. Bear Debate)
          </span>
        </label>

        <button
          type="submit"
          disabled={isLoading || !text.trim()}
          className={clsx(
            "btn-pill-dark flex items-center gap-2",
            (isLoading || !text.trim()) && "opacity-50 cursor-not-allowed"
          )}
        >
          {isLoading ? "Executing Desks..." : "Generate Research Dossier"}
          {!isLoading && <ArrowRight size={14} />}
        </button>
      </div>

      {/* Examples */}
      {examples.length > 0 && !text && (
        <div className="pt-2 border-t border-border/40">
          <div className="text-[11px] font-bold text-muted-foreground mb-2">Example Directives:</div>
          <div className="flex flex-wrap gap-1.5">
            {examples.map((ex, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setText(ex)}
                disabled={isLoading}
                className="px-3 py-1.5 rounded-xl bg-background/80 border border-border/70 text-xs text-muted-foreground hover:text-foreground hover:border-foreground/40 transition text-left"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      )}
    </form>
  );
};
