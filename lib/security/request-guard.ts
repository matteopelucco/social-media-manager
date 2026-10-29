const ALLOWED_HOSTS = new Set(["localhost:3000", "127.0.0.1:3000", "[::1]:3000"]);
const SAFE_METHODS = new Set(["GET", "HEAD"]);

export type RequestCheck = { allowed: true } | { allowed: false; reason: string };

/** Confronto sul nome intero (con porta), senza distinguere maiuscole/minuscole. */
export function isHostAllowed(host: string | null | undefined): boolean {
  if (!host) return false;
  return ALLOWED_HOSTS.has(host.toLowerCase());
}

export function isRequestAllowed(input: {
  host?: string | null;
  origin?: string | null;
  method: string;
}): RequestCheck {
  if (!isHostAllowed(input.host)) {
    return { allowed: false, reason: "host-not-allowed" };
  }
  const method = input.method.toUpperCase();
  if (SAFE_METHODS.has(method)) return { allowed: true };
  if (!input.origin) return { allowed: false, reason: "origin-missing" };
  const expected = `http://${(input.host as string).toLowerCase()}`;
  if (input.origin.toLowerCase() !== expected) {
    return { allowed: false, reason: "origin-mismatch" };
  }
  return { allowed: true };
}
