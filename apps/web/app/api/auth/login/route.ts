import { NextResponse } from "next/server";
import { signSession, SESSION_COOKIE, getSessionCookieOptions } from "../../../../lib/session";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let body: { email?: unknown };
  try {
    body = (await request.json()) as { email?: unknown };
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  const email = body.email;
  if (typeof email !== "string" || !email.trim()) {
    return NextResponse.json({ error: "email is required" }, { status: 400 });
  }

  const user = {
    userId: `dev|${email}`,
    email: email.trim(),
    name: email.trim().split("@")[0],
    orgId: "org_dev",
    orgName: "Dev Organization",
    role: "dealer",
  };
  const session = signSession(user);

  const response = NextResponse.json({ ok: true, user });
  response.cookies.set(SESSION_COOKIE, session, getSessionCookieOptions());
  return response;
}
