"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Icon } from "@/components/icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, login } from "@/lib/api";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

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
    <form onSubmit={onSubmit} className="flex flex-col gap-5" aria-busy={pending}>
      <div className="flex flex-col gap-2">
        <Label htmlFor="email">Email address</Label>
        <Input
          id="email"
          type="email"
          name="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="password">Password</Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            aria-describedby={error ? "login-error" : undefined}
            className="pr-11"
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-[6px] top-1/2 -translate-y-1/2 border-transparent"
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
            onClick={() => setShowPassword(!showPassword)}
          >
            <Icon name="eye" size={18} />
          </Button>
        </div>
      </div>

      {error ? (
        <p id="login-error" role="alert" className="text-[12px] text-destructive">
          {error}
        </p>
      ) : null}

      <Button type="submit" disabled={pending} className="mt-1 w-full">
        {pending ? "Signing in…" : "Sign in"}
        <Icon name="arrow" size={17} />
      </Button>
    </form>
  );
}
