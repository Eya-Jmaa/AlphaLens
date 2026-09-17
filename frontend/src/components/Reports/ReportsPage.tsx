import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import clsx from "clsx";
import { Trash2, FileText, Loader2, ArrowLeft, Search, Filter } from "lucide-react";
import { deleteReport, getReport, listReports } from "../../api/client";
import { deleteReportFromHistory, loadReportHistory } from "../../utils/reportHistory";
import { formatDate, outlookTone } from "../../utils/formatters";
import { AnalysisResult } from "../../types";
import { Badge } from "../Common/Badge";
import { Spinner } from "../Common/Spinner";
import { ReportView } from "../Analysis/ReportView";
import { usePageMeta } from "../Layout/AppShell";

type Row = { id: string; query: string; outlook: string; createdAt: string; source: "backend" | "local" };
type SortKey = "date" | "query" | "outlook";

export const ReportsPage: React.FC = () => {
  usePageMeta({ title: "Research Archive", subtitle: "Institutional Coverage & Stored Equity Dossiers" });
  const [rows, setRows] = useState<Row[] | null>(null);
  const [usingBackend, setUsingBackend] = useState(false);
  const [selected, setSelected] = useState<AnalysisResult | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [searchFilter, setSearchFilter] = useState("");
  const [outlookFilter, setOutlookFilter] = useState<string>("ALL");

  useEffect(() => {
    listReports()
      .then((reports) => {
        setUsingBackend(true);
        setRows(
          reports.map((r) => ({
            id: r.id,
            query: r.query,
            outlook: r.overall_outlook,
            createdAt: r.created_at,
            source: "backend",
          }))
        );
      })
      .catch(() => {
        setUsingBackend(false);
        setRows(
          loadReportHistory().map((h) => ({
            id: h.id,
            query: h.query,
            outlook: h.outlook,
            createdAt: h.generatedAt,
            source: "local",
          }))
        );
      });
  }, []);

  async function open(row: Row) {
    setLoadingId(row.id);
    try {
      if (row.source === "backend") {
        setSelected(await getReport(row.id));
      } else {
        const local = loadReportHistory().find((h) => h.id === row.id);
        if (local) setSelected(local.result);
      }
    } catch (err) {
      toast.error("Could not retrieve dossier from warehouse.");
    } finally {
      setLoadingId(null);
    }
  }

  async function remove(row: Row, e: React.MouseEvent) {
    e.stopPropagation();
    if (row.source === "backend") {
      try {
        await deleteReport(row.id);
      } catch {
        toast.error("Could not delete report.");
        return;
      }
    } else {
      deleteReportFromHistory(row.id);
    }
    setRows((prev) => prev?.filter((r) => r.id !== row.id) ?? prev);
    if (selected?.id === row.id) setSelected(null);
    toast.success("Dossier removed.");
  }

  if (selected) {
    return (
      <div className="max-w-6xl mx-auto space-y-4">
        <button
          onClick={() => setSelected(null)}
          className="no-print inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-muted-foreground hover:text-foreground transition pb-2"
        >
          <ArrowLeft size={13} /> Return to Research Archive
        </button>
        <ReportView result={selected} />
      </div>
    );
  }

  if (rows === null) {
    return (
      <div className="flex justify-center py-24">
        <Spinner size={32} />
      </div>
    );
  }

  const filtered = rows.filter((r) => {
    const matchesSearch = !searchFilter.trim() || r.query.toLowerCase().includes(searchFilter.toLowerCase());
    const matchesOutlook = outlookFilter === "ALL" || r.outlook.toUpperCase().includes(outlookFilter);
    return matchesSearch && matchesOutlook;
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortKey === "query") return a.query.localeCompare(b.query);
    if (sortKey === "outlook") return a.outlook.localeCompare(b.outlook);
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Archive Header & Filters */}
      <div className="bg-card border border-border rounded p-4 md:p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-3">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wide text-foreground">
              Equity Research Archive
            </h2>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Historical dossiers, investment committee verdicts, and factor analyses.
            </p>
          </div>
          <span className="text-xs font-mono text-muted-foreground">
            {rows.length} Total Dossiers &middot; {usingBackend ? "Warehouse Connected" : "Local Browser Session"}
          </span>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-subtle" />
            <input
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Filter dossiers by ticker or keyword..."
              className="w-full h-8 pl-8 pr-3 rounded border border-border bg-background text-xs font-medium focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono uppercase text-subtle mr-1">Outlook:</span>
            {["ALL", "POSITIVE", "NEUTRAL", "NEGATIVE"].map((f) => (
              <button
                key={f}
                onClick={() => setOutlookFilter(f)}
                className={clsx(
                  "px-2.5 py-1 rounded text-[10px] font-mono font-bold uppercase tracking-wider transition",
                  outlookFilter === f
                    ? "bg-primary text-primary-foreground"
                    : "bg-background border border-border text-muted-foreground hover:text-foreground"
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="bg-card border border-border rounded p-12 text-center space-y-2">
          <FileText size={32} className="mx-auto text-subtle" />
          <div className="text-sm font-bold text-foreground">No Research Dossiers Found</div>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            {rows.length === 0
              ? "Run an equity research query on the Research Desk to generate your first institutional dossier."
              : "No dossiers match the current search filters."}
          </p>
        </div>
      ) : (
        <div className="bg-card border border-border rounded overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-xs min-w-[560px]">
              <thead>
                <tr className="bg-muted/40 text-[10px] uppercase font-mono tracking-wider text-subtle border-b border-border">
                  <th
                    onClick={() => setSortKey("query")}
                    className="text-left font-semibold px-4 py-2.5 cursor-pointer hover:text-foreground"
                  >
                    Research Directive
                  </th>
                  <th
                    onClick={() => setSortKey("outlook")}
                    className="text-center font-semibold px-4 py-2.5 cursor-pointer hover:text-foreground"
                  >
                    Consensus Outlook
                  </th>
                  <th
                    onClick={() => setSortKey("date")}
                    className="text-right font-semibold px-4 py-2.5 cursor-pointer hover:text-foreground"
                  >
                    Timestamp
                  </th>
                  <th className="w-10" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60 font-mono">
                {sorted.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => open(row)}
                    className="cursor-pointer hover:bg-elevated/60 transition-colors group"
                  >
                    <td className="px-4 py-3 font-sans font-medium text-foreground">
                      <div className="truncate max-w-lg group-hover:text-primary transition-colors">
                        {row.query}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge tone={outlookTone(row.outlook)} className="text-[10px]">
                        {row.outlook}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right text-muted-foreground text-[11px] whitespace-nowrap">
                      {formatDate(row.createdAt)}
                    </td>
                    <td className="px-2 py-3 text-center">
                      {loadingId === row.id ? (
                        <Loader2 size={14} className="animate-spin text-primary mx-auto" />
                      ) : (
                        <button
                          onClick={(e) => remove(row, e)}
                          aria-label="Delete report"
                          className="p-1 text-subtle hover:text-danger transition"
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
