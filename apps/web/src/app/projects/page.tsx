"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AccountBar } from "@/components/account-bar";
import { CreateProjectForm } from "@/components/create-project-form";
import { ApiError, listProjects, type Project } from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  paused: "Paused",
  finished: "Finished",
  archived: "Archived",
};

export default function ProjectsPage() {
  const router = useRouter();
  const { data, error, isPending } = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) {
      router.replace("/login");
    }
  }, [error, router]);

  const grouped = (data ?? []).reduce<Record<string, Project[]>>((accumulator, project) => {
    const bucket = accumulator[project.status] ?? [];
    bucket.push(project);
    accumulator[project.status] = bucket;
    return accumulator;
  }, {});

  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col gap-8 px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <h1 className="text-xl font-semibold tracking-tight">Projects</h1>
        <AccountBar />
      </header>

      <CreateProjectForm />

      {isPending ? <p className="text-sm text-neutral-500">Loading…</p> : null}

      {Object.entries(grouped).map(([status, projects]) => (
        <section key={status} className="flex flex-col gap-2">
          <h2 className="text-xs font-medium uppercase tracking-wide text-neutral-500">
            {STATUS_LABEL[status] ?? status}
          </h2>
          <ul className="flex flex-col gap-2">
            {projects.map((project) => (
              <li
                key={project.id}
                className="rounded-xl border border-neutral-200 px-4 py-3 text-sm dark:border-neutral-800"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{project.name}</span>
                  <span className="text-xs text-neutral-500">since {project.start_date}</span>
                </div>
                {project.note ? (
                  <p className="mt-1 text-xs text-neutral-500">{project.note}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ))}

      <footer className="mt-auto text-xs text-neutral-500">
        <Link href="/" className="underline underline-offset-4">
          Back to today
        </Link>
      </footer>
    </main>
  );
}
