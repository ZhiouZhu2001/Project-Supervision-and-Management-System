"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ApiError, setProjectStatus, type Project, type ProjectStatus } from "@/lib/api";

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
 * Status is a deliberate act with a date attached (R14). Pausing is offered as
 * a single button rather than a dropdown because there are exactly two states
 * a running project can move to here.
 */
export function ProjectStatusCard({ project }: { project: Project }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState<ProjectStatus | null>(null);

  const change = useMutation({
    mutationFn: (status: ProjectStatus) => setProjectStatus(project.id, status),
    onSuccess: async () => {
      setConfirming(null);
      await queryClient.invalidateQueries({ queryKey: ["project", project.id] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
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

      {project.status === "active" ? (
        <Button
          type="button"
          variant="subtle"
          size="sm"
          className="mt-4"
          disabled={change.isPending}
          onClick={() => change.mutate("paused")}
        >
          {change.isPending ? "Pausing…" : "Pause this project"}
        </Button>
      ) : null}

      {project.status === "paused" ? (
        <Button
          type="button"
          size="sm"
          className="mt-4"
          disabled={change.isPending}
          onClick={() => change.mutate("active")}
        >
          {change.isPending ? "Resuming…" : "Resume"}
        </Button>
      ) : null}

      {project.status === "finished" || project.status === "archived" ? (
        <div className="mt-4 flex flex-col gap-2">
          {confirming === "active" ? (
            <p role="alert" className="text-[12px] text-foreground">
              Restore this project to active? It starts expecting records again from today.
            </p>
          ) : null}
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="subtle"
              size="sm"
              disabled={change.isPending}
              onClick={() => (confirming === "active" ? change.mutate("active") : setConfirming("active"))}
            >
              {confirming === "active" ? "Yes, reactivate" : "Reactivate"}
            </Button>
            {confirming === "active" ? (
              <Button type="button" variant="subtle" size="sm" onClick={() => setConfirming(null)}>
                Cancel
              </Button>
            ) : null}
          </div>
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
