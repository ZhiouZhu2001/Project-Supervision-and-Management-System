"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  ApiError,
  getProjectStats,
  setProjectStatus,
  type Project,
  type ProjectStatus,
} from "@/lib/api";

const LABEL: Record<ProjectStatus, string> = {
  active: "Active",
  paused: "Paused",
  finished: "Finished",
  archived: "Archived",
};

const EXPLANATION: Record<ProjectStatus, string> = {
  active: "This project expects a record on its expected days.",
  paused: "Nothing is expected while paused, and the streak waits where it stopped.",
  finished: "Closed. The numbers are kept, and nothing is expected again.",
  archived: "Out of the way, kept on the record.",
};

/**
 * Status is a deliberate act with a date attached (R14). Finishing asks twice
 * and cannot be undone from here: a finished project is a statement that the
 * work is done, so the interface must not make that word cheap.
 */
export function ProjectStatusCard({ project }: { project: Project }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState<ProjectStatus | null>(null);
  const closed = project.status === "finished" || project.status === "archived";

  const stats = useQuery({
    queryKey: ["project-stats", project.id],
    queryFn: () => getProjectStats(project.id),
    enabled: closed,
  });

  const change = useMutation({
    mutationFn: (status: ProjectStatus) => setProjectStatus(project.id, status),
    onSuccess: async () => {
      setConfirming(null);
      await queryClient.invalidateQueries({ queryKey: ["project", project.id] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      await queryClient.invalidateQueries({ queryKey: ["project-stats", project.id] });
      await queryClient.invalidateQueries({ queryKey: ["today"] });
      await queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
  });

  return (
    <Card aria-labelledby="status-heading">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="status-heading" className="text-[15px] font-[600] text-foreground">
            Status
          </h2>
          <p className="mt-1 text-[12px] text-muted-foreground">{EXPLANATION[project.status]}</p>
        </div>
        <span className="inline-flex items-center gap-[6px] whitespace-nowrap rounded-[5px] bg-secondary px-[9px] py-[5px] text-[10px] font-[550] text-muted-foreground">
          <Icon name="info" size={12} />
          {LABEL[project.status]}
        </span>
      </div>

      {closed ? (
        <div className="mt-4 rounded-[10px] bg-secondary px-4 py-3">
          <p className="text-[11px] font-[600] uppercase tracking-[1.2px] text-muted-foreground">
            Final numbers
          </p>
          {stats.data ? (
            <p className="mt-1 text-[13px] text-foreground">
              {stats.data.current_streak} day streak · best {stats.data.longest_streak} days
            </p>
          ) : (
            <p className="mt-1 text-[12px] text-muted-foreground">Loading…</p>
          )}
        </div>
      ) : null}

      {confirming === "paused" ? (
        <div className="mt-4 flex flex-col gap-3">
          <p className="text-[12px] text-foreground">
            Pause “{project.name}”? Nothing will be expected until you resume, and the streak holds
            where it is.
          </p>
          <div className="flex items-center gap-2">
            <Button type="button" size="sm" disabled={change.isPending} onClick={() => change.mutate("paused")}>
              {change.isPending ? "Pausing…" : "Pause it"}
            </Button>
            <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming(null)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : null}

      {confirming === "finished" ? (
        <div className="mt-4 flex flex-col gap-3">
          <p className="text-[12px] text-foreground">
            Finish “{project.name}”? It leaves today for good, keeps its final numbers, and cannot
            be reopened from this screen.
          </p>
          <div className="flex items-center gap-2">
            <Button type="button" size="sm" disabled={change.isPending} onClick={() => change.mutate("finished")}>
              {change.isPending ? "Finishing…" : "Finish it"}
            </Button>
            <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming(null)}>
              Keep going
            </Button>
          </div>
        </div>
      ) : null}

      {confirming === "active" ? (
        <div className="mt-4 flex flex-col gap-3">
          <p className="text-[12px] text-foreground">
            Bring “{project.name}” back? It starts expecting records again from today.
          </p>
          <div className="flex items-center gap-2">
            <Button type="button" size="sm" disabled={change.isPending} onClick={() => change.mutate("active")}>
              {change.isPending ? "Restoring…" : "Yes, unarchive"}
            </Button>
            <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming(null)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : null}

      {confirming === null ? (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {project.status === "active" ? (
            <>
              <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming("paused")}>
                Pause this project
              </Button>
              <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming("finished")}>
                Finish this project
              </Button>
              <Button
                type="button"
                variant="subtle"
                size="sm"
                disabled={change.isPending}
                onClick={() => change.mutate("archived")}
              >
                Archive
              </Button>
            </>
          ) : null}

          {project.status === "paused" ? (
            <>
              <Button type="button" size="sm" disabled={change.isPending} onClick={() => change.mutate("active")}>
                {change.isPending ? "Resuming…" : "Resume"}
              </Button>
              <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming("finished")}>
                Finish this project
              </Button>
              <Button
                type="button"
                variant="subtle"
                size="sm"
                disabled={change.isPending}
                onClick={() => change.mutate("archived")}
              >
                Archive
              </Button>
            </>
          ) : null}

          {project.status === "archived" ? (
            <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming("active")}>
              Unarchive
            </Button>
          ) : null}
        </div>
      ) : null}

      {change.isError ? (
        <p role="alert" className="mt-3 text-[11px] text-destructive">
          {change.error instanceof ApiError && change.error.code === "STATUS_TRANSITION_INVALID"
            ? "That change is not allowed from the current status."
            : "Could not change the status."}
        </p>
      ) : null}
    </Card>
  );
}
