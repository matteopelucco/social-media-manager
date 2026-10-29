import { describe, expect, it } from "vitest";
import { securityHeaders } from "@/lib/security/headers";
import { generateNonce } from "@/lib/security/nonce";

const get = (h: Record<string, string>, name: string) =>
  Object.entries(h).find(([k]) => k.toLowerCase() === name.toLowerCase())?.[1];
const directive = (csp: string, name: string) =>
  csp
    .split(";")
    .map((s) => s.trim())
    .find((s) => s === name || s.startsWith(name + " ")) ?? "";

const prod = () => securityHeaders({ isDev: false, nonce: "abc123" });
const dev = () => securityHeaders({ isDev: true, nonce: "abc123" });
const csp = (h: Record<string, string>) => get(h, "Content-Security-Policy") ?? "";

describe("REQ-PROT-04 header di sicurezza", () => {
  it("Cache disattivata", () => {
    expect(get(prod(), "Cache-Control")).toBe("no-store");
  });
  it("Niente incorniciamento", () => {
    expect(get(prod(), "X-Frame-Options")).toBe("DENY");
    expect(csp(prod())).toContain("frame-ancestors 'none'");
  });
  it("CSP in produzione", () => {
    const c = csp(prod());
    expect(c).toContain("default-src 'self'");
    expect(c).toContain("script-src 'self' 'nonce-abc123' 'strict-dynamic'");
    expect(c).toContain("object-src 'none'");
    expect(c).toContain("base-uri 'self'");
    expect(c).toContain("form-action 'self'");
    expect(c).toContain("frame-ancestors 'none'");
    expect(c).not.toContain("'unsafe-eval'");
    expect(directive(c, "script-src")).not.toContain("'unsafe-inline'");
    expect(c).not.toContain("upgrade-insecure-requests");
  });
  it("CSP in sviluppo", () => {
    const d = csp(dev());
    expect(directive(d, "script-src")).toContain("'unsafe-eval'");
    expect(d).toContain("default-src 'self'");
    expect(d).toContain("'nonce-abc123'");
    expect(d).toContain("object-src 'none'");
    expect(d).toContain("base-uri 'self'");
    expect(d).toContain("form-action 'self'");
    expect(d).toContain("frame-ancestors 'none'");
    expect(d).not.toContain("upgrade-insecure-requests");
  });
  it("Nonce diverso a ogni richiesta", () => {
    const a = generateNonce();
    const b = generateNonce();
    expect(a).not.toBe(b);
    expect(a).toMatch(/^[A-Za-z0-9+/]+=*$/);
    expect(csp(securityHeaders({ isDev: false, nonce: a }))).toContain(`'nonce-${a}'`);
  });
  it("Nessun CORS aperto", () => {
    for (const h of [prod(), dev()]) {
      expect(Object.keys(h).some((k) => k.toLowerCase().startsWith("access-control-"))).toBe(false);
    }
  });
});
