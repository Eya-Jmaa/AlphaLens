import React from "react";

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-bold text-foreground">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}

export const MarkdownLite: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;
  const lines = text.split("\n");
  const blocks: React.ReactNode[] = [];
  let listBuffer: string[] = [];
  let numberedBuffer: string[] = [];

  const flushList = (key: string) => {
    if (listBuffer.length > 0) {
      blocks.push(
        <ul key={`ul-${key}`} className="list-disc pl-5 space-y-1.5 my-2.5 text-foreground/90">
          {listBuffer.map((item, i) => (
            <li key={i} className="text-xs md:text-sm leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
    if (numberedBuffer.length > 0) {
      blocks.push(
        <ol key={`ol-${key}`} className="list-decimal pl-5 space-y-1.5 my-2.5 text-foreground/90 font-mono text-xs md:text-sm">
          {numberedBuffer.map((item, i) => (
            <li key={i} className="leading-relaxed font-sans">
              {renderInline(item)}
            </li>
          ))}
        </ol>
      );
      numberedBuffer = [];
    }
  };

  lines.forEach((line, i) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("### ")) {
      flushList(`head3-${i}`);
      blocks.push(
        <h4 key={i} className="text-xs font-mono font-bold uppercase tracking-wider text-foreground mt-4 mb-1.5">
          {renderInline(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith("## ")) {
      flushList(`head2-${i}`);
      blocks.push(
        <h3 key={i} className="text-sm md:text-base font-bold text-foreground mt-5 mb-2 first:mt-0 border-b border-border/60 pb-1">
          {renderInline(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith("# ")) {
      flushList(`head1-${i}`);
      blocks.push(
        <h2 key={i} className="text-base md:text-lg font-bold text-foreground mt-6 mb-2.5 first:mt-0">
          {renderInline(trimmed.slice(2))}
        </h2>
      );
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      listBuffer.push(trimmed.slice(2));
    } else if (/^\d+\.\s/.test(trimmed)) {
      numberedBuffer.push(trimmed.replace(/^\d+\.\s/, ""));
    } else if (trimmed.startsWith("> ")) {
      flushList(`quote-${i}`);
      blocks.push(
        <div key={i} className="p-3 my-2 rounded bg-elevated/80 border-l-2 border-primary text-xs md:text-sm italic text-muted-foreground">
          {renderInline(trimmed.slice(2))}
        </div>
      );
    } else if (trimmed === "") {
      flushList(`blank-${i}`);
    } else {
      flushList(`text-${i}`);
      blocks.push(
        <p key={i} className="text-xs md:text-sm leading-relaxed text-foreground/90 my-2">
          {renderInline(trimmed)}
        </p>
      );
    }
  });
  flushList("list-end");

  return <div className="space-y-1">{blocks}</div>;
};
