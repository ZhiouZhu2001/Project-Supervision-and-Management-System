"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, login } from "@/lib/api";
import { Icon } from "@/components/icon";

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
    <form onSubmit={onSubmit} className="form" aria-busy={pending}>
      <label className="field">
        <span>Email address</span>
        <input
          type="email"
          name="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />
      </label>
      <div className="field">
        <label htmlFor="password">Password</label>
        <div className="password-field">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            aria-describedby={error ? "login-error" : undefined}
          />
          <button
            className="icon-button"
            type="button"
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
            onClick={() => setShowPassword(!showPassword)}
          >
            <Icon name="eye" size={18} />
          </button>
        </div>
      </div>
      {error ? (
        <p id="login-error" role="alert" className="form-error">
          {error}
        </p>
      ) : null}
      <button type="submit" disabled={pending} className="button">
        {pending ? "Signing in…" : "Sign in"}
        <Icon name="arrow" size={17} />
      </button>
    </form>
  );
}
