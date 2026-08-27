import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Trash2, FileText, Loader2 } from "lucide-react";
import { deleteReport, getReport, listReports } from "../../api/client";
import { deleteReportFromHistory, loadReportHistory } from "../../utils/reportHistory";
import { formatDate, outlookTone } from "../../utils/formatters";
import { AnalysisResult } from "../../types";
import { Badge } from "../Common/Badge";
import { Spinner } from "../Common/Spinner";
import { ReportView } from "../Analysis/ReportView";
import { usePageMeta } from "../Layout/AppShell";

type Row = { id: string; query: string; outlook: string; createdAt: string; source: "backend" | "local" };

export const ReportsPage: React.FC = () => {
  usePageMeta({ title: "Reports", subtitle: "Your past analyses" });
  const [rows, setRows] = useState<Row[] | null>(null);
  const [usingBackend, setUsingBackend] = useState(false);
  const [selected, setSelected] = useState<AnalysisResult | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);

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
        // No database configured, or the backend is unreachable - fall back to
        // this browser's local history rather than showing an empty page.
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
      toast.error("Could not load that report.");
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
        toast.error("Could not delete that report.");
        return;
      }
    } else {
      deleteReportFromHistory(row.id);
    }
    setRows((prev) => prev?.filter((r) => r.id !== row.id) ?? prev);
    if (selected?.id === row.id) setSelected(null);
  }

  if (selected) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <button onClick={() => setSelected(null)} className="text-sm text-muted-foreground hover:text-foreground transition">
          &larr; Back to reports
        </button>
        <ReportView result={selected} />
      </div>
    );
  }

  if (rows === null) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size={28} />
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <FileText size={32} className="mx-auto text-muted-foreground mb-3" />
        <p className="text-sm font-medium">No saved reports yet</p>
        <p className="text-xs text-muted-foreground mt-1">
          {usingBackend
            ? "Reports are saved automatically after you run an analysis."
            : "No database is configured, so reports are only saved to this browser."}
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-3">
      {!usingBackend && (
        <p className="text-xs text-muted-foreground text-center mb-1">
          No database configured &mdash; showing reports saved locally in this browser only.
        </p>
      )}
      {rows.map((row) => (
        <div
          key={row.id}
          className="bg-card border border-border rounded-xl p-4 flex items-center justify-between gap-3 cursor-pointer hover:border-primary/50 transition"
          onClick={() => open(row)}
        >
          <div className="min-w-0">
            <div className="text-sm font-medium truncate">{row.query}</div>
            <div className="text-xs text-muted-foreground mt-1">{formatDate(row.createdAt)}</div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Badge tone={outlookTone(row.outlook)}>{row.outlook}</Badge>
            {loadingId === row.id ? (
              <Loader2 size={15} className="animate-spin text-muted-foreground" />
            ) : (
              <button
                onClick={(e) => remove(row, e)}
                aria-label="Delete report"
                className="p-1.5 text-muted-foreground hover:text-danger transition"
              >
                <Trash2 size={15} />
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
