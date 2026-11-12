import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import {
  getSessionCookieOptions,
  SESSION_COOKIE,
  signSession,
  verifySession,
  type Session,
} from "../../../../lib/session";

export const dynamic = "force-dynamic";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function refreshApiSession(session: Session): Promise<Session | null> {
  if (
    process.env.NODE_ENV !== "development" ||
    (process.env.CHRONOARB_AUTH_MODE ?? "dev") !== "dev"
  ) {
    return null;
  }

  const apiBaseUrl = (
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
  ).replace(/\/+$/, "");
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1/identity/dev-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: session.email }),
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
  } catch (error) {
    if (error instanceof Error) {
      return null;
    }
    throw error;
  }
  if (!response.ok) {
    return null;
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    return null;
  }
  if (!isRecord(payload) || !isRecord(payload.data)) {
    return null;
  }
  const data = payload.data;
  if (
    typeof data.access_token !== "string" ||
    typeof data.user_id !== "string" ||
    typeof data.email !== "string" ||
    typeof data.organization_id !== "string" ||
    typeof data.organization_name !== "string" ||
    typeof data.role !== "string" ||
    (data.display_name !== null && typeof data.display_name !== "string")
  ) {
    return null;
  }

  return {
    userId: data.user_id,
    email: data.email,
    name: data.display_name,
    orgId: data.organization_id,
    orgName: data.organization_name,
    role: data.role,
    apiToken: data.access_token,
  };
}

export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "no session" }, { status: 401 });
  }

  const session = verifySession(token);
  if (!session) {
    return NextResponse.json({ error: "invalid session" }, { status: 401 });
  }

  const refreshRequested = request.nextUrl.searchParams.get("refresh") === "1";
  const refreshedSession = refreshRequested
    ? await refreshApiSession(session)
    : session;
  if (!refreshedSession) {
    return NextResponse.json(
      { error: "Unable to refresh the development API session." },
      { status: 503 },
    );
  }

  const response = NextResponse.json({ ok: true, user: refreshedSession });
  if (refreshedSession !== session) {
    response.cookies.set(
      SESSION_COOKIE,
      signSession(refreshedSession),
      getSessionCookieOptions(),
    );
  }
  return response;
}
