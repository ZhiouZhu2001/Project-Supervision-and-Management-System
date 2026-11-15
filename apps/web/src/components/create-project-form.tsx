"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError, createProject } from "@/lib/api";

export function CreateProjectForm() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: async () => {
      setName("");
      setStartDate("");
      setError(null);
      // The list and the today view both read ["projects"]; one invalidation
      // refreshes both without a manual reload.
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (cause: unknown) => {
      setError(
        cause instanceof ApiError && cause.code === "VALIDATION_ERROR"
          ? "A project needs a name of 1–60 characters."
          : "Could not create the project. Try again.",
      );
    },
  });

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed.length === 0) {
      setError("A project needs a name.");
      return;
    }
    mutation.mutate({
      name: trimmed,
      ...(startDate ? { start_date: startDate } : {}),
    });
  }

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-col gap-3 rounded-xl border border-neutral-200 p-4 dark:border-neutral-800"
    >
      <h2 className="text-sm font-medium text-neutral-500">New project</h2>

      <input
        type="text"
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="What are you going to keep doing?"
        maxLength={60}
        className="rounded-lg border border-neutral-300 bg-transparent px-3 py-2 text-sm outline-none focus:border-neutral-500 dark:border-neutral-700"
      />

      <label className="flex items-center gap-2 text-xs text-neutral-500">
        <span className="w-20 shrink-0">Start date</span>
        <input
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
          className="rounded-lg border border-neutral-300 bg-transparent px-2 py-1 outline-none focus:border-neutral-500 dark:border-neutral-700"
        />
        <span className="text-neutral-400">leave empty for today</span>
      </label>

      {error ? (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="self-start rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900"
      >
        {mutation.isPending ? "Adding…" : "Add project"}
      </button>
    </form>
  );
}
