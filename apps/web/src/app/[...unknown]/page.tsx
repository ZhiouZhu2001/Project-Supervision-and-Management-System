import { notFound, redirect } from "next/navigation";

/**
 * Catch-all for every URL the application does not define.
 *
 * Without this, an unknown path falls through to the framework's built-in
 * "404 This page could not be found" page. That is a dead end, and it is the
 * wrong thing to show: a path the app does not define is not a screen the owner
 * can be in, so it is treated like an unauthenticated entry point and sent to
 * /login — the same destination `middleware.ts` picks when there is no session.
 *
 * A catch-all route is used instead of `not-found.tsx` on purpose. `notFound()`
 * is also what a real route will call when an entity is missing (a deleted
 * project id, say); that case must keep its own not-found page rather than
 * bounce to login. Only "this URL is not part of the application" lands here.
 *
 * Catch-all routes always rank below every defined route, so pages added later
 * cannot collide with this file.
 */
export default async function UnknownRoute({
  params,
}: {
  params: Promise<{ unknown: string[] }>;
}): Promise<never> {
  const { unknown } = await params;
  const lastSegment = unknown.at(-1) ?? "";

  // A request for a missing file — a favicon, a source map — is not a screen
  // the owner is trying to reach, so it keeps the plain 404. Redirecting it to
  // /login would answer every page load's favicon request with the login HTML.
  // This only ever sees URLs with no route behind them, so it cannot shadow a
  // real page.
  if (lastSegment.includes(".")) {
    notFound();
  }

  redirect("/login");
}
