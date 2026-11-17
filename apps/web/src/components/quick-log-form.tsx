"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, createLog, type TodayProject } from "@/lib/api";

/**
 * The quick log. Exactly two required fields — project and body — because the
 * ten-second budget is a product constraint, not a preference (invariant 5).
 */
export function QuickLogForm({ projects }: { projects: TodayProject[] }) {
  const queryClient = useQueryClient();
  const firstUnrecorded = projects.find((project) => !project.recorded) ?? projects[0];
  const [projectId, setProjectId] = useState(firstUnrecorded?.id ?? "");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: createLog,
    onSuccess: async (log) => {
      setContent("");
      setSaved(log.id);
      setError(null);
      // The card, the count and the date all come from one query.
      await queryClient.invalidateQueries({ queryKey: ["today"] });
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (cause: unknown) => {
      setSaved(null);
      setError(
        cause instanceof ApiError
          ? cause.code === "VALIDATION_ERROR"
            ? "A project and a few words are required."
            : `Could not save that (${cause.code}).`
          : "Could not save that. Try again.",
      );
    },
  });

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaved(null);
    if (!projectId) {
      setError("Choose a project first.");
      return;
    }
    if (!content.trim()) {
      setError("Write a few words about what you did.");
      return;
    }
    mutation.mutate({ project_id: projectId, content: content.trim() });
  }

  if (projects.length === 0) {
    return null;
  }

  return (
    <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-4" aria-busy={mutation.isPending}>
      <div className="flex flex-col gap-2">
        <Label htmlFor="log-project">Project</Label>
        <Select
          id="log-project"
          value={projectId}
          onChange={(event) => setProjectId(event.target.value)}
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
              {project.recorded ? " — already recorded today" : ""}
            </option>
          ))}
        </Select>
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="log-content">What did you do?</Label>
        <Textarea
          id="log-content"
          rows={3}
          maxLength={2000}
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="A few words is enough."
        />
      </div>

      {error ? (
        <p role="alert" className="text-[12px] text-destructive">
          {error}
        </p>
      ) : null}

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : "Save it"}
        </Button>
        {saved ? (
          <span role="status" className="inline-flex items-center gap-[6px] text-[12px] text-sage-ink">
            <Icon name="check" size={16} />
            Recorded
          </span>
        ) : null}
      </div>
    </form>
  );
}
