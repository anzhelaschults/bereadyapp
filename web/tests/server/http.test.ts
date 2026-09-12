import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { errorResponse, HttpError, readJson, requireSameOrigin } from "../../lib/server/http";

describe("server HTTP boundary", () => {
  beforeEach(() => { process.env.APP_URL = "https://app.example.test"; });
  afterEach(() => { delete process.env.APP_URL; });
  it("rejects cross-origin cookie mutations", () => {
    const request = new NextRequest("https://app.example.test/api/plans", { method: "POST", headers: { origin: "https://evil.example.test" } });
    try {
      requireSameOrigin(request);
      expect.unreachable("cross-origin request was accepted");
    } catch (error) {
      expect(error).toMatchObject({ status: 403, code: "FORBIDDEN" } satisfies Partial<HttpError>);
    }
  });

  it("accepts the exact request origin", () => {
    const request = new NextRequest("https://app.example.test/api/plans", { method: "POST", headers: { origin: "https://app.example.test" } });
    expect(() => requireSameOrigin(request)).not.toThrow();
  });

  it("enforces the JSON body size cap before parsing", async () => {
    const request = new Request("https://app.example.test/api/plans", { method: "POST", headers: { "content-type": "application/json", "content-length": "65537" }, body: "{}" });
    await expect(readJson(request)).rejects.toMatchObject({ status: 413, code: "PAYLOAD_TOO_LARGE" });
  });

  it("requires JSON content types and marks errors no-store", async () => {
    await expect(readJson(new Request("https://app.example.test", { method: "POST", headers: { "content-type": "text/plain" }, body: "{}" }))).rejects.toMatchObject({ status: 415 });
    expect(errorResponse(new Error("token=should-not-leak")).headers.get("Cache-Control")).toBe("no-store");
  });
});
