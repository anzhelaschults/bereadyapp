import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
vi.mock("server-only", () => ({}));
const mocks = vi.hoisted(() => ({ requireUser: vi.fn(), createTrustedSupabaseClient: vi.fn(), regeneratePlan: vi.fn(), saveCanonicalPlan: vi.fn(), loadOwnedPlan: vi.fn(), recomputeProgress: vi.fn() }));
vi.mock("../../lib/server/supabase", () => ({ requireUser: mocks.requireUser, createTrustedSupabaseClient: mocks.createTrustedSupabaseClient }));
vi.mock("../../lib/server/beready-api", () => ({ regeneratePlan: mocks.regeneratePlan, recomputeProgress: mocks.recomputeProgress }));
vi.mock("../../lib/server/saved-plans", () => ({ saveCanonicalPlan: mocks.saveCanonicalPlan, loadOwnedPlan: mocks.loadOwnedPlan }));
import { POST as savePlan } from "../../app/api/plans/route";
import { PATCH } from "../../app/api/plans/[id]/route";

const id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const sessionId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01";
const canonical = { version: 1, trail_id: "trail", fitness: 1, start_date: "2025-01-01", trip_date: "2025-01-08", sessions: [{ id: sessionId, week: 1, day: 1, date: "2025-01-01", kind: "base", label: "Walk", adapted: false }], notes: [], assessment: { status: "ready" } };

describe("saved plan routes", () => {
  beforeEach(() => { process.env.APP_URL = "https://app.test"; });
  afterEach(() => { vi.clearAllMocks(); delete process.env.APP_URL; });
  it("discards forged client assessment and persists only regenerated canonical plan", async () => {
    const trusted = {};
    mocks.requireUser.mockResolvedValue({ supabase: {}, user: { id: "11111111-1111-4111-8111-111111111111" } }); mocks.createTrustedSupabaseClient.mockReturnValue(trusted); mocks.regeneratePlan.mockResolvedValue(canonical); mocks.saveCanonicalPlan.mockResolvedValue(id);
    const request = new NextRequest("https://app.test/api/plans", { method: "POST", headers: { origin: "https://app.test", "content-type": "application/json" }, body: JSON.stringify({ plan: { ...canonical, assessment: { status: "ready", why: "FORGED" }, sessions: [{ id: "forged" }] } }) });
    expect((await savePlan(request)).status).toBe(201);
    expect(mocks.regeneratePlan).toHaveBeenCalledWith({ trail_id: "trail", fitness: 1, start_date: "2025-01-01", trip_date: "2025-01-08" });
    expect(mocks.saveCanonicalPlan).toHaveBeenCalledWith(trusted, "11111111-1111-4111-8111-111111111111", canonical);
  });
  it("rejects a cross-plan session before database mutation", async () => {
    mocks.requireUser.mockResolvedValue({ supabase: { from: vi.fn() } }); mocks.loadOwnedPlan.mockResolvedValue({ plan: canonical, logs: [] });
    const request = new NextRequest(`https://app.test/api/plans/${id}`, { method: "PATCH", headers: { origin: "https://app.test", "content-type": "application/json" }, body: JSON.stringify({ session_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", done: true }) });
    expect((await PATCH(request, { params: Promise.resolve({ id }) })).status).toBe(422);
  });
});
