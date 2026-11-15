"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AccountBar } from "@/components/account-bar";
import { HealthPill } from "@/components/health-pill";
import { ApiError, listProjects, type Project } from "@/lib/api";

/**
 * Today's view. Every active project is listed as "not recorded" because
 * recording does not exist yet (ticket 07). When logs arrive this reads their
 * state from the API instead of assuming.
 */
export default function TodayPage() {
  const router = useRouter();
  const { data, error, isPending } = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) {
      router.replace("/login");
    }
  }, [error, router]);

  const active = (data ?? []).filter((project: Project) => project.status === "active");

  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col gap-8 px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold tracking-tight">Today</h1>
        <AccountBar />
      </header>

      {isPending ? <p className="text-sm text-neutral-500">Loading…</p> : null}

      {!isPending && active.length === 0 ? (
        <section className="rounded-xl border border-dashed border-neutral-300 p-6 text-center dark:border-neutral-700">
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            No active projects yet.
          </p>
          <Link
            href="/projects"
            className="mt-3 inline-block rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white dark:bg-neutral-100 dark:text-neutral-900"
          >
            Create the first one
          </Link>
        </section>
      ) : null}

      <ul className="flex flex-col gap-3">
        {active.map((project) => (
          <li
            key={project.id}
            className="flex items-center justify-between gap-4 rounded-xl border border-neutral-200 px-4 py-3 dark:border-neutral-800"
          >
            <span className="text-sm font-medium">{project.name}</span>
            <span className="rounded-full bg-neutral-100 px-2.5 py-1 text-xs text-neutral-600 dark:bg-neutral-900 dark:text-neutral-400">
              Not recorded
            </span>
          </li>
        ))}
      </ul>

      <footer className="mt-auto flex items-center justify-between gap-4 text-xs text-neutral-500">
        <Link href="/projects" className="underline underline-offset-4">
          Manage projects
        </Link>
        <HealthPill />
      </footer>
    </main>
  );
}
