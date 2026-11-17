"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { ApiError, logout, me } from "@/lib/api";

export function AccountBar() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: account, error } = useQuery({
    queryKey: ["account"],
    queryFn: me,
    retry: false,
  });

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) router.replace("/login");
  }, [error, router]);

  const signOut = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
      router.replace("/login");
      router.refresh();
    },
  });

  const initial = (account?.display_name ?? account?.email ?? "O").slice(0, 1).toUpperCase();

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-[10px]">
        <span
          aria-hidden="true"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-foreground text-[12px] font-[600] text-primary-foreground"
        >
          {initial}
        </span>
        <div className="flex min-w-0 flex-col leading-[1.35]">
          <strong className="truncate text-[12px] font-[600] text-foreground">
            {account?.display_name ?? "Owner"}
          </strong>
          <span className="truncate text-[11px] text-muted-foreground">
            {error ? "Account unavailable" : (account?.email ?? "Loading account…")}
          </span>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="ml-auto border-transparent"
          aria-label="Sign out"
          title="Sign out"
          disabled={signOut.isPending}
          onClick={() => signOut.mutate()}
        >
          <Icon name="logout" size={17} />
        </Button>
      </div>
      {signOut.isError ? (
        <p role="alert" className="text-[12px] text-destructive">
          Could not sign out. Try again.
        </p>
      ) : null}
    </div>
  );
}
