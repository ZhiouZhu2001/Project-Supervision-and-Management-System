"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppShell, LoadingProjects, PageHeading } from "@/components/app-shell";
import { CreateProjectForm } from "@/components/create-project-form";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  ApiError,
  listProjects,
  restoreProject,
  updateProject,
  type Project,
  type ProjectStatus,
} from "@/lib/api";

const STATUS_LABEL: Record<ProjectStatus, string> = {
  active: "Active",
  paused: "Paused",
  // The status is "finished"; the list it lands in is the completed one.
  finished: "Completed",
  archived: "Archived",
};

const STATUS_ORDER: ProjectStatus[] = ["active", "paused", "finished", "archived"];

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects(),
  });

  const deleted = useQuery({
    queryKey: ["projects", "deleted"],
    queryFn: () => listProjects(true),
  });

  const restore = useMutation({
    mutationFn: (id: string) => restoreProject(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      await queryClient.invalidateQueries({ queryKey: ["today"] });
    },
  });

  const recentlyDeleted = (deleted.data ?? []).filter((project) => project.deleted_at !== null);

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);

  const reorder = useMutation({
    mutationFn: async ({ project, neighbour }: { project: Project; neighbour: Project }) => {
      await updateProject(project.id, { sort_order: neighbour.sort_order });
      await updateProject(neighbour.id, { sort_order: project.sort_order });
    },
    // Refresh on partial failure as well so the displayed order stays honest.
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const ordered = data ?? [];

  function move(project: Project, direction: -1 | 1) {
    const index = ordered.findIndex((candidate) => candidate.id === project.id);
    const neighbour = ordered[index + direction];
    if (neighbour) reorder.mutate({ project, neighbour });
  }

  return (
    <AppShell>
      <PageHeading
        eyebrow="THE THINGS YOU COME BACK TO"
        title="Your projects."
        description="Give the things that matter a place in your day."
        action={
          <Button asChild>
            <a href="#new-project">
              <Icon name="plus" size={17} />
              New project
            </a>
          </Button>
        }
      />

      <div className="grid grid-cols-[minmax(0,1fr)_320px] items-start gap-7 max-[1150px]:grid-cols-[minmax(0,1fr)_285px] max-[1150px]:gap-5 max-[900px]:grid-cols-1">
        <section aria-label="Project list">
          {isPending ? (
            <LoadingProjects />
          ) : error ? (
            <p role="alert" className="text-[12px] text-destructive">
              Could not load projects.{" "}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => void refetch()}
              >
                Try again
              </button>
            </p>
          ) : ordered.length === 0 ? (
            <Card className="flex flex-col items-start gap-3">
              <span className="grid h-[44px] w-[42px] place-items-center rounded-[10px] bg-sage text-sage-ink">
                <Icon name="projects" size={25} />
              </span>
              <h3 className="text-[15px] font-[600]">What will you keep doing?</h3>
              <p className="text-[13px] text-muted-foreground">
                Writing, moving, learning. Start with one project that matters to you.
              </p>
              <a
                href="#project-name"
                className="inline-flex min-h-[44px] items-center gap-2 text-[13px] font-[600] text-accent-foreground"
              >
                Create your first project
                <Icon name="arrow" size={16} />
              </a>
            </Card>
          ) : (
            STATUS_ORDER.map((status) => {
              const projects = ordered.filter((project) => project.status === status);
              if (!projects.length) return null;
              return (
                <section key={status} className="mb-8">
                  <div className="mb-3 flex items-baseline justify-between gap-3">
                    <h2 className="text-[15px] font-[600] text-foreground">
                      {STATUS_LABEL[status]}
                      <span className="ml-2 rounded-full bg-secondary px-2 py-[2px] text-[11px] font-[600] text-muted-foreground">
                        {projects.length}
                      </span>
                    </h2>
                    <span className="text-[11px] text-muted-foreground">
                      {status === "active" ? "Keep showing up." : "A part of your record."}
                    </span>
                  </div>

                  <ul className="flex flex-col gap-2">
                    {projects.map((project) => {
                      const index = ordered.findIndex(
                        (candidate) => candidate.id === project.id,
                      );
                      return (
                        <li
                          key={project.id}
                          className="flex items-center gap-[15px] rounded-[10px] border border-border bg-card px-5 py-[22px] max-[1150px]:gap-3 max-[1150px]:px-[15px] max-[1150px]:py-[18px] max-[700px]:px-[14px] max-[700px]:py-[17px]"
                        >
                          <span className="grid h-[44px] w-[42px] shrink-0 place-items-center rounded-[10px] bg-sage text-sage-ink">
                            <Icon
                              name="book"
                              style={project.color ? { color: project.color } : undefined}
                            />
                          </span>

                          <Link
                            href={`/projects/${project.id}`}
                            className="flex min-w-0 flex-1 flex-col"
                          >
                            <strong className="truncate text-[14px] font-[600] text-foreground">
                              {project.name}
                            </strong>
                            <p className="truncate text-[12px] text-muted-foreground">
                              {project.note || `Started ${project.start_date}`}
                            </p>
                          </Link>

                          <div className="flex shrink-0 gap-1">
                            <Button
                              type="button"
                              variant="subtle"
                              size="icon"
                              aria-label={`Move ${project.name} up`}
                              disabled={index <= 0 || reorder.isPending}
                              onClick={() => move(project, -1)}
                            >
                              <Icon name="up" size={16} />
                            </Button>
                            <Button
                              type="button"
                              variant="subtle"
                              size="icon"
                              aria-label={`Move ${project.name} down`}
                              disabled={index >= ordered.length - 1 || reorder.isPending}
                              onClick={() => move(project, 1)}
                            >
                              <Icon name="down" size={16} />
                            </Button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </section>
              );
            })
          )}

          {reorder.isError ? (
            <p role="alert" className="mb-4 text-[12px] text-destructive">
              Could not finish reordering. The list has been refreshed; try again.
            </p>
          ) : null}

          {recentlyDeleted.length > 0 ? (
            <section className="mb-8">
              <div className="mb-3 flex items-baseline justify-between gap-3">
                <h2 className="text-[15px] font-[600] text-foreground">
                  Recently deleted
                  <span className="ml-2 rounded-full bg-secondary px-2 py-[2px] text-[11px] font-[600] text-muted-foreground">
                    {recentlyDeleted.length}
                  </span>
                </h2>
                <span className="text-[11px] text-muted-foreground">Restorable for thirty days</span>
              </div>
              <ul className="flex flex-col gap-2">
                {recentlyDeleted.map((project) => (
                  <li
                    key={project.id}
                    className="flex items-center gap-3 rounded-[10px] border border-dashed border-border px-5 py-4"
                  >
                    <div className="flex min-w-0 flex-1 flex-col">
                      <strong className="truncate text-[14px] font-[600] text-muted-foreground">
                        {project.name}
                      </strong>
                      <span className="text-[11px] text-muted-foreground">
                        deleted {(project.deleted_at ?? "").slice(0, 10)}
                      </span>
                    </div>
                    <Button
                      type="button"
                      variant="subtle"
                      size="sm"
                      disabled={restore.isPending}
                      onClick={() => restore.mutate(project.id)}
                    >
                      Restore
                    </Button>
                  </li>
                ))}
              </ul>
              {restore.isError ? (
                <p role="alert" className="mt-2 text-[11px] text-destructive">
                  {restore.error instanceof ApiError && restore.error.code === "PROJECT_EXPIRED"
                    ? "That project was deleted too long ago to restore."
                    : "Could not restore that project."}
                </p>
              ) : null}
            </section>
          ) : null}

          <p className="flex items-start gap-2 rounded-[10px] bg-note px-4 py-3 text-[12px] text-muted-foreground">
            <Icon name="info" size={16} />
            <span>
              A project is something you keep doing. Start small; you can edit its details
              whenever you need.
            </span>
          </p>
        </section>

        <Card id="new-project" className="scroll-mt-5">
          <h2 className="text-[15px] font-[600] text-foreground">Make a little commitment.</h2>
          <p className="mb-5 mt-2 text-[12px] text-muted-foreground">
            Choose something you want to keep doing.
          </p>
          <CreateProjectForm />
        </Card>
      </div>
    </AppShell>
  );
}
