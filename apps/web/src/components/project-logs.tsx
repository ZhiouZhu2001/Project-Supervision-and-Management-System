"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, listLogs, updateLog, type LogView } from "@/lib/api";

export function ProjectLogs({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const { data, isPending, error } = useQuery({
    queryKey: ["logs", projectId],
    queryFn: () => listLogs(projectId),
  });

  const [editing, setEditing] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [duration, setDuration] = useState("");
  const [tags, setTags] = useState("");
  const [failure, setFailure] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: (id: string) =>
      updateLog(id, {
        content: content.trim(),
        duration_minutes: duration.trim() === "" ? null : Number(duration),
        tags: tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      }),
    onSuccess: async () => {
      setEditing(null);
      setFailure(null);
      await queryClient.invalidateQueries({ queryKey: ["logs", projectId] });
      await queryClient.invalidateQueries({ queryKey: ["today"] });
    },
    onError: (cause: unknown) => {
      setFailure(
        cause instanceof ApiError && cause.code === "VALIDATION_ERROR"
          ? "A log needs some text and a duration under a day."
          : "Could not save. Try again.",
      );
    },
  });

  function startEditing(log: LogView) {
    setEditing(log.id);
    setContent(log.content);
    setDuration(log.duration_minutes === null ? "" : String(log.duration_minutes));
    setTags(log.tags.join(", "));
    setFailure(null);
  }

  const logs = data ?? [];

  return (
    <Card aria-labelledby="logs-heading">
      <div className="mb-5 flex items-center justify-between gap-3">
        <h2 id="logs-heading" className="text-[15px] font-[600] text-foreground">
          Project logs
        </h2>
        <span className="text-[11px] text-muted-foreground">
          {logs.length === 0 ? "Nothing yet" : `${logs.length} recorded`}
        </span>
      </div>

      {isPending ? <p className="text-[12px] text-muted-foreground">Loading…</p> : null}
      {error ? (
        <p className="text-[12px] text-destructive">Could not load the log timeline.</p>
      ) : null}

      {!isPending && logs.length === 0 ? (
        <div className="flex items-center gap-[15px]">
          <span className="grid h-[44px] w-[42px] shrink-0 place-items-center rounded-[10px] bg-sage text-sage-ink">
            <Icon name="book" />
          </span>
          <div className="flex flex-col gap-1">
            <strong className="text-[13px] font-[600] text-foreground">The story starts here.</strong>
            <p className="text-[12px] text-muted-foreground">
              Record something from the today screen and it will appear here.
            </p>
          </div>
        </div>
      ) : null}

      <ul className="flex flex-col gap-3">
        {logs.map((log) => (
          <li key={log.id} className="rounded-[10px] border border-border px-4 py-3">
            {editing === log.id ? (
              <div className="flex flex-col gap-3">
                <Textarea
                  rows={3}
                  maxLength={2000}
                  value={content}
                  onChange={(event) => setContent(event.target.value)}
                />
                <div className="flex flex-wrap items-center gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={1440}
                    value={duration}
                    onChange={(event) => setDuration(event.target.value)}
                    placeholder="minutes"
                    className="w-[120px]"
                    aria-label="Duration in minutes"
                  />
                  <Input
                    value={tags}
                    onChange={(event) => setTags(event.target.value)}
                    placeholder="tags, comma separated"
                    className="flex-1"
                    aria-label="Tags"
                  />
                </div>
                {failure ? (
                  <p role="alert" className="text-[11px] text-destructive">
                    {failure}
                  </p>
                ) : null}
                <div className="flex items-center gap-2">
                  <Button type="button" size="sm" disabled={save.isPending} onClick={() => save.mutate(log.id)}>
                    {save.isPending ? "Saving…" : "Save"}
                  </Button>
                  <Button type="button" variant="subtle" size="sm" onClick={() => setEditing(null)}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 flex-col gap-1">
                  <span className="flex items-center gap-2 text-[11px] text-muted-foreground">
                    {log.business_date}
                    {log.backfilled ? (
                      <span className="rounded-[4px] bg-pill px-[6px] py-[1px] text-[10px] font-[550] text-pill-ink">
                        backfilled
                      </span>
                    ) : null}
                    {log.duration_minutes !== null ? <span>· {log.duration_minutes} min</span> : null}
                  </span>
                  <p className="text-[13px] text-foreground">{log.content}</p>
                  {log.tags.length > 0 ? (
                    <span className="flex flex-wrap gap-1">
                      {log.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-[4px] bg-secondary px-[6px] py-[1px] text-[10px] text-muted-foreground"
                        >
                          {tag}
                        </span>
                      ))}
                    </span>
                  ) : null}
                </div>
                <Button type="button" variant="subtle" size="sm" onClick={() => startEditing(log)}>
                  Edit
                </Button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}
