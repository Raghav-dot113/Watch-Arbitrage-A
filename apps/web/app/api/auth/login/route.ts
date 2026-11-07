import { NextResponse } from "next/server";
import { signSession, SESSION_COOKIE, getSessionCookieOptions } from "../../../../lib/session";

export const dynamic = "force-dynamic";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export async function POST(request: Request) {
  if (
    process.env.NODE_ENV !== "development" ||
    (process.env.CHRONOARB_AUTH_MODE ?? "dev") !== "dev"
  ) {
    return NextResponse.json({ error: "Development login is unavailable" }, { status: 404 });
  }

  let body: { email?: unknown };
  try {
    body = (await request.json()) as { email?: unknown };
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  const email = typeof body.email === "string" ? body.email.trim() : "";
  if (!email) {
    return NextResponse.json({ error: "email is required" }, { status: 400 });
  }

  const apiBaseUrl = (
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
  ).replace(/\/+$/, "");
  let upstream: Response;
  try {
    upstream = await fetch(`${apiBaseUrl}/api/v1/identity/dev-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
  } catch {
    return NextResponse.json(
      { error: "Development API is unavailable; start the API and try again." },
      { status: 503 },
    );
  }

  if (!upstream.ok) {
    if (upstream.status === 401) {
      return NextResponse.json(
        { error: "No local demo account matches that email." },
        { status: 401 },
      );
    }
    return NextResponse.json(
      { error: "Development API could not authenticate this account." },
      { status: upstream.status >= 400 && upstream.status < 500 ? upstream.status : 503 },
    );
  }

  let upstreamBody: unknown;
  try {
    upstreamBody = await upstream.json();
  } catch {
    return NextResponse.json(
      { error: "Development API returned an invalid authentication response." },
      { status: 503 },
    );
  }
  const tokenData =
    isRecord(upstreamBody) && isRecord(upstreamBody.data)
      ? upstreamBody.data
      : null;
  if (
    !tokenData ||
    typeof tokenData.access_token !== "string" ||
    typeof tokenData.user_id !== "string" ||
    typeof tokenData.email !== "string" ||
    typeof tokenData.organization_id !== "string" ||
    typeof tokenData.organization_name !== "string" ||
    typeof tokenData.role !== "string" ||
    (tokenData.display_name !== null && typeof tokenData.display_name !== "string")
  ) {
    return NextResponse.json(
      { error: "Development API returned an invalid authentication response." },
      { status: 503 },
    );
  }

  const user = {
    userId: tokenData.user_id,
    email: tokenData.email,
    name: tokenData.display_name,
    orgId: tokenData.organization_id,
    orgName: tokenData.organization_name,
    role: tokenData.role,
    apiToken: tokenData.access_token,
  };
  const session = signSession(user);

  const response = NextResponse.json({ ok: true, user });
  response.cookies.set(SESSION_COOKIE, session, getSessionCookieOptions());
  return response;
}
