/**
 * API ATTESA (da implementare in lib/security/, specifica specs/03 - protezione-app-locale.md)
 *
 * @/lib/security/request-guard
 *   isHostAllowed(host: string | null | undefined): boolean
 *   isRequestAllowed(input: { host?: string | null; origin?: string | null; method: string })
 *     : { allowed: true } | { allowed: false; reason: string }
 *     (metodo normalizzato in maiuscolo; GET/HEAD sicuri, tutti gli altri non sicuri)
 *
 * @/lib/security/headers
 *   securityHeaders(input: { isDev: boolean; nonce: string }): Record<string, string>
 *     chiavi con la grafia canonica: "Cache-Control", "Content-Security-Policy", "X-Frame-Options"
 *
 * @/lib/security/nonce
 *   generateNonce(): string   (base64 non vuoto, diverso a ogni chiamata)
 */
import { describe, expect, it } from "vitest";
import { isHostAllowed, isRequestAllowed } from "@/lib/security/request-guard";

describe("REQ-PROT-02 Host", () => {
  it("Host locale con nome localhost", () => {
    expect(isRequestAllowed({ host: "localhost:3000", method: "GET" }).allowed).toBe(true);
    expect(isHostAllowed("localhost:3000")).toBe(true);
  });
  it("Host locale con IPv4", () => {
    expect(isRequestAllowed({ host: "127.0.0.1:3000", method: "GET" }).allowed).toBe(true);
  });
  it("Host locale con IPv6", () => {
    expect(isRequestAllowed({ host: "[::1]:3000", method: "GET" }).allowed).toBe(true);
  });
  it("Host con maiuscole", () => {
    expect(isRequestAllowed({ host: "LocalHost:3000", method: "GET" }).allowed).toBe(true);
  });
  it("Host esterno", () => {
    expect(isRequestAllowed({ host: "evil.example", method: "GET" }).allowed).toBe(false);
  });
  it("DNS rebinding con prefisso locale", () => {
    expect(isRequestAllowed({ host: "127.0.0.1.evil.example:3000", method: "GET" }).allowed).toBe(false);
  });
  it("DNS rebinding con suffisso locale", () => {
    expect(isRequestAllowed({ host: "localhost.evil.example:3000", method: "GET" }).allowed).toBe(false);
  });
  it("IP di rete locale", () => {
    expect(isRequestAllowed({ host: "192.168.1.20:3000", method: "GET" }).allowed).toBe(false);
  });
  it("Host assente", () => {
    expect(isRequestAllowed({ method: "GET" }).allowed).toBe(false);
    expect(isRequestAllowed({ host: null, method: "GET" }).allowed).toBe(false);
    expect(isRequestAllowed({ host: "", method: "GET" }).allowed).toBe(false);
    expect(isHostAllowed(undefined)).toBe(false);
  });
  it("Porta diversa", () => {
    expect(isRequestAllowed({ host: "localhost:4000", method: "GET" }).allowed).toBe(false);
  });
  it("Host locale senza porta", () => {
    expect(isRequestAllowed({ host: "localhost", method: "GET" }).allowed).toBe(false);
  });
  it("Casi limite: Host con spazi o piu valori separati da virgola", () => {
    expect(isHostAllowed("localhost:3000 ")).toBe(false);
    expect(isHostAllowed("localhost:3000, evil.example")).toBe(false);
    expect(isHostAllowed("localhost:3000,127.0.0.1:3000")).toBe(false);
  });
});
