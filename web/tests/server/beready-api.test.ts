import { afterEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { regeneratePlan } from "../../lib/server/beready-api";

const responsePlan = { version: 1, trail_id: "test-trail", fitness: 1, start_date: "2025-01-01", trip_date: "2025-01-15", sessions: [], notes: [] };

describe("regeneratePlan", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends whole available weeks required by Python while retaining dates as authority", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(responsePlan), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await regeneratePlan({ trail_id: "test-trail", fitness: 1, start_date: "2025-01-01", trip_date: "2025-01-15" });
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toMatchObject({ weeks: 2, start_date: "2025-01-01", trip_date: "2025-01-15" });
  });

  it("rejects dates outside Python's accepted seven to 364 day interval before calling upstream", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    await expect(regeneratePlan({ trail_id: "test-trail", fitness: 1, start_date: "2025-01-01", trip_date: "2025-01-07" })).rejects.toMatchObject({ status: 422 });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
