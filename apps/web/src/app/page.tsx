"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppShell, LoadingProjects, PageHeading } from "@/components/app-shell";
import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ApiError, listProjects, type Project } from "@/lib/api";

export default function TodayPage() {
  const router = useRouter();
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);

  const active = (data ?? []).filter((project: Project) => project.status === "active");

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

      <section
        aria-labelledby="welcome-title"
        className="relative mb-[34px] flex justify-between gap-7 overflow-hidden rounded-[14px] border border-welcome-line bg-welcome px-8 py-[30px] max-[700px]:mb-7 max-[700px]:gap-3 max-[700px]:p-6"
      >
        <div className="min-w-0">
          <span className="text-[10px] font-[600] tracking-[1.6px] text-sage-ink/80">
            YOUR PERSONAL RECORD
          </span>
          <h2
            id="welcome-title"
            className="mt-[10px] font-serif text-[31px] leading-[1.2] tracking-[-0.5px] text-foreground max-[700px]:text-[26px]"
          >
            Good days start with
            <br />
            one small thing.
          </h2>
          <p className="mt-3 text-[13px] text-muted-foreground">
            Choose a project. Do something that matters.
            <br />
            Leave a little proof of your progress.
          </p>
          <Link
            href="/projects"
            className="mt-1 inline-flex min-h-[44px] items-center gap-2 text-[13px] font-[600] text-accent-foreground"
          >
            Find your next small step
            <Icon name="arrow" size={16} />
          </Link>
        </div>

        <svg
          viewBox="0 0 170 140"
          fill="none"
          aria-hidden="true"
          className="h-[140px] w-[170px] shrink-0 text-[#8c9979] max-[700px]:h-[100px] max-[700px]:w-[100px]"
        >
          <path d="M20 121h133" stroke="currentColor" strokeWidth="1.5" />
          <rect
            x="37"
            y="24"
            width="84"
            height="100"
            rx="5"
            transform="rotate(-9 37 24)"
            fill="#d9dfcb"
            stroke="#8c9979"
          />
          <rect
            x="48"
            y="15"
            width="84"
            height="107"
            rx="5"
            transform="rotate(6 48 15)"
            fill="#fafbf2"
            stroke="#8c9979"
          />
          <path
            d="m65 43 5 6 10-11M87 45l25 3M62 65l5 6 10-11M85 67l25 3M61 87l5 6 10-11M83 89l24 3"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="m131 100 11-45 6 1-11 45-5 8-1-9Z" fill="#bd613e" stroke="#935036" />
          <path
            d="M22 41v-9m-4 4h8M145 25v-7m-3.5 3.5h7"
            stroke="#8c9979"
            strokeLinecap="round"
          />
        </svg>
      </section>

      <div className="grid grid-cols-[minmax(0,1fr)_280px] items-start gap-7 max-[1150px]:grid-cols-[minmax(0,1fr)_245px] max-[1150px]:gap-5 max-[900px]:grid-cols-1">
        <section aria-labelledby="projects-heading">
          <div className="mb-3 flex items-baseline justify-between gap-3">
            <h2 id="projects-heading" className="text-[15px] font-[600] text-foreground">
              Your active projects
              {data ? (
                <span className="ml-2 rounded-full bg-secondary px-2 py-[2px] text-[11px] font-[600] text-muted-foreground">
                  {active.length}
                </span>
              ) : null}
            </h2>
            <span className="text-[11px] text-muted-foreground">One small step at a time</span>
          </div>

          {isPending ? (
            <LoadingProjects />
          ) : error ? (
            <p role="alert" className="text-[12px] text-destructive">
              Could not load your projects.{" "}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => void refetch()}
              >
                Try again
              </button>
            </p>
          ) : active.length === 0 ? (
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
              {active.map((project) => (
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
                        {project.note || "Ready for your next small step."}
                      </p>
                    </div>
                    <span className="ml-auto inline-flex items-center gap-[6px] whitespace-nowrap rounded-[5px] bg-pill px-[9px] py-[5px] text-[10px] font-[550] text-pill-ink">
                      <Icon name="clock" size={12} />
                      Not recorded
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}

          <p className="mt-4 flex items-start gap-2 rounded-[10px] bg-[#f3f4ec] px-4 py-3 text-[12px] text-muted-foreground">
            <Icon name="info" size={16} />
            <span>
              Recording is not available yet. Projects are ready; logs and daily supervision are
              the next step.
            </span>
          </p>

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
