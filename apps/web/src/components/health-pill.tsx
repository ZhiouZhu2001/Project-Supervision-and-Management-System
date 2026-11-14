"use client";

import { useEffect, useState } from "react";

type Health = {
  status: string;
  db: boolean;
  version: string;
  env: string;
  time: string;
};

type State =
  | { kind: "loading" }
  | { kind: "ok"; health: Health }
  | { kind: "error"; message: string };

/**
 * Deliberately fetches a relative path, not the configured base: this widget
 * exists to prove the browser talks to its own origin, which is what makes
 * the session cookie work without any CORS configuration.
 */
export function HealthPill() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    fetch("/api/healthz", { cache: "no-store" })
      .then(async (response) => {
        const body = (await response.json()) as Health;
        if (!cancelled) setState({ kind: "ok", health: body });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({ kind: "error", message: error instanceof Error ? error.message : "failed" });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.kind === "loading") {
    return <span className="text-sm text-neutral-500">checking API…</span>;
  }

  if (state.kind === "error") {
    return (
      <span className="text-sm text-red-600 dark:text-red-400">API unreachable — {state.message}</span>
    );
  }

  const ok = state.health.db;
  return (
    <span className={ok ? "text-sm text-emerald-600 dark:text-emerald-400" : "text-sm text-red-600"}>
      {ok ? "API and database reachable" : "API up, database unreachable"} · v{state.health.version}
    </span>
  );
}
