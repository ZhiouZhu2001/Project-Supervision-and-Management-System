"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell, PageHeading } from "@/components/app-shell";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ApiError, getSettings, updateRestDays } from "@/lib/api";
import { cn } from "@/lib/utils";

const WEEKDAYS = [
  { value: 1, label: "Mon" },
  { value: 2, label: "Tue" },
  { value: 3, label: "Wed" },
  { value: 4, label: "Thu" },
  { value: 5, label: "Fri" },
  { value: 6, label: "Sat" },
  { value: 7, label: "Sun" },
];

export default function SettingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, error, isPending } = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  const [draft, setDraft] = useState<number[] | null>(null);
  const [saved, setSaved] = useState(false);
  const selected = draft ?? data?.rest_weekdays ?? [];

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);

  const mutation = useMutation({
    mutationFn: updateRestDays,
    onSuccess: async () => {
      setSaved(true);
      setDraft(null);
      // Rest days change what "expected" means, so today and the settings
      // themselves both have to be re-read.
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      await queryClient.invalidateQueries({ queryKey: ["today"] });
    },
  });

  function toggle(weekday: number) {
    setSaved(false);
    setDraft(
      selected.includes(weekday)
        ? selected.filter((value) => value !== weekday)
        : [...selected, weekday].sort((a, b) => a - b),
    );
  }

  const dirty = draft !== null && [...draft].sort().join() !== [...(data?.rest_weekdays ?? [])].sort().join();

  return (
    <AppShell>
      <PageHeading
        eyebrow="HOW THIS WORKS FOR YOU"
        title="Settings."
        description="Small rules that decide what counts as a good day."
      />

      <div className="grid max-w-[720px] grid-cols-1 gap-6">
        <Card aria-labelledby="rest-heading">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 id="rest-heading" className="text-[15px] font-[600] text-foreground">
                Rest days
              </h2>
              <p className="mt-1 text-[13px] text-muted-foreground">
                Days you are not expected to record. They neither add to a streak nor break one.
              </p>
            </div>
            <Icon name="rest" size={20} />
          </div>

          {isPending ? (
            <p className="mt-5 text-[12px] text-muted-foreground">Loading…</p>
          ) : (
            <>
              <div className="mt-5 flex flex-wrap gap-2">
                {WEEKDAYS.map((day) => {
                  const active = selected.includes(day.value);
                  return (
                    <button
                      key={day.value}
                      type="button"
                      aria-pressed={active}
                      onClick={() => toggle(day.value)}
                      className={cn(
                        "min-h-[40px] rounded-[7px] border px-4 text-[13px] font-[550] transition-colors duration-[160ms]",
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

              <p className="mt-4 text-[11px] text-muted-foreground">
                {data?.effective_from
                  ? `Current rule has applied since ${data.effective_from}.`
                  : "Using the default: Saturday and Sunday."}{" "}
                A change applies from today onward; past streaks keep the rules they were earned
                under.
              </p>

              <div className="mt-5 flex items-center gap-3">
                <Button
                  type="button"
                  disabled={!dirty || mutation.isPending}
                  onClick={() => mutation.mutate(selected)}
                >
                  {mutation.isPending ? "Saving…" : "Save rest days"}
                </Button>
                {saved ? (
                  <span role="status" className="inline-flex items-center gap-[6px] text-[12px] text-sage-ink">
                    <Icon name="check" size={16} />
                    Saved
                  </span>
                ) : null}
                {mutation.isError ? (
                  <span role="alert" className="text-[12px] text-destructive">
                    {mutation.error instanceof ApiError && mutation.error.code === "REST_DAYS_INVALID"
                      ? "At least one day must stay expected."
                      : "Could not save. Try again."}
                  </span>
                ) : null}
              </div>
            </>
          )}
        </Card>

        <Card>
          <h2 className="text-[15px] font-[600] text-foreground">Time</h2>
          <p className="mt-1 text-[13px] text-muted-foreground">
            A day runs from 04:00 to 04:00, Europe/Madrid. It is fixed on purpose: changing it
            would recompute every streak you have.
          </p>
        </Card>

        <Card>
          <h2 className="text-[15px] font-[600] text-foreground">Your data</h2>
          <p className="mt-1 text-[13px] text-muted-foreground">
            One file with every project, log, tag, rule and status change you have written. No
            passwords, no session tokens, no image bytes — only the record itself.
          </p>
          <a
            href="/api/export.json"
            download="daymark-export.json"
            className="mt-4 inline-flex min-h-[36px] items-center gap-2 rounded-[7px] border border-border bg-card px-4 text-[12px] font-[600] text-foreground hover:bg-secondary"
          >
            <Icon name="download" size={15} />
            Download the export
          </a>
        </Card>
      </div>
    </AppShell>
  );
}
