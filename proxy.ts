import { NextResponse, type NextRequest } from "next/server";
import { securityHeaders } from "@/lib/security/headers";
import { generateNonce } from "@/lib/security/nonce";
import { isRequestAllowed } from "@/lib/security/request-guard";

export function proxy(request: NextRequest) {
  const nonce = generateNonce();
  const headers = securityHeaders({ isDev: process.env.NODE_ENV === "development", nonce });

  const check = isRequestAllowed({
    host: request.headers.get("host"),
    origin: request.headers.get("origin"),
    method: request.method,
  });
  if (!check.allowed) {
    return Response.json({ error: "Richiesta non consentita." }, { status: 403, headers });
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", headers["Content-Security-Policy"] ?? "");

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  for (const [name, value] of Object.entries(headers)) response.headers.set(name, value);
  return response;
}
