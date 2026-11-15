"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, login } from "@/lib/api";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await login(email, password);
      router.replace("/");
      router.refresh();
    } catch (cause) {
      setError(
        cause instanceof ApiError && cause.code === "INVALID_CREDENTIALS"
          ? "Email or password is incorrect."
          : "Could not sign in. Try again.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-neutral-600 dark:text-neutral-400">Email</span>
        <input
          type="email"
          name="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="rounded-lg border border-neutral-300 bg-transparent px-3 py-2 outline-none focus:border-neutral-500 dark:border-neutral-700"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="text-neutral-600 dark:text-neutral-400">Password</span>
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded-lg border border-neutral-300 bg-transparent px-3 py-2 outline-none focus:border-neutral-500 dark:border-neutral-700"
        />
      </label>

      {error ? (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-neutral-100 dark:text-neutral-900"
      >
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
