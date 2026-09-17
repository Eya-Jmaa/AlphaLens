import { useEffect, useState } from "react";

/** Real-time, client-computed NYSE session status (9:30-16:00 America/New_York,
 * Mon-Fri). Uses Intl's IANA timezone conversion so it's correct regardless of
 * the viewer's local timezone and DST - no API call, no invented data. Does
 * NOT account for market holidays (no holiday calendar in this app), so it can
 * read "Open" on a holiday; labeled as a best-effort session estimate. */
export function useMarketHours() {
  const [isOpen, setIsOpen] = useState(() => computeIsOpen());

  useEffect(() => {
    const interval = setInterval(() => setIsOpen(computeIsOpen()), 60_000);
    return () => clearInterval(interval);
  }, []);

  return isOpen;
}

function computeIsOpen(): boolean {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    hour: "numeric",
    minute: "numeric",
    hour12: false,
  }).formatToParts(new Date());

  const weekday = parts.find((p) => p.type === "weekday")?.value ?? "";
  const hour = Number(parts.find((p) => p.type === "hour")?.value ?? 0);
  const minute = Number(parts.find((p) => p.type === "minute")?.value ?? 0);

  if (weekday === "Sat" || weekday === "Sun") return false;

  const minutesSinceMidnight = hour * 60 + minute;
  return minutesSinceMidnight >= 9 * 60 + 30 && minutesSinceMidnight < 16 * 60;
}
