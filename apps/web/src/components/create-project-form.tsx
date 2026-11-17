"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, createProject, type Project } from "@/lib/api";

export function CreateProjectForm() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Project | null>(null);

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: async (project) => {
      setName("");
      setStartDate("");
      setError(null);
      setCreated(project);
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (cause: unknown) => {
      setError(
        cause instanceof ApiError && cause.code === "VALIDATION_ERROR"
          ? "A project needs a name of 1–60 characters and a valid start date."
          : "Could not create the project. Try again.",
      );
    },
  });

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setCreated(null);
    if (!name.trim()) {
      setError("A project needs a name.");
      return;
    }
    mutation.mutate({
      name: name.trim(),
      ...(startDate ? { start_date: startDate } : {}),
    });
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5" aria-busy={mutation.isPending}>
      <div className="flex flex-col gap-2">
        <Label htmlFor="project-name">Project name</Label>
        <Input
          id="project-name"
          type="text"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="e.g. Read a little every day"
          maxLength={60}
          aria-describedby={error ? "create-error" : undefined}
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="project-start">
          Start date
          <span className="ml-2 text-[11px] font-[400] text-muted-foreground">
            optional
          </span>
        </Label>
        <Input
          id="project-start"
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
        />
        <span className="text-[11px] text-muted-foreground">
          Leave empty to use the current business day.
        </span>
      </div>

      {error ? (
        <p id="create-error" role="alert" className="text-[12px] text-destructive">
          {error}
        </p>
      ) : null}

      {created ? (
        <p role="status" className="flex items-center gap-2 text-[12px] text-sage-ink">
          <Icon name="check" size={16} />
          <Link href={`/projects/${created.id}`} className="underline underline-offset-4">
            Project created. Open project →
          </Link>
        </p>
      ) : null}

      <Button type="submit" disabled={mutation.isPending} className="w-full">
        <Icon name="plus" size={16} />
        {mutation.isPending ? "Creating…" : "Create project"}
      </Button>

      <p className="text-[11px] text-muted-foreground">
        A small beginning is still a beginning.
      </p>
    </form>
  );
}
