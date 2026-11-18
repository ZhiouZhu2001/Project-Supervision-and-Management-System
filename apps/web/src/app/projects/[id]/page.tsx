"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AppShell, LoadingProjects, PageHeading } from "@/components/app-shell";
import { Icon } from "@/components/icon";
import { ProjectLogs } from "@/components/project-logs";
import { ProjectSchedule } from "@/components/project-schedule";
import { ProjectStatusCard } from "@/components/project-status-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, deleteProject, getProject, updateProject, type Project } from "@/lib/api";
import { cn } from "@/lib/utils";

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
    mutationFn: (patch: Parameters<typeof updateProject>[1]) => updateProject(id, patch),
    onSuccess: async (project: Project) => {
      setSaved(true);
      queryClient.setQueryData(["project", id], project);
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const remove = useMutation({
    mutationFn: () => deleteProject(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      await queryClient.invalidateQueries({ queryKey: ["today"] });
      router.replace("/projects");
    },
  });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
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

  if (isPending) {
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
  }

  if (!data) {
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
        <div className="flex gap-3">
          <Button asChild>
            <Link href="/projects">Back to projects</Link>
          </Button>
          {!(error instanceof ApiError && error.status === 404) ? (
            <Button variant="secondary" onClick={() => void refetch()}>
              Try again
            </Button>
          ) : null}
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Link
        href="/projects"
        className="mb-6 inline-flex items-center gap-2 text-[12px] font-[600] text-muted-foreground"
      >
        <Icon name="back" size={16} />
        All projects
      </Link>

      <PageHeading
        eyebrow="KEEP COMING BACK"
        title={data.name}
        description={data.note || "A little commitment. A place to see it grow."}
      />

      <div className="grid grid-cols-[minmax(0,1fr)_320px] items-start gap-7 max-[1150px]:grid-cols-[minmax(0,1fr)_285px] max-[1150px]:gap-5 max-[900px]:grid-cols-1">
        <div className="flex flex-col gap-6">
          <Card aria-labelledby="details-heading">
            <h2 id="details-heading" className="text-[15px] font-[600] text-foreground">
              Project details
            </h2>

            <form onSubmit={save} aria-busy={mutation.isPending} className="mt-5 flex flex-col gap-5">
              <div className="flex flex-col gap-2">
                <Label htmlFor="project-name">Project name</Label>
                <Input
                  id="project-name"
                  required
                  maxLength={60}
                  value={name}
                  onChange={(event) => {
                    setName(event.target.value);
                    setSaved(false);
                  }}
                />
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="project-note">
                  Note
                  <span className="ml-2 text-[11px] font-[400] text-muted-foreground">
                    optional
                  </span>
                </Label>
                <Textarea
                  id="project-note"
                  value={note}
                  rows={4}
                  maxLength={2000}
                  onChange={(event) => {
                    setNote(event.target.value);
                    setSaved(false);
                  }}
                  placeholder="What does this project mean to you?"
                />
                <span className="text-[11px] text-muted-foreground">
                  A little context for the days you need it.
                </span>
              </div>

              <fieldset className="flex flex-col gap-2">
                <legend className="mb-2 text-[13px] font-[550] text-foreground">
                  Project colour
                </legend>
                <div className="flex flex-wrap items-center gap-[10px]">
                  {PALETTE.map((swatch) => (
                    <button
                      key={swatch.value}
                      type="button"
                      aria-label={swatch.name}
                      aria-pressed={color === swatch.value}
                      onClick={() => {
                        setColor(swatch.value);
                        setSaved(false);
                      }}
                      className={cn(
                        "grid h-7 w-7 place-items-center rounded-full transition-shadow duration-[160ms]",
                        color === swatch.value &&
                          "ring-2 ring-foreground ring-offset-2 ring-offset-card",
                      )}
                    >
                      <span
                        aria-hidden="true"
                        className="block h-7 w-7 rounded-full"
                        style={{ backgroundColor: swatch.value }}
                      />
                    </button>
                  ))}
                  <Button
                    type="button"
                    variant="subtle"
                    size="sm"
                    aria-pressed={color === null}
                    onClick={() => {
                      setColor(null);
                      setSaved(false);
                    }}
                  >
                    None
                  </Button>
                </div>
              </fieldset>

              {validation || mutation.isError ? (
                <p role="alert" className="text-[12px] text-destructive">
                  {validation ||
                    (mutation.error instanceof ApiError &&
                    mutation.error.code === "VALIDATION_ERROR"
                      ? "A project needs a name of 1–60 characters."
                      : "Could not save your changes. Try again.")}
                </p>
              ) : null}

              <div className="flex items-center gap-3">
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? "Saving…" : "Save changes"}
                </Button>
                {saved ? (
                  <span role="status" className="inline-flex items-center gap-[6px] text-[12px] text-sage-ink">
                    <Icon name="check" size={16} />
                    Changes saved
                  </span>
                ) : null}
              </div>
            </form>
          </Card>

          <ProjectLogs projectId={id} />

          <Card>
            <h2 className="text-[15px] font-[600] text-foreground">Delete this project</h2>
            <p className="mt-1 text-[12px] text-muted-foreground">
              Hides the project and its logs. You can restore it for thirty days, after which it is
              gone for good.
            </p>
            {confirmingDelete ? (
              <div className="mt-4 flex flex-col gap-3">
                <p role="alert" className="text-[12px] text-foreground">
                  Delete “{data.name}”? Its logs stop counting immediately.
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setConfirmingDelete(false)}
                  >
                    Keep it
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    disabled={remove.isPending}
                    onClick={() => remove.mutate()}
                  >
                    {remove.isPending ? "Deleting…" : "Yes, delete"}
                  </Button>
                </div>
                {remove.isError ? (
                  <p role="alert" className="text-[11px] text-destructive">
                    Could not delete this project.
                  </p>
                ) : null}
              </div>
            ) : (
              <Button
                type="button"
                variant="subtle"
                size="sm"
                className="mt-4"
                onClick={() => setConfirmingDelete(true)}
              >
                Delete project
              </Button>
            )}
          </Card>
        </div>

        <aside className="flex flex-col gap-4">
          <Card>
            <h2 className="text-[15px] font-[600] text-foreground">At a glance</h2>
            <dl className="mt-4 flex flex-col gap-3">
              <div className="flex items-center justify-between gap-3">
                <dt className="text-[12px] text-muted-foreground">Status</dt>
                <dd>
                  <span
                    className={cn(
                      "inline-flex items-center gap-[6px] whitespace-nowrap rounded-[5px] px-[9px] py-[5px] text-[10px] font-[550]",
                      data.status === "active"
                        ? "bg-sage text-sage-ink"
                        : "bg-pill text-pill-ink",
                    )}
                  >
                    {data.status}
                  </span>
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-[12px] text-muted-foreground">Start date</dt>
                <dd className="text-[12px] text-foreground">{data.start_date}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-[12px] text-muted-foreground">Created business day</dt>
                <dd className="text-[12px] text-foreground">{data.created_business_date}</dd>
              </div>
            </dl>
            <p className="mt-4 border-t border-border pt-3 text-[11px] text-muted-foreground">
              Start date and status stay unchanged when you edit these details.
            </p>
          </Card>

          <ProjectSchedule projectId={id} />

          <ProjectStatusCard project={data} />

          <p className="flex items-start gap-2 rounded-[10px] bg-[#f3f4ec] px-4 py-3 text-[12px] text-muted-foreground">
            <Icon name="info" size={17} />
            <span>
              Status changes are dated. Changing them today never rewrites a past streak.
            </span>
          </p>
        </aside>
      </div>
    </AppShell>
  );
}
