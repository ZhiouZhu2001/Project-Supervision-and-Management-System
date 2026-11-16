"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AccountBar } from "@/components/account-bar";
import { ApiError, getProject, updateProject, type Project } from "@/lib/api";

const PALETTE = ["#71717a", "#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6"];

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data, error, isPending } = useQuery({
    queryKey: ["project", id],
    queryFn: () => getProject(id),
  });

  const [name, setName] = useState("");
  const [note, setNote] = useState("");
  const [color, setColor] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // The form is seeded once from the server value; re-seeding on every
  // refetch would overwrite what the owner is currently typing.
  useEffect(() => {
    if (data) {
      setName(data.name);
      setNote(data.note ?? "");
      setColor(data.color);
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: (patch: Parameters<typeof updateProject>[1]) => updateProject(id, patch),
    onSuccess: async (project: Project) => {
      setSaved(true);
      queryClient.setQueryData(["project", id], project);
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) {
      router.replace("/login");
    }
  }, [error, router]);

  useEffect(() => {
    if (!saved) return;
    const timer = setTimeout(() => setSaved(false), 2000);
    return () => clearTimeout(timer);
  }, [saved]);

  if (isPending) {
    return <Shell><p className="text-sm text-neutral-500">Loading…</p></Shell>;
  }

  if (error instanceof ApiError && error.status === 404) {
    return (
      <Shell>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">This project no longer exists.</p>
        <Link href="/projects" className="text-sm underline underline-offset-4">
          Back to projects
        </Link>
      </Shell>
    );
  }

  if (!data) {
    return <Shell><p className="text-sm text-red-600">Could not load the project.</p></Shell>;
  }

  return (
    <Shell>
      <section className="flex flex-col gap-3">
        <h2 className="text-xs font-medium uppercase tracking-wide text-neutral-500">Details</h2>

        <label className="flex flex-col gap-1 text-sm">
          <span className="text-neutral-600 dark:text-neutral-400">Name</span>
          <input
            value={name}
            maxLength={60}
            onChange={(event) => setName(event.target.value)}
            className="rounded-lg border border-neutral-300 bg-transparent px-3 py-2 outline-none focus:border-neutral-500 dark:border-neutral-700"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="text-neutral-600 dark:text-neutral-400">Note</span>
          <textarea
            value={note}
            rows={3}
            maxLength={2000}
            onChange={(event) => setNote(event.target.value)}
            className="rounded-lg border border-neutral-300 bg-transparent px-3 py-2 outline-none focus:border-neutral-500 dark:border-neutral-700"
          />
        </label>

        <div className="flex flex-col gap-1 text-sm">
          <span className="text-neutral-600 dark:text-neutral-400">Colour</span>
          <div className="flex gap-2">
            {PALETTE.map((swatch) => (
              <button
                key={swatch}
                type="button"
                aria-label={`colour ${swatch}`}
                onClick={() => setColor(swatch)}
                style={{ backgroundColor: swatch }}
                className={`h-7 w-7 rounded-full ring-offset-2 ${
                  color === swatch ? "ring-2 ring-neutral-900 dark:ring-neutral-100" : ""
                }`}
              />
            ))}
            <button
              type="button"
              onClick={() => setColor(null)}
              className="h-7 rounded-full border border-neutral-300 px-2 text-xs dark:border-neutral-700"
            >
              none
            </button>
          </div>
        </div>

        <p className="text-xs text-neutral-500">
          Started {data.start_date} · {data.status}. The start date and status are not editable here:
          changing when a project started changes every streak it has.
        </p>

        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() =>
              mutation.mutate({ name: name.trim(), note: note.trim() === "" ? null : note.trim(), color })
            }
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900"
          >
            {mutation.isPending ? "Saving…" : "Save"}
          </button>
          {saved ? <span className="text-xs text-emerald-600 dark:text-emerald-400">Saved</span> : null}
          {mutation.error instanceof ApiError ? (
            <span className="text-xs text-red-600 dark:text-red-400">
              {mutation.error.code === "VALIDATION_ERROR"
                ? "A name of 1–60 characters is required."
                : `Save failed (${mutation.error.code}).`}
            </span>
          ) : null}
        </div>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-xs font-medium uppercase tracking-wide text-neutral-500">Logs</h2>
        <p className="text-sm text-neutral-500">
          Nothing recorded yet. Recording arrives in the next slice.
        </p>
      </section>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col gap-8 px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <div className="flex flex-col">
          <Link href="/projects" className="text-xs text-neutral-500 underline underline-offset-4">
            Projects
          </Link>
          <h1 className="text-xl font-semibold tracking-tight">Project</h1>
        </div>
        <AccountBar />
      </header>
      {children}
    </main>
  );
}
