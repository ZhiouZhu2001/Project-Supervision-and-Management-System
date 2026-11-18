"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  ApiError,
  clearProjectSchedule,
  getProjectSchedule,
  updateProjectSchedule,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const WEEKDAYS = [
  { value: 1, label: "M" },
  { value: 2, label: "T" },
  { value: 3, label: "W" },
  { value: 4, label: "T" },
  { value: 5, label: "F" },
  { value: 6, label: "S" },
  { value: 7, label: "S" },
];

/**
 * Per-project rest overrides. The parent decides when this project's days
 * differ from the account default; the API keeps one rule per effective date,
 * so a change today never reaches back into an earlier streak.
 */
export function ProjectSchedule({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const { data, isPending } = useQuery({
    queryKey: ["schedule", projectId],
    queryFn: () => getProjectSchedule(projectId),
  });

  const [draft, setDraft] = useState<number[] | null>(null);
  const [saved, setSaved] = useState(false);
  const selected = draft ?? data?.rest_weekdays ?? [];

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["schedule", projectId] });
    await queryClient.invalidateQueries({ queryKey: ["today"] });
  }

  const save = useMutation({
    mutationFn: (days: number[]) => updateProjectSchedule(projectId, days),
    onSuccess: async () => {
      setDraft(null);
      setSaved(true);
      await refresh();
    },
  });

  const clear = useMutation({
    mutationFn: () => clearProjectSchedule(projectId),
    onSuccess: async () => {
      setDraft(null);
      setSaved(true);
      await refresh();
    },
  });

  const dirty =
    draft !== null && [...draft].sort().join() !== [...(data?.rest_weekdays ?? [])].sort().join();

  return (
    <Card aria-labelledby="schedule-heading">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="schedule-heading" className="text-[15px] font-[600] text-foreground">
            Rest days
          </h2>
          <p className="mt-1 text-[12px] text-muted-foreground">
            {isPending
              ? "Loading…"
              : data?.inherited
                ? "Following your account default."
                : `Overridden since ${data?.effective_from}.`}
          </p>
        </div>
        <Icon name="rest" size={18} />
      </div>

      <div className="mt-4 flex flex-wrap gap-[6px]">
        {WEEKDAYS.map((day, index) => {
          const active = selected.includes(day.value);
          return (
            <button
              key={`${day.label}-${index}`}
              type="button"
              aria-label={`weekday ${day.value}`}
              aria-pressed={active}
              onClick={() => {
                setSaved(false);
                setDraft(
                  active
                    ? selected.filter((value) => value !== day.value)
                    : [...selected, day.value].sort((a, b) => a - b),
                );
              }}
              className={cn(
                "h-9 w-9 rounded-[7px] border text-[12px] font-[600] transition-colors duration-[160ms]",
                active
                  ? "border-transparent bg-primary text-primary-foreground"
                  : "border-border bg-card text-muted-foreground hover:bg-secondary",
              )}
            >
              {day.label}
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button type="button" size="sm" disabled={!dirty || save.isPending} onClick={() => save.mutate(selected)}>
          {save.isPending ? "Saving…" : "Save override"}
        </Button>
        {data && !data.inherited ? (
          <Button
            type="button"
            variant="subtle"
            size="sm"
            disabled={clear.isPending}
            onClick={() => clear.mutate()}
          >
            Use account default
          </Button>
        ) : null}
        {saved ? (
          <span role="status" className="inline-flex items-center gap-[6px] text-[11px] text-sage-ink">
            <Icon name="check" size={14} />
            Saved
          </span>
        ) : null}
        {save.isError || clear.isError ? (
          <span role="alert" className="text-[11px] text-destructive">
            {save.error instanceof ApiError && save.error.code === "REST_DAYS_INVALID"
              ? "At least one day must stay expected."
              : "Could not save. Try again."}
          </span>
        ) : null}
      </div>
    </Card>
  );
}
