import { afterEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
const mocks = vi.hoisted(() => ({ createSupabaseServerClient: vi.fn(), supabaseConfigured: vi.fn() }));
vi.mock("../../lib/server/supabase", () => mocks);
import { GET, DELETE } from "../../app/api/auth/route";
import { NextRequest } from "next/server";

describe("auth status route", () => {
  afterEach(() => { vi.clearAllMocks(); vi.unstubAllEnvs(); });
  it("honestly reports an unconfigured provider", async () => {
    mocks.supabaseConfigured.mockReturnValue(false);
    expect(await (await GET()).json()).toEqual({ configured: false, user: null });
  });
  it("does not acknowledge a failed sign-out", async () => {
    vi.stubEnv("APP_URL", "https://app.example.test");
    mocks.createSupabaseServerClient.mockResolvedValue({ auth: { signOut: vi.fn().mockResolvedValue({ error: new Error("provider secret") }) } });
    const result = await DELETE(new NextRequest("https://app.example.test/api/auth", { method: "DELETE", headers: { origin: "https://app.example.test" } }));
    expect(result.status).toBe(503);
    expect(await result.text()).not.toContain("provider secret");
  });
  it("does not trust a failed provider session as a user", async () => {
    mocks.supabaseConfigured.mockReturnValue(true); mocks.createSupabaseServerClient.mockResolvedValue({ auth: { getUser: vi.fn().mockResolvedValue({ data: { user: null }, error: new Error("bad") }) } });
    expect(await (await GET()).json()).toEqual({ configured: true, user: null });
  });
});
