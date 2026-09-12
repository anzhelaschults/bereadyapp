import { afterEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
const mocks = vi.hoisted(() => ({ constructEvent: vi.fn(), recordBillingEvent: vi.fn(), readBoundedRawBody: vi.fn().mockResolvedValue("{}") }));
vi.mock("stripe", () => ({ default: class { webhooks = { constructEvent: mocks.constructEvent }; } }));
vi.mock("../../lib/server/billing-ledger", () => ({ readBoundedRawBody: mocks.readBoundedRawBody, recordBillingEvent: mocks.recordBillingEvent }));
import { POST } from "../../app/api/billing/webhook/route";
import { HttpError } from "../../lib/server/http";

const env = { BILLING_ENABLED: "true", STRIPE_SECRET_KEY: "sk_test", STRIPE_WEBHOOK_SECRET: "whsec_test", BILLING_DATABASE_URL: "postgres://private" };
describe("billing webhook", () => {
  afterEach(() => { vi.clearAllMocks(); Object.assign(process.env, env); });
  it("returns 503 without a configured private ledger", async () => {
    delete process.env.BILLING_DATABASE_URL;
    expect((await POST(new Request("https://app.test", { method: "POST" }) as never)).status).toBe(503);
  });
  it("records a verified event once and accepts duplicate delivery", async () => {
    Object.assign(process.env, env); mocks.constructEvent.mockReturnValue({ id: "evt_1", type: "checkout.session.completed" }); mocks.recordBillingEvent.mockResolvedValueOnce(true).mockResolvedValueOnce(false);
    const request = () => new Request("https://app.test/api/billing/webhook", { method: "POST", headers: { "stripe-signature": "sig" }, body: "{}" });
    expect((await POST(request() as never)).status).toBe(200);
    expect((await POST(request() as never)).status).toBe(200);
    expect(mocks.recordBillingEvent).toHaveBeenCalledWith("evt_1", "checkout.session.completed");
  });
  it("does not insert an invalid signature", async () => {
    Object.assign(process.env, env); mocks.constructEvent.mockImplementation(() => { throw new Error("bad signature"); });
    expect((await POST(new Request("https://app.test", { method: "POST", headers: { "stripe-signature": "sig" }, body: "{}" }) as never)).status).toBe(400);
    expect(mocks.recordBillingEvent).not.toHaveBeenCalled();
  });
  it("returns non-2xx when the private ledger fails", async () => {
    Object.assign(process.env, env); mocks.constructEvent.mockReturnValue({ id: "evt_1", type: "x" }); mocks.recordBillingEvent.mockRejectedValue(new HttpError(503, "BILLING_UNAVAILABLE", "Billing is temporarily unavailable."));
    expect((await POST(new Request("https://app.test", { method: "POST", headers: { "stripe-signature": "sig" }, body: "{}" }) as never)).status).toBe(503);
  });
});
