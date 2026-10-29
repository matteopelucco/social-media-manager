import { describe, expect, it } from "vitest";
import { cn } from "@/lib/utils";

describe("cn", () => {
  it("unisce le classi ignorando i valori falsi", () => {
    expect(cn("a", false, undefined, null, "b")).toBe("a b");
  });

  it("accetta condizioni in forma di oggetto", () => {
    expect(cn("base", { attivo: true, spento: false })).toBe("base attivo");
  });

  it("risolve i conflitti di Tailwind: vince l'ultima classe", () => {
    expect(cn("p-2 text-red-500", "p-4")).toBe("text-red-500 p-4");
  });
});
