import { NextResponse } from "next/server";
import { SESSION_COOKIE, getSessionCookieOptions } from "../../../../lib/session";

export const dynamic = "force-dynamic";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, "", {
    ...getSessionCookieOptions(),
    maxAge: 0,
  });
  return response;
}
