import { useEffect, useState } from "react";
import { getHealth } from "../api/client";
import { HealthCheck } from "../types";

const POLL_MS = 60_000;

/** Polls the backend's real /health endpoint (not mocked) for the sidebar's
 * System Status panel. Fails silently to `null` - the panel just shows
 * "unavailable" rather than throwing, since the app itself must still work
 * with the backend unreachable. */
export function useSystemHealth() {
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const result = await getHealth();
        if (!cancelled) {
          setHealth(result);
          setError(false);
        }
      } catch {
        if (!cancelled) setError(true);
      }
    }

    poll();
    const interval = setInterval(poll, 3_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return { health, error };
}
