import { describe, expect, it } from "vitest";
import { isRequestAllowed } from "@/lib/security/request-guard";

const HOST = "127.0.0.1:3000";

describe("REQ-PROT-03 Origin e metodi", () => {
  it("Metodo sicuro senza Origin", () => {
    expect(isRequestAllowed({ host: HOST, method: "GET" }).allowed).toBe(true);
    expect(isRequestAllowed({ host: HOST, method: "HEAD" }).allowed).toBe(true);
  });
  it("Metodo sicuro con Origin esterno", () => {
    expect(isRequestAllowed({ host: HOST, origin: "https://evil.example", method: "GET" }).allowed).toBe(true);
  });
  it("Metodo non sicuro con Origin uguale", () => {
    expect(isRequestAllowed({ host: HOST, origin: "http://127.0.0.1:3000", method: "POST" }).allowed).toBe(true);
  });
  it("Metodo non sicuro con Origin diverso", () => {
    for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
      expect(isRequestAllowed({ host: HOST, origin: "https://evil.example", method }).allowed).toBe(false);
    }
  });
  it("Origin locale ma di un altro host", () => {
    expect(isRequestAllowed({ host: HOST, origin: "http://localhost:3000", method: "POST" }).allowed).toBe(false);
  });
  it("Metodo non sicuro senza Origin", () => {
    expect(isRequestAllowed({ host: HOST, method: "POST" }).allowed).toBe(false);
    expect(isRequestAllowed({ host: HOST, origin: null, method: "POST" }).allowed).toBe(false);
  });
  it("Metodo non sicuro con Origin null", () => {
    expect(isRequestAllowed({ host: HOST, origin: "null", method: "POST" }).allowed).toBe(false);
  });
  it("Metodo non sicuro con Host non valido", () => {
    expect(isRequestAllowed({ host: "evil.example", origin: "http://evil.example", method: "POST" }).allowed).toBe(false);
  });
  it("OPTIONS e metodo in minuscolo", () => {
    expect(isRequestAllowed({ host: HOST, method: "OPTIONS" }).allowed).toBe(false);
    expect(isRequestAllowed({ host: HOST, origin: "https://evil.example", method: "OPTIONS" }).allowed).toBe(false);
    expect(isRequestAllowed({ host: HOST, method: "post" }).allowed).toBe(false);
    expect(isRequestAllowed({ host: HOST, origin: "http://127.0.0.1:3000", method: "post" }).allowed).toBe(true);
    expect(isRequestAllowed({ host: HOST, method: "get" }).allowed).toBe(true);
  });
  it("Casi limite: Origin https con stesso host e porta", () => {
    expect(isRequestAllowed({ host: HOST, origin: "https://127.0.0.1:3000", method: "POST" }).allowed).toBe(false);
  });
  it("Il rifiuto riporta un motivo", () => {
    const r = isRequestAllowed({ host: "evil.example", method: "GET" });
    expect(r.allowed).toBe(false);
    expect("reason" in r && typeof r.reason === "string" && r.reason.length > 0).toBe(true);
  });
});
