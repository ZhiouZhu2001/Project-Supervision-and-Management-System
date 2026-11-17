"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AppShell, LoadingProjects, PageHeading } from "@/components/app-shell";
import { Icon } from "@/components/icon";
import { ApiError, getProject, updateProject, type Project } from "@/lib/api";

const PALETTE = [
  { value: "#71717a", name: "Stone" },
  { value: "#ef4444", name: "Red" },
  { value: "#f59e0b", name: "Amber" },
  { value: "#10b981", name: "Green" },
  { value: "#3b82f6", name: "Blue" },
  { value: "#8b5cf6", name: "Violet" },
];

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ["project", id],
    queryFn: () => getProject(id),
  });
  const [name, setName] = useState("");
  const [note, setNote] = useState("");
  const [color, setColor] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [validation, setValidation] = useState<string | null>(null);
  const seededId = useRef<string | null>(null);
  useEffect(() => {
    // Background refetches must not replace the owner's unsaved work.
    if (data && seededId.current !== data.id) {
      seededId.current = data.id;
      setName(data.name);
      setNote(data.note ?? "");
      setColor(data.color);
    }
  }, [data]);
  const mutation = useMutation({
    mutationFn: (patch: Parameters<typeof updateProject>[1]) =>
      updateProject(id, patch),
    onSuccess: async (project: Project) => {
      setSaved(true);
      queryClient.setQueryData(["project", id], project);
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401)
      router.replace("/login");
  }, [error, router]);
  function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    setValidation(null);
    if (!name.trim()) {
      setValidation("A project needs a name of 1–60 characters.");
      return;
    }
    mutation.mutate({ name: name.trim(), note: note.trim() || null, color });
  }
  if (isPending)
    return (
      <AppShell>
        <PageHeading
          eyebrow="YOUR PROJECT"
          title="A moment…"
          description="Getting your project ready."
        />
        <LoadingProjects />
      </AppShell>
    );
  if (!data)
    return (
      <AppShell>
        <PageHeading
          eyebrow="YOUR PROJECT"
          title={
            error instanceof ApiError && error.status === 404
              ? "Project not found."
              : "Could not load this project."
          }
          description="Your other projects are still just a click away."
        />
        <Link className="button" href="/projects">
          Back to projects
        </Link>
        {!(error instanceof ApiError && error.status === 404) ? (
          <button className="button secondary" onClick={() => void refetch()}>
            Try again
          </button>
        ) : null}
      </AppShell>
    );
  return (
    <AppShell>
      <Link href="/projects" className="back-link">
        <Icon name="back" size={16} />
        All projects
      </Link>
      <PageHeading
        eyebrow="KEEP COMING BACK"
        title={data.name}
        description={
          data.note || "A little commitment. A place to see it grow."
        }
      />
      <div className="project-layout">
        <div>
          <section
            className="panel detail-panel"
            aria-labelledby="details-heading"
          >
            <h2 id="details-heading" className="panel-heading">
              Project details
            </h2>
            <form
              className="form"
              onSubmit={save}
              aria-busy={mutation.isPending}
            >
              <label className="field">
                <span>Project name</span>
                <input
                  required
                  maxLength={60}
                  value={name}
                  onChange={(event) => {
                    setName(event.target.value);
                    setSaved(false);
                  }}
                />
              </label>
              <label className="field">
                <span>
                  Note<span className="optional">optional</span>
                </span>
                <textarea
                  value={note}
                  rows={4}
                  maxLength={2000}
                  onChange={(event) => {
                    setNote(event.target.value);
                    setSaved(false);
                  }}
                  placeholder="What does this project mean to you?"
                />
                <span className="helper">
                  A little context for the days you need it.
                </span>
              </label>
              <fieldset className="field">
                <legend>Project colour</legend>
                <div className="color-options">
                  {PALETTE.map((swatch) => (
                    <button
                      key={swatch.value}
                      type="button"
                      aria-label={swatch.name}
                      aria-pressed={color === swatch.value}
                      className="swatch"
                      onClick={() => {
                        setColor(swatch.value);
                        setSaved(false);
                      }}
                    >
                      <span style={{ backgroundColor: swatch.value }} />
                    </button>
                  ))}
                  <button
                    type="button"
                    aria-pressed={color === null}
                    className="button subtle"
                    onClick={() => {
                      setColor(null);
                      setSaved(false);
                    }}
                  >
                    None
                  </button>
                </div>
              </fieldset>
              {validation || mutation.isError ? (
                <p role="alert" className="form-error">
                  {validation ||
                    (mutation.error instanceof ApiError &&
                    mutation.error.code === "VALIDATION_ERROR"
                      ? "A project needs a name of 1–60 characters."
                      : "Could not save your changes. Try again.")}
                </p>
              ) : null}
              <div className="form-actions">
                <button
                  type="submit"
                  disabled={mutation.isPending}
                  className="button"
                >
                  {mutation.isPending ? "Saving…" : "Save changes"}
                </button>
                {saved ? (
                  <span role="status" className="success">
                    <Icon name="check" size={16} />
                    Changes saved
                  </span>
                ) : null}
              </div>
            </form>
          </section>
          <section
            className="panel timeline-panel"
            aria-labelledby="logs-heading"
          >
            <div className="section-heading">
              <h2 id="logs-heading">Project logs</h2>
              <span className="status-pill">Not recorded</span>
            </div>
            <div className="timeline-empty">
              <span className="project-symbol">
                <Icon name="book" />
              </span>
              <div>
                <strong>The story starts here.</strong>
                <p>No logs yet. Recording is not available in this version.</p>
              </div>
            </div>
          </section>
        </div>
        <aside>
          <section className="panel">
            <h2 className="panel-heading">At a glance</h2>
            <dl className="project-facts">
              <div>
                <dt>Status</dt>
                <dd>
                  <span
                    className={`status-pill ${data.status === "active" ? "active" : ""}`}
                  >
                    {data.status}
                  </span>
                </dd>
              </div>
              <div>
                <dt>Start date</dt>
                <dd>{data.start_date}</dd>
              </div>
              <div>
                <dt>Created business day</dt>
                <dd>{data.created_business_date}</dd>
              </div>
            </dl>
            <p className="helper">
              Start date and status stay unchanged when you edit these details.
            </p>
          </section>
          <div className="availability">
            <Icon name="info" size={17} />
            <span>
              Streaks will appear when recording is available. Every project
              will have its own streak.
            </span>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
