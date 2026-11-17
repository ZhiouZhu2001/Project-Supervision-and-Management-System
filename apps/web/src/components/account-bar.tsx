"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { ApiError, logout, me } from "@/lib/api";
import { Icon } from "@/components/icon";

export function AccountBar() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: account, error } = useQuery({
    queryKey: ["account"],
    queryFn: me,
    retry: false,
  });
  useEffect(() => {
    if (error instanceof ApiError && error.status === 401)
      router.replace("/login");
  }, [error, router]);
  const signOut = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
      router.replace("/login");
      router.refresh();
    },
  });
  return (
    <div>
      <div className="account">
        <span className="avatar" aria-hidden="true">
          {(account?.display_name ?? account?.email ?? "O")
            .slice(0, 1)
            .toUpperCase()}
        </span>
        <div className="account-copy">
          <strong>{account?.display_name ?? "Owner"}</strong>
          <span>
            {error
              ? "Account unavailable"
              : (account?.email ?? "Loading account…")}
          </span>
        </div>
        <button
          type="button"
          className="icon-button"
          aria-label="Sign out"
          title="Sign out"
          disabled={signOut.isPending}
          onClick={() => signOut.mutate()}
        >
          <Icon name="logout" size={17} />
        </button>
      </div>
      {signOut.isError ? (
        <p role="alert" className="form-error">
          Could not sign out. Try again.
        </p>
      ) : null}
    </div>
  );
}
