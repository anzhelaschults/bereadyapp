import { describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { sessionCookieOptions } from "../../lib/server/supabase";

describe("Supabase session cookies", () => {
  it("uses non-JavaScript, same-site cookies and requires HTTPS for an HTTPS app", () => {
    expect(sessionCookieOptions("https://app.example.test")).toMatchObject({ httpOnly: true, secure: true, sameSite: "lax", path: "/" });
  });

  it("permits insecure cookies only for an explicit local HTTP app", () => {
    expect(sessionCookieOptions("http://localhost:3000").secure).toBe(false);
    expect(sessionCookieOptions("http://app.example.test").secure).toBe(true);
  });
});
