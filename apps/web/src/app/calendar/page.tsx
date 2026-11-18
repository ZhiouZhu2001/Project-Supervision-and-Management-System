"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell, PageHeading } from "@/components/app-shell";
import { CalendarDayPanel } from "@/components/calendar-day-panel";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ApiError, getCalendar, listProjects, type CalendarDayState } from "@/lib/api";
import { cn } from "@/lib/utils";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const STATE_STYLE: Record<CalendarDayState, string> = {
  all: "bg-sage-ink text-white",
  most: "bg-sage text-sage-ink",
  partial: "bg-accent text-accent-foreground",
  none: "bg-pill text-pill-ink",
  rest: "bg-secondary text-muted-foreground",
  future: "bg-transparent text-muted-foreground/40",
};

const LEGEND: { state: CalendarDayState; label: string }[] = [
  { state: "all", label: "Everything recorded" },
  { state: "most", label: "Most recorded" },
  { state: "partial", label: "Partly recorded" },
  { state: "none", label: "Nothing recorded" },
  { state: "rest", label: "Nothing expected" },
];

function shiftMonth(month: string, delta: number): string {
  const [yearText, monthText] = month.split("-");
  const index = Number(yearText) * 12 + (Number(monthText) - 1) + delta;
  const year = Math.floor(index / 12);
  const monthNumber = (index % 12) + 1;
  return `${year}-${String(monthNumber).padStart(2, "0")}`;
}

function monthLabel(month: string): string {
  const [yearText, monthText] = month.split("-");
  const names = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  return `${names[Number(monthText) - 1]} ${yearText}`;
}

export default function CalendarPage() {
  const router = useRouter();
  const [month, setMonth] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const { data, error, isPending } = useQuery({
    queryKey: ["calendar", month],
    queryFn: () => getCalendar(month ?? undefined),
  });

  const projects = useQuery({ queryKey: ["projects"], queryFn: () => listProjects() });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);

  const days = data?.days ?? [];
  const leadingBlanks = data ? data.first_weekday - 1 : 0;
  const selectedDay = days.find((day) => day.business_date === selected) ?? null;

  return (
    <AppShell>
      <PageHeading
        eyebrow="WHAT THE DAYS ADD UP TO"
        title="Calendar."
        description="Every day, shaded by how much of it you recorded."
        action={
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              aria-label="Previous month"
              onClick={() => setMonth(shiftMonth(data?.month ?? "", -1))}
              disabled={!data}
            >
              ←
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              aria-label="Next month"
              onClick={() => setMonth(shiftMonth(data?.month ?? "", 1))}
              disabled={!data}
            >
              →
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-[minmax(0,1fr)_260px] items-start gap-7 max-[900px]:grid-cols-1">
        <div className="flex flex-col gap-6">
          <Card>
          <div className="mb-5 flex items-baseline justify-between gap-3">
            <h2 className="text-[15px] font-[600] text-foreground">
              {data ? monthLabel(data.month) : "Loading…"}
            </h2>
            {data ? (
              <span className="text-[11px] text-muted-foreground">
                {days.filter((day) => day.state === "all").length} complete days
              </span>
            ) : null}
          </div>

          {isPending ? (
            <p className="text-[12px] text-muted-foreground">Loading…</p>
          ) : error ? (
            <p className="text-[12px] text-destructive">Could not load the calendar.</p>
          ) : (
            <>
              <div className="grid grid-cols-7 gap-[6px] text-[10px] font-[600] tracking-[1.2px] text-muted-foreground">
                {WEEKDAY_LABELS.map((label) => (
                  <span key={label} className="px-1 py-1 text-center">
                    {label}
                  </span>
                ))}
              </div>
              <div className="mt-1 grid grid-cols-7 gap-[6px]">
                {Array.from({ length: leadingBlanks }).map((_, index) => (
                  <span key={`blank-${index}`} />
                ))}
                {days.map((day) => {
                  const dayNumber = Number(day.business_date.slice(-2));
                  const isToday = data?.today === day.business_date;
                  const isSelected = selected === day.business_date;
                  return (
                    <button
                      key={day.business_date}
                      type="button"
                      onClick={() => setSelected(day.business_date)}
                      aria-pressed={isSelected}
                      aria-label={`${day.business_date}, ${day.state}`}
                      title={`${day.business_date} · ${day.done_count}/${day.expected_count} recorded`}
                      className={cn(
                        "flex aspect-square flex-col items-center justify-center rounded-[8px] text-[12px] font-[550] tabular-nums transition-colors duration-[160ms]",
                        STATE_STYLE[day.state],
                        isToday && "ring-2 ring-foreground ring-offset-2 ring-offset-card",
                        isSelected && "outline outline-2 outline-offset-2 outline-accent-foreground",
                      )}
                    >
                      {dayNumber}
                      {day.backfilled_count > 0 ? (
                        <span
                          aria-label="written later"
                          className="mt-[2px] h-[3px] w-[3px] rounded-full bg-current opacity-70"
                        />
                      ) : null}
                    </button>
                  );
                })}
              </div>
            </>
          )}
          </Card>

          <CalendarDayPanel
            day={selectedDay}
            isToday={data?.today === selectedDay?.business_date}
            projects={projects.data ?? []}
          />
        </div>

        <Card>
          <h2 className="text-[15px] font-[600] text-foreground">How to read it</h2>
          <ul className="mt-4 flex flex-col gap-2">
            {LEGEND.map((entry) => (
              <li key={entry.state} className="flex items-center gap-2 text-[12px] text-muted-foreground">
                <span
                  className={cn("h-4 w-4 shrink-0 rounded-[4px]", STATE_STYLE[entry.state])}
                  aria-hidden="true"
                />
                {entry.label}
              </li>
            ))}
          </ul>
          <p className="mt-4 flex items-start gap-2 border-t border-border pt-3 text-[11px] text-muted-foreground">
            <Icon name="info" size={14} />
            <span>
              Days with nothing expected stay neutral: rest days, before a project started, or
              while it was paused.
            </span>
          </p>
        </Card>
      </div>
    </AppShell>
  );
}
