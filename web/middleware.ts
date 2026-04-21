import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TPO_COOKIE = "verifai_tpo_session";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (!pathname.startsWith("/tpo")) {
    return NextResponse.next();
  }

  const hasTpoCookie = Boolean(request.cookies.get(TPO_COOKIE)?.value);
  const isLoginPage = pathname === "/tpo/login";

  if (!hasTpoCookie && !isLoginPage) {
    const url = request.nextUrl.clone();
    url.pathname = "/tpo/login";
    return NextResponse.redirect(url);
  }

  if (hasTpoCookie && isLoginPage) {
    const url = request.nextUrl.clone();
    url.pathname = "/tpo/candidates";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/tpo", "/tpo/:path*"],
};
