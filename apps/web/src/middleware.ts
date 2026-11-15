import { NextResponse, type NextRequest } from "next/server";

/**
 * Route guard. It only checks that a session cookie exists — it cannot verify
 * the signature, and it does not try to. The API is the authority: every
 * request is rejected there with 401 if the session is invalid, and the client
 * reacts by redirecting.
 *
 * /login is always allowed through, otherwise the guard would redirect the
 * login page to itself. There is deliberately no redirect from /login to /
 * when a cookie is present: a stale cookie would bounce the user between the
 * two routes forever.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname === "/login" || request.cookies.has("sid")) {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
