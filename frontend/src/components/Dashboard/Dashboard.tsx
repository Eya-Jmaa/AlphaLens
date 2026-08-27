import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Newspaper, PieChart, ShieldAlert, Sparkles, FileText } from "lucide-react";
import { loadReportHistory, ReportHistoryEntry } from "../../utils/reportHistory";
import { formatDate, outlookTone } from "../../utils/formatters";
import { Badge } from "../Common/Badge";
import { usePageMeta } from "../Layout/AppShell";

const EXAMPLES = [
  "Analyze NVIDIA including news and risk",
  "Compare AAPL, MSFT, and GOOGL",
  "What are Tesla's biggest risks?",
  "Analyze my portfolio with AAPL 30%, MSFT 30%, NVDA 40%",
];

const PIPELINE = [
  { label: "Supervisor", icon: Sparkles, desc: "Extracts tickers, routes to the agents this query needs" },
  { label: "Stock & Fundamentals", icon: PieChart, desc: "Live market data, valuation, technical indicators" },
  { label: "News & Risk", icon: ShieldAlert, desc: "Sentiment analysis and volatility / VaR / drawdown" },
  { label: "SEC Filings", icon: FileText, desc: "RAG over real 10-K/10-Q filings, with citations" },
  { label: "Final Analyst", icon: Newspaper, desc: "Synthesizes every agent's evidence into one report" },
];

export const Dashboard: React.FC = () => {
  usePageMeta({ title: "Dashboard" });
  const navigate = useNavigate();
  const [recent, setRecent] = useState<ReportHistoryEntry[]>([]);

  useEffect(() => {
    setRecent(loadReportHistory().slice(0, 3));
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <section className="text-center py-6">
        <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
          Financial Intelligence, Powered by Multi-Agent AI
        </h1>
        <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
          Ask about a stock, compare companies, or analyze a portfolio &mdash; FinAgent routes your
          question to real market data, news, risk, and SEC filing agents, then synthesizes one
          evidence-backed report.
        </p>
        <button
          onClick={() => navigate("/analyze")}
          className="mt-5 inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-primary text-primary-foreground font-semibold hover:opacity-95 transition"
        >
          Start an analysis <ArrowRight size={16} />
        </button>
      </section>

      <section>
        <div className="text-sm font-semibold mb-3 text-muted-foreground">Try an example</div>
        <div className="grid sm:grid-cols-2 gap-3">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => navigate("/analyze", { state: { query: ex } })}
              className="text-left bg-card border border-border rounded-lg p-4 text-sm hover:border-primary/50 hover:bg-secondary/40 transition"
            >
              {ex}
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="text-sm font-semibold mb-3 text-muted-foreground">How it works</div>
        <div className="grid sm:grid-cols-5 gap-3">
          {PIPELINE.map(({ label, icon: Icon, desc }) => (
            <div key={label} className="bg-card border border-border rounded-lg p-3.5">
              <Icon size={16} className="text-primary mb-2" />
              <div className="text-xs font-semibold">{label}</div>
              <div className="text-[11px] text-muted-foreground mt-1 leading-snug">{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {recent.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-semibold text-muted-foreground">Recent analyses</div>
            <button onClick={() => navigate("/reports")} className="text-xs text-primary hover:opacity-80">
              View all
            </button>
          </div>
          <div className="space-y-2">
            {recent.map((entry) => (
              <div key={entry.id} className="bg-card border border-border rounded-lg p-3.5 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm truncate">{entry.query}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{formatDate(entry.generatedAt)}</div>
                </div>
                <Badge tone={outlookTone(entry.outlook)}>{entry.outlook}</Badge>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
