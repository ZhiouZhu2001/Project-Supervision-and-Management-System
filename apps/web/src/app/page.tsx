import { HealthPill } from "@/components/health-pill";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col justify-center gap-6 px-6 py-16">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">Project Supervision</h1>
        <p className="text-neutral-600 dark:text-neutral-400">
          Record what you actually did. Be told when you did not.
        </p>
      </header>

      <section className="rounded-xl border border-neutral-200 p-4 dark:border-neutral-800">
        <h2 className="mb-2 text-sm font-medium text-neutral-500">Environment</h2>
        <HealthPill />
      </section>

      <footer className="text-xs text-neutral-500">
        Phase 1 · ticket 01. Projects, logging and streaks arrive in later slices.
      </footer>
    </main>
  );
}
