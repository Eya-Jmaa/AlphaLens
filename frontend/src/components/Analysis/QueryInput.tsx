import React, { useEffect, useState } from "react";
import { Swords } from "lucide-react";

type Props = {
  onSubmit: (q: string, debate: boolean) => void;
  isLoading?: boolean;
  examples?: string[];
  initialValue?: string;
};

export const QueryInput: React.FC<Props> = ({ onSubmit, isLoading = false, examples = [], initialValue }) => {
  const [text, setText] = useState(initialValue ?? "");
  const [debate, setDebate] = useState(false);

  useEffect(() => {
    if (initialValue) setText(initialValue);
  }, [initialValue]);

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const q = text.trim();
    if (!q) return;
    onSubmit(q, debate);
  };

  return (
    <form onSubmit={submit} className="bg-card p-6 rounded-xl shadow-sm border border-border">
      <label className="block text-sm font-medium text-muted-foreground mb-2">Ask a financial question or enter a ticker / portfolio</label>
      <div className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isLoading}
          placeholder="E.g. Analyze AAPL and MSFT, show sentiment and risks"
          className="flex-1 rounded-md border border-border bg-background px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground font-semibold hover:opacity-95 disabled:opacity-60"
        >
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      <div className="mt-3 flex items-center justify-between flex-wrap gap-2">
        {examples.length > 0 && (
          <div className="text-sm text-muted-foreground">
            Examples: {examples.map((ex, i) => (
              <button
                key={i}
                type="button"
                onClick={() => { setText(ex); }}
                className="mr-2 underline hover:text-foreground"
              >
                {ex}
              </button>
            ))}
          </div>
        )}

        <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none ml-auto">
          <input
            type="checkbox"
            checked={debate}
            onChange={(e) => setDebate(e.target.checked)}
            disabled={isLoading}
            className="rounded border-border accent-primary"
          />
          <Swords size={13} />
          Bull vs. Bear debate
        </label>
      </div>
    </form>
  );
};
