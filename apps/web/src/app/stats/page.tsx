"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppShell, PageHeading } from "@/components/app-shell";
import { Icon } from "@/components/icon";
import { Card } from "@/components/ui/card";
import { ApiError, getStatistics, type ProjectRates } from "@/lib/api";

/** A dash, never 0%: nothing was expected, so nothing was failed. */
function percent(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function RateBar({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between text-[11px] text-muted-foreground">
        <span>{label}</span>
        <span className="tabular-nums">{percent(value)}</span>
      </div>
      <div className="h-[5px] w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full bg-sage-ink"
          style={{ width: value === null ? "0%" : `${Math.round(value * 100)}%` }}
        />
      </div>
    </div>
  );
}

function ProjectRow({ project }: { project: ProjectRates }) {
  return (
    <li className="flex flex-col gap-3 rounded-[10px] border border-border px-4 py-3">
      <div className="flex items-baseline justify-between gap-3">
        <strong className="truncate text-[13px] font-[600] text-foreground">{project.name}</strong>
        <span className="shrink-0 text-[11px] text-muted-foreground">
          {project.recorded_days}/{project.expected_days} days
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <RateBar label="Recorded" value={project.completion_rate} />
        <RateBar label="Written on the day" value={project.clean_completion_rate} />
      </div>
      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
        <span className="inline-flex items-center gap-[6px]">
          <Icon name="check" size={12} />
          {project.current_streak} day streak
        </span>
        <span>best {project.longest_streak}</span>
      </div>
    </li>
  );
}

export default function StatsPage() {
  const router = useRouter();
  const { data, error, isPending } = useQuery({
    queryKey: ["stats"],
    queryFn: getStatistics,
  });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);

  const rollup = data?.rollup ?? [];
  const peak = Math.max(1, ...rollup.map((week) => week.expected));

  return (
    <AppShell>
      <PageHeading
        eyebrow="THE SHAPE OF THE WORK"
        title="Statistics."
        description="What was expected, what was recorded, and how much of it was written on the day."
      />

      {isPending ? (
        <p className="text-[12px] text-muted-foreground">Loading…</p>
      ) : error ? (
        <p className="text-[12px] text-destructive">Could not load the statistics.</p>
      ) : (
        <div className="grid grid-cols-[minmax(0,1fr)_300px] items-start gap-7 max-[900px]:grid-cols-1">
          <Card aria-labelledby="projects-heading">
            <div className="mb-4 flex items-baseline justify-between gap-3">
              <h2 id="projects-heading" className="text-[15px] font-[600] text-foreground">
                Each project
              </h2>
              <span className="text-[11px] text-muted-foreground">{data.projects.length} tracked</span>
            </div>

            {data.projects.length === 0 ? (
              <p className="text-[12px] text-muted-foreground">
                Nothing to measure yet. Create a project and record a day.
              </p>
            ) : (
              <ul className="flex flex-col gap-3">
                {data.projects.map((project) => (
                  <ProjectRow key={project.id} project={project} />
                ))}
              </ul>
            )}
          </Card>

          <div className="flex flex-col gap-6">
            <Card aria-labelledby="recent-heading">
              <h2 id="recent-heading" className="text-[15px] font-[600] text-foreground">
                Last {data.recent_days} days
              </h2>
              <p className="mt-3 text-[34px] font-[650] leading-none text-foreground tabular-nums">
                {data.recent_logs}
              </p>
              <p className="mt-1 text-[12px] text-muted-foreground">
                {data.recent_logs === 1 ? "entry written" : "entries written"}
              </p>
            </Card>

            <Card aria-labelledby="rollup-heading">
              <h2 id="rollup-heading" className="text-[15px] font-[600] text-foreground">
                Twelve weeks
              </h2>
              <p className="mt-1 text-[11px] text-muted-foreground">
                Recorded against expected, week by week.
              </p>

              {rollup.length === 0 ? (
                <p className="mt-4 text-[12px] text-muted-foreground">
                  No week expected anything yet.
                </p>
              ) : (
                <ul className="mt-4 flex h-[120px] items-end gap-[6px]">
                  {rollup.map((week) => {
                    const recordedHeight = (week.recorded / peak) * 100;
                    const expectedHeight = (week.expected / peak) * 100;
                    return (
                      <li
                        key={week.week_start}
                        className="relative h-full flex-1"
                        title={`week of ${week.week_start}: ${week.recorded}/${week.expected}`}
                      >
                        <div
                          className="w-full rounded-[3px] bg-secondary"
                          style={{ height: `${expectedHeight}%`, minHeight: "4px" }}
                        />
                        <div
                          className="absolute bottom-0 w-full rounded-[3px] bg-sage-ink"
                          style={{ height: `${recordedHeight}%` }}
                        />
                      </li>
                    );
                  })}
                </ul>
              )}
              <p className="mt-3 flex items-start gap-2 text-[11px] text-muted-foreground">
                <Icon name="info" size={14} />
                <span>Weeks with nothing expected are left out rather than drawn as zero.</span>
              </p>
            </Card>
          </div>
        </div>
      )}
    </AppShell>
  );
}
