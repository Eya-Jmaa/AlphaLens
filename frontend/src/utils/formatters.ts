export function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function numberToPercent(n: number | null | undefined, digits = 1): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  return `${(n * 100).toFixed(digits)}%`;
}

export function formatNumber(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  // Fixed locale (not the visitor's system locale) so figures are never
  // ambiguous - e.g. a comma-as-decimal-separator locale misreading "31,94".
  return n.toLocaleString("en-US", { maximumFractionDigits: digits });
}

export function formatCurrency(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000_000) return `$${(n / 1_000_000_000_000).toFixed(2)}T`;
  if (abs >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${n.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  return `$${n.toFixed(2)}`;
}

export function outlookTone(outlook: string): "success" | "danger" | "warning" | "muted" {
  switch (outlook) {
    case "Strongly Positive":
    case "Positive":
      return "success";
    case "Strongly Negative":
    case "Negative":
      return "danger";
    case "Insufficient Evidence":
      return "muted";
    default:
      return "warning";
  }
}

export function sentimentTone(sentiment: string): "success" | "danger" | "warning" | "muted" {
  switch (sentiment) {
    case "positive":
      return "success";
    case "negative":
      return "danger";
    default:
      return "muted";
  }
}
