import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center gap-8 px-6 py-16">
      <header className="flex flex-col gap-2">
        <h1 className="text-xl font-semibold tracking-tight">Project Supervision</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Sign in to record what you did today.
        </p>
      </header>

      <LoginForm />

      <p className="text-xs text-neutral-500">
        There is one account. It is created from configuration on first start; there is no
        registration.
      </p>
    </main>
  );
}
