"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icon";
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
    <form onSubmit={onSubmit} className="form" aria-busy={mutation.isPending}>
      <label className="field" htmlFor="project-name">
        <span>Project name</span>
        <input
          id="project-name"
          type="text"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="e.g. Read a little every day"
          maxLength={60}
          aria-describedby={error ? "create-error" : undefined}
        />
      </label>
      <label className="field">
        <span>
          Start date<span className="optional">optional</span>
        </span>
        <input
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
        />
        <span className="helper">
          Leave empty to use the current business day.
        </span>
      </label>
      {error ? (
        <p id="create-error" role="alert" className="form-error">
          {error}
        </p>
      ) : null}
      {created ? (
        <p role="status" className="success">
          <Icon name="check" size={16} />
          <Link href={`/projects/${created.id}`}>
            Project created. Open project →
          </Link>
        </p>
      ) : null}
      <button type="submit" disabled={mutation.isPending} className="button">
        <Icon name="plus" size={16} />
        {mutation.isPending ? "Creating…" : "Create project"}
      </button>
      <p className="helper">A small beginning is still a beginning.</p>
    </form>
  );
}
