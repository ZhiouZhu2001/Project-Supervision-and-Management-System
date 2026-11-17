"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell, LoadingProjects, PageHeading } from "@/components/app-shell";
import { CreateProjectForm } from "@/components/create-project-form";
import { Icon } from "@/components/icon";
import {
  ApiError,
  listProjects,
  updateProject,
  type Project,
  type ProjectStatus,
} from "@/lib/api";

const STATUS_LABEL: Record<ProjectStatus, string> = {
  active: "Active",
  paused: "Paused",
  finished: "Finished",
  archived: "Archived",
};
const STATUS_ORDER: ProjectStatus[] = [
  "active",
  "paused",
  "finished",
  "archived",
];

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401)
      router.replace("/login");
  }, [error, router]);
  const reorder = useMutation({
    mutationFn: async ({
      project,
      neighbour,
    }: {
      project: Project;
      neighbour: Project;
    }) => {
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
          <a href="#new-project" className="button">
            <Icon name="plus" size={17} />
            New project
          </a>
        }
      />
      <div className="project-layout">
        <section aria-label="Project list">
          {isPending ? (
            <LoadingProjects />
          ) : error ? (
            <div className="form-error" role="alert">
              Could not load projects.{" "}
              <button className="text-link" onClick={() => void refetch()}>
                Try again
              </button>
            </div>
          ) : ordered.length === 0 ? (
            <div className="empty-state">
              <span className="project-symbol">
                <Icon name="projects" size={25} />
              </span>
              <h3>What will you keep doing?</h3>
              <p>
                Writing, moving, learning. Start with one project that matters
                to you.
              </p>
              <a className="text-link" href="#project-name">
                Create your first project
                <Icon name="arrow" size={16} />
              </a>
            </div>
          ) : (
            STATUS_ORDER.map((status) => {
              const projects = ordered.filter(
                (project) => project.status === status,
              );
              if (!projects.length) return null;
              return (
                <section key={status} className="project-group">
                  <div className="section-heading">
                    <h2>
                      {STATUS_LABEL[status]}
                      <span className="count">{projects.length}</span>
                    </h2>
                    <span className="section-note">
                      {status === "active"
                        ? "Keep showing up."
                        : "A part of your record."}
                    </span>
                  </div>
                  <ul className="project-list">
                    {projects.map((project) => {
                      const index = ordered.findIndex(
                        (candidate) => candidate.id === project.id,
                      );
                      return (
                        <li key={project.id} className="project-row">
                          <span className="project-symbol">
                            <Icon
                              name="book"
                              style={
                                project.color
                                  ? { color: project.color }
                                  : undefined
                              }
                            />
                          </span>
                          <Link
                            className="project-info"
                            href={`/projects/${project.id}`}
                          >
                            <strong>{project.name}</strong>
                            <p>
                              {project.note || `Started ${project.start_date}`}
                            </p>
                          </Link>
                          <div className="reorder">
                            <button
                              className="icon-button"
                              type="button"
                              aria-label={`Move ${project.name} up`}
                              disabled={index <= 0 || reorder.isPending}
                              onClick={() => move(project, -1)}
                            >
                              <Icon name="up" size={16} />
                            </button>
                            <button
                              className="icon-button"
                              type="button"
                              aria-label={`Move ${project.name} down`}
                              disabled={
                                index >= ordered.length - 1 || reorder.isPending
                              }
                              onClick={() => move(project, 1)}
                            >
                              <Icon name="down" size={16} />
                            </button>
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
            <p role="alert" className="form-error">
              Could not finish reordering. The list has been refreshed; try
              again.
            </p>
          ) : null}
          <div className="availability">
            <Icon name="info" size={16} />
            <span>
              A project is something you keep doing. Start small; you can edit
              its details whenever you need.
            </span>
          </div>
        </section>
        <aside id="new-project" className="panel create-panel">
          <h2 className="panel-heading">Make a little commitment.</h2>
          <p className="helper">Choose something you want to keep doing.</p>
          <CreateProjectForm />
        </aside>
      </div>
    </AppShell>
  );
}
