import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
vi.mock("../../lib/server/supabase", () => ({ supabaseConfigured: () => false }));
import { GET } from "../../app/auth/callback/route";

afterEach(() => vi.unstubAllEnvs());
describe("fixed-origin sign-in callback", () => {
  it("ignores a hostile request origin and redirect query", async () => {
    vi.stubEnv("APP_URL", "https://app.example.test");
    const response = await GET(new NextRequest("https://attacker.example/auth/callback?next=https://attacker.example"));
    expect(response.headers.get("location")).toBe("https://app.example.test/workspace");
    expect(response.headers.get("cache-control")).toBe("no-store");
  });
  it.each(["", "not-a-url", "javascript:alert(1)", "https://user:secret@app.example.test"])("fails closed for invalid configured URL %s", async (url) => {
    vi.stubEnv("APP_URL", url);
    const response = await GET(new NextRequest("https://attacker.example/auth/callback"));
    expect(response.status).toBe(503);
    expect(response.headers.get("location")).toBeNull();
  });
});
