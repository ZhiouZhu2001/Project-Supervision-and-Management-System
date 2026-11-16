"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AccountBar } from "@/components/account-bar";
import { CreateProjectForm } from "@/components/create-project-form";
import { ApiError, listProjects, updateProject, type Project } from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  paused: "Paused",
  finished: "Finished",
  archived: "Archived",
};

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, error, isPending } = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) {
      router.replace("/login");
    }
  }, [error, router]);

  const reorder = useMutation({
    mutationFn: async ({ project, neighbour }: { project: Project; neighbour: Project }) => {
      // Two writes rather than one swap endpoint: the API stays a plain
      // resource, and the pair is small enough that a partial failure leaves
      // both projects with the same order — visible, and fixable by moving
      // either of them again.
      await updateProject(project.id, { sort_order: neighbour.sort_order });
      await updateProject(neighbour.id, { sort_order: project.sort_order });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const ordered = data ?? [];
  const grouped = ordered.reduce<Record<string, Project[]>>((accumulator, project) => {
    const bucket = accumulator[project.status] ?? [];
    bucket.push(project);
    accumulator[project.status] = bucket;
    return accumulator;
  }, {});

  function move(project: Project, direction: -1 | 1) {
    const index = ordered.findIndex((candidate) => candidate.id === project.id);
    const neighbour = ordered[index + direction];
    if (!neighbour) return;
    reorder.mutate({ project, neighbour });
  }

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
            {projects.map((project) => {
              const index = ordered.findIndex((candidate) => candidate.id === project.id);
              return (
                <li
                  key={project.id}
                  className="flex items-center gap-3 rounded-xl border border-neutral-200 px-4 py-3 text-sm dark:border-neutral-800"
                >
                  {project.color ? (
                    <span
                      aria-hidden
                      className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: project.color }}
                    />
                  ) : null}

                  <Link href={`/projects/${project.id}`} className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate font-medium">{project.name}</span>
                    <span className="text-xs text-neutral-500">since {project.start_date}</span>
                  </Link>

                  <div className="flex shrink-0 gap-1">
                    <button
                      type="button"
                      aria-label="move up"
                      disabled={index <= 0 || reorder.isPending}
                      onClick={() => move(project, -1)}
                      className="rounded border border-neutral-300 px-2 py-0.5 text-xs disabled:opacity-30 dark:border-neutral-700"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      aria-label="move down"
                      disabled={index < 0 || index >= ordered.length - 1 || reorder.isPending}
                      onClick={() => move(project, 1)}
                      className="rounded border border-neutral-300 px-2 py-0.5 text-xs disabled:opacity-30 dark:border-neutral-700"
                    >
                      ↓
                    </button>
                  </div>
                </li>
              );
            })}
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
