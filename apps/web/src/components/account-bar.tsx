"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, logout, me, type Account } from "@/lib/api";

export function AccountBar() {
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    me()
      .then((value) => {
        if (!cancelled) setAccount(value);
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        // A cookie can exist while the session behind it is gone — the API is
        // the authority, so a 401 sends the user to the login page.
        if (cause instanceof ApiError && cause.status === 401) {
          router.replace("/login");
          return;
        }
        setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function onSignOut() {
    await logout().catch(() => undefined);
    router.replace("/login");
    router.refresh();
  }

  if (failed) {
    return <span className="text-sm text-red-600 dark:text-red-400">Account unavailable</span>;
  }

  if (account === null) {
    return <span className="text-sm text-neutral-500">…</span>;
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-neutral-600 dark:text-neutral-400">{account.email}</span>
      <button
        type="button"
        onClick={onSignOut}
        className="rounded-lg border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-900"
      >
        Sign out
      </button>
    </div>
  );
}
