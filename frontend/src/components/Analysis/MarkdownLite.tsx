import React from "react";

/**
 * Minimal, safe renderer for the small markdown subset the backend's report
 * text actually uses (# / ## headings, "- " bullets, blank-line paragraphs,
 * **bold** spans). Builds React elements directly - no HTML injection risk,
 * unlike a dangerouslySetInnerHTML + markdown-to-HTML approach.
 */
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}

export const MarkdownLite: React.FC<{ text: string }> = ({ text }) => {
  const lines = text.split("\n");
  const blocks: React.ReactNode[] = [];
  let listBuffer: string[] = [];

  const flushList = (key: string) => {
    if (listBuffer.length > 0) {
      blocks.push(
        <ul key={key} className="list-disc pl-5 space-y-1 my-2">
          {listBuffer.map((item, i) => (
            <li key={i} className="text-sm leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
  };

  lines.forEach((line, i) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("## ")) {
      flushList(`list-${i}`);
      blocks.push(
        <h3 key={i} className="text-base font-semibold mt-5 mb-1.5 first:mt-0">
          {renderInline(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith("# ")) {
      flushList(`list-${i}`);
      blocks.push(
        <h2 key={i} className="text-lg font-bold mt-5 mb-2 first:mt-0">
          {renderInline(trimmed.slice(2))}
        </h2>
      );
    } else if (trimmed.startsWith("- ")) {
      listBuffer.push(trimmed.slice(2));
    } else if (trimmed === "") {
      flushList(`list-${i}`);
    } else {
      flushList(`list-${i}`);
      blocks.push(
        <p key={i} className="text-sm leading-relaxed text-foreground/90 my-1.5">
          {renderInline(trimmed)}
        </p>
      );
    }
  });
  flushList("list-end");

  return <div>{blocks}</div>;
};
