"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppShell, LoadingProjects, PageHeading } from "@/components/app-shell";
import { Icon } from "@/components/icon";
import { QuickLogForm } from "@/components/quick-log-form";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ApiError, getToday } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function TodayPage() {
  const router = useRouter();
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ["today"],
    queryFn: getToday,
  });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);

  const projects = data?.projects ?? [];
  const recordedCount = projects.filter((project) => project.recorded).length;

  return (
    <AppShell>
      <PageHeading
        eyebrow="A LITTLE PROGRESS, EVERY DAY"
        title="Make today count."
        description="You don’t have to do everything. Just keep showing up."
        action={
          <Button asChild variant="secondary">
            <Link href="/projects#new-project">
              <Icon name="plus" size={17} />
              New project
            </Link>
          </Button>
        }
      />

      {projects.length > 0 ? (
        <Card className="mb-8">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div>
              <p className="mb-2 text-[10px] font-[650] tracking-[2px] text-accent-foreground">
                TODAY’S RECORD
              </p>
              <h2 className="font-serif text-[27px] leading-[1.2] tracking-[-0.5px] text-foreground">
                What did you do today?
              </h2>
            </div>
            <span className="text-[11px] text-muted-foreground">
              {recordedCount} of {projects.length} recorded
            </span>
          </div>
          <p className="mt-2 text-[13px] text-muted-foreground">
            One project, a few words. That is the whole ritual.
          </p>
          <QuickLogForm projects={projects} />
        </Card>
      ) : null}

      <div className="grid grid-cols-[minmax(0,1fr)_280px] items-start gap-7 max-[1150px]:grid-cols-[minmax(0,1fr)_245px] max-[1150px]:gap-5 max-[900px]:grid-cols-1">
        <section aria-labelledby="projects-heading">
          <div className="mb-3 flex items-baseline justify-between gap-3">
            <h2 id="projects-heading" className="text-[15px] font-[600] text-foreground">
              Your active projects
              {data ? (
                <span className="ml-2 rounded-full bg-secondary px-2 py-[2px] text-[11px] font-[600] text-muted-foreground">
                  {projects.length}
                </span>
              ) : null}
            </h2>
            <span className="text-[11px] text-muted-foreground">One small step at a time</span>
          </div>

          {isPending ? (
            <LoadingProjects />
          ) : error ? (
            <p role="alert" className="text-[12px] text-destructive">
              Could not load today.{" "}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => void refetch()}
              >
                Try again
              </button>
            </p>
          ) : projects.length === 0 ? (
            <Card className="flex flex-col items-start gap-3">
              <span className="grid h-[44px] w-[42px] place-items-center rounded-[10px] bg-sage text-sage-ink">
                <Icon name="projects" size={24} />
              </span>
              <h3 className="text-[15px] font-[600]">A place for what matters.</h3>
              <p className="text-[13px] text-muted-foreground">
                Create your first project. Something you want to keep coming back to.
              </p>
              <Button asChild>
                <Link href="/projects#new-project">
                  <Icon name="plus" size={16} />
                  Create a project
                </Link>
              </Button>
            </Card>
          ) : (
            <ul className="flex flex-col gap-2">
              {projects.map((project) => (
                <li key={project.id}>
                  <Link
                    href={`/projects/${project.id}`}
                    className="flex items-center gap-[15px] rounded-[10px] border border-border bg-card px-5 py-[22px] transition-colors duration-[160ms] hover:border-[#cfd3c6] max-[1150px]:gap-3 max-[1150px]:px-[15px] max-[1150px]:py-[18px] max-[700px]:px-[14px] max-[700px]:py-[17px]"
                  >
                    <span className="grid h-[44px] w-[42px] shrink-0 place-items-center rounded-[10px] bg-sage text-sage-ink">
                      <Icon
                        name="book"
                        style={project.color ? { color: project.color } : undefined}
                      />
                    </span>
                    <div className="flex min-w-0 flex-col">
                      <strong className="truncate text-[14px] font-[600] text-foreground">
                        {project.name}
                      </strong>
                      <p className="truncate text-[12px] text-muted-foreground">
                        {project.recorded && project.last_log
                          ? project.last_log.content
                          : (project.note ?? "Ready for your next small step.")}
                      </p>
                    </div>
                    <div className="ml-auto flex shrink-0 flex-col items-end gap-1">
                      <span
                        className={cn(
                          "inline-flex items-center gap-[6px] whitespace-nowrap rounded-[5px] px-[9px] py-[5px] text-[10px] font-[550]",
                          project.recorded || project.is_rest_day
                            ? "bg-sage text-sage-ink"
                            : "bg-pill text-pill-ink",
                        )}
                      >
                        <Icon
                          name={project.recorded ? "check" : project.is_rest_day ? "rest" : "clock"}
                          size={12}
                        />
                        {project.recorded
                          ? "Recorded"
                          : project.is_rest_day
                            ? "Rest day"
                            : "Not recorded"}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {project.current_streak === 0
                          ? "No streak yet"
                          : `${project.current_streak}-day streak`}
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}

          <Link
            href="/projects"
            className="inline-flex min-h-[44px] items-center gap-2 text-[13px] font-[600] text-accent-foreground"
          >
            Manage your projects
            <Icon name="arrow" size={15} />
          </Link>
        </section>

        <Card aria-labelledby="rules-heading" className="max-[900px]:mt-2">
          <h2 id="rules-heading" className="text-[15px] font-[600] text-foreground">
            A simple agreement.
          </h2>
          <ol className="mt-5 flex flex-col gap-5 max-[900px]:grid max-[900px]:grid-cols-3 max-[900px]:gap-4 max-[700px]:block">
            {[
              {
                title: "Write what you did.",
                body: "A project and a few words. That’s all a log needs.",
              },
              {
                title: "Keep it honest.",
                body: "A backfill completes your record. It never repairs a streak.",
              },
              {
                title: "Make room for rest.",
                body: "Rest days don’t add to a streak or break it.",
              },
            ].map((rule, index) => (
              <li key={rule.title} className="flex gap-3 max-[700px]:mb-5">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full border border-border text-[11px] font-[600] text-muted-foreground">
                  {index + 1}
                </span>
                <div className="flex flex-col gap-1">
                  <h3 className="text-[13px] font-[600] text-foreground">{rule.title}</h3>
                  <p className="text-[12px] text-muted-foreground">{rule.body}</p>
                </div>
              </li>
            ))}
          </ol>
          <div className="mt-5 flex items-start gap-2 border-t border-border pt-4 text-[11px] text-muted-foreground">
            <Icon name="book" size={16} />
            <span>
              A record of your effort.
              <br />
              Something real to look back on.
            </span>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
