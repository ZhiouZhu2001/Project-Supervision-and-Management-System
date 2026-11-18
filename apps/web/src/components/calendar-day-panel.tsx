"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Icon } from "@/components/icon";
import { Card } from "@/components/ui/card";
import { listLogs, listProjects, type CalendarDay } from "@/lib/api";

/**
 * One day, in full. The calendar answers "how did the month go"; this answers
 * "what exactly happened on that Tuesday". Logs are grouped by project because
 * that is how the owner thinks about them, not sorted by creation time.
 */
export function CalendarDayPanel({
  day,
  isToday,
  projects,
}: {
  day: CalendarDay | null;
  isToday: boolean;
  projects: { id: string; name: string }[];
}) {
  const { data, isPending, error } = useQuery({
    queryKey: ["logs", "day", day?.business_date],
    queryFn: () => listLogs({ from: day?.business_date, to: day?.business_date }),
    enabled: day !== null,
  });

  if (day === null) {
    return (
      <Card>
        <h2 className="text-[15px] font-[600] text-foreground">A day in detail</h2>
        <p className="mt-2 text-[12px] text-muted-foreground">
          Pick a day above to see what was recorded on it.
        </p>
      </Card>
    );
  }

  const logs = data ?? [];
  const nameById = new Map(projects.map((project) => [project.id, project.name]));
  const grouped = logs.reduce<Record<string, typeof logs>>((accumulator, log) => {
    const bucket = accumulator[log.project_id] ?? [];
    bucket.push(log);
    accumulator[log.project_id] = bucket;
    return accumulator;
  }, {});

  return (
    <Card aria-labelledby="day-heading">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 id="day-heading" className="text-[15px] font-[600] text-foreground">
            {day.business_date}
          </h2>
          <p className="mt-1 text-[11px] text-muted-foreground">
            {day.state === "rest"
              ? "Nothing expected — a rest day."
              : `${day.done_count} of ${day.expected_count} projects recorded.`}
          </p>
        </div>
        {isToday ? (
          <Link
            href="/"
            className="inline-flex min-h-[36px] items-center gap-2 text-[12px] font-[600] text-accent-foreground"
          >
            Record today
            <Icon name="arrow" size={14} />
          </Link>
        ) : null}
      </div>

      {isPending ? <p className="mt-4 text-[12px] text-muted-foreground">Loading…</p> : null}
      {error ? (
        <p className="mt-4 text-[12px] text-destructive">Could not load that day.</p>
      ) : null}

      {!isPending && logs.length === 0 ? (
        <p className="mt-4 rounded-[10px] bg-secondary px-4 py-3 text-[12px] text-muted-foreground">
          {day.state === "rest"
            ? "This day expected nothing, and nothing was written. That is fine."
            : "Nothing was recorded on this day."}
        </p>
      ) : null}

      <div className="mt-4 flex flex-col gap-4">
        {Object.entries(grouped).map(([projectId, entries]) => (
          <section key={projectId} className="flex flex-col gap-2">
            <h3 className="text-[11px] font-[600] uppercase tracking-[1.2px] text-muted-foreground">
              {nameById.get(projectId) ?? "Project"}
            </h3>
            <ul className="flex flex-col gap-2">
              {entries.map((log) => (
                <li
                  key={log.id}
                  className="rounded-[10px] border border-border px-4 py-3 text-[13px] text-foreground"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 flex-col gap-1">
                      <p>{log.content}</p>
                      <span className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                        {log.duration_minutes !== null ? <span>{log.duration_minutes} min</span> : null}
                        {log.backfilled ? (
                          <span className="rounded-[4px] bg-pill px-[6px] py-[1px] text-[10px] font-[550] text-pill-ink">
                            backfilled
                          </span>
                        ) : null}
                        {log.tags.map((tag) => (
                          <span
                            key={tag}
                            className="rounded-[4px] bg-secondary px-[6px] py-[1px] text-[10px]"
                          >
                            {tag}
                          </span>
                        ))}
                      </span>
                    </div>
                    <Link
                      href={`/projects/${log.project_id}`}
                      className="shrink-0 text-[11px] font-[600] text-accent-foreground underline underline-offset-4"
                    >
                      Edit there
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </Card>
  );
}
