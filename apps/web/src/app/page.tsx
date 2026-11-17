"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell, LoadingProjects, PageHeading } from "@/components/app-shell";
import { Icon } from "@/components/icon";
import { ApiError, listProjects } from "@/lib/api";

export default function TodayPage() {
  const router = useRouter();
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401)
      router.replace("/login");
  }, [error, router]);
  const active = (data ?? []).filter((project) => project.status === "active");
  return (
    <AppShell>
      <PageHeading
        eyebrow="A LITTLE PROGRESS, EVERY DAY"
        title="Make today count."
        description="You don’t have to do everything. Just keep showing up."
        action={
          <Link className="button secondary" href="/projects#new-project">
            <Icon name="plus" size={17} />
            New project
          </Link>
        }
      />
      <section className="welcome-panel" aria-labelledby="welcome-title">
        <div>
          <span className="tiny-label">YOUR PERSONAL RECORD</span>
          <h2 id="welcome-title">
            Good days start with
            <br />
            one small thing.
          </h2>
          <p>
            Choose a project. Do something that matters.
            <br />
            Leave a little proof of your progress.
          </p>
          <Link href="/projects" className="text-link">
            Find your next small step
            <Icon name="arrow" size={16} />
          </Link>
        </div>
        <svg
          className="welcome-art"
          viewBox="0 0 170 140"
          fill="none"
          aria-hidden="true"
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
          <path
            d="m131 100 11-45 6 1-11 45-5 8-1-9Z"
            fill="#bd613e"
            stroke="#935036"
          />
          <path
            d="M22 41v-9m-4 4h8M145 25v-7m-3.5 3.5h7"
            stroke="#8c9979"
            strokeLinecap="round"
          />
        </svg>
      </section>
      <div className="dashboard-grid">
        <section aria-labelledby="projects-heading">
          <div className="section-heading">
            <h2 id="projects-heading">
              Your active projects
              {data ? <span className="count">{active.length}</span> : null}
            </h2>
            <span className="section-note">One small step at a time</span>
          </div>
          {isPending ? (
            <LoadingProjects />
          ) : error ? (
            <div className="form-error" role="alert">
              Could not load your projects.{" "}
              <button className="text-link" onClick={() => void refetch()}>
                Try again
              </button>
            </div>
          ) : active.length === 0 ? (
            <div className="empty-state">
              <span className="project-symbol">
                <Icon name="projects" size={24} />
              </span>
              <h3>A place for what matters.</h3>
              <p>
                Create your first project. Something you want to keep coming
                back to.
              </p>
              <Link href="/projects#new-project" className="button">
                <Icon name="plus" size={16} />
                Create a project
              </Link>
            </div>
          ) : (
            <ul className="project-list">
              {active.map((project) => (
                <li key={project.id}>
                  <Link
                    href={`/projects/${project.id}`}
                    className="project-row"
                  >
                    <span className="project-symbol">
                      <Icon
                        name="book"
                        style={
                          project.color ? { color: project.color } : undefined
                        }
                      />
                    </span>
                    <div className="project-info">
                      <strong>{project.name}</strong>
                      <p>{project.note || "Ready for your next small step."}</p>
                    </div>
                    <span className="status-pill">
                      <Icon name="clock" size={12} />
                      Not recorded
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <p className="availability">
            <Icon name="info" size={16} />
            <span>
              Recording is not available yet. Projects are ready; logs and daily
              supervision are the next step.
            </span>
          </p>
          <Link href="/projects" className="text-link">
            Manage your projects
            <Icon name="arrow" size={15} />
          </Link>
        </section>
        <aside className="panel" aria-labelledby="rules-heading">
          <h2 id="rules-heading" className="panel-heading">
            A simple agreement.
          </h2>
          <ol className="rule-list">
            <li>
              <span className="rule-number">1</span>
              <div>
                <h3>Write what you did.</h3>
                <p>A project and a few words. That’s all a log needs.</p>
              </div>
            </li>
            <li>
              <span className="rule-number">2</span>
              <div>
                <h3>Keep it honest.</h3>
                <p>
                  A backfill completes your record. It never repairs a streak.
                </p>
              </div>
            </li>
            <li>
              <span className="rule-number">3</span>
              <div>
                <h3>Make room for rest.</h3>
                <p>Rest days don’t add to a streak or break it.</p>
              </div>
            </li>
          </ol>
          <div className="rule-bottom">
            <Icon name="book" size={16} />
            <span>
              A record of your effort.
              <br />
              Something real to look back on.
            </span>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
