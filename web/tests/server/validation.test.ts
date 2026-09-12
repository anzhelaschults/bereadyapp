import { describe, expect, it } from "vitest";
import { isIsoDate, isUuid, parseCompletion } from "../../lib/server/validation";

describe("server validation", () => {
  it("accepts only UUIDs and boolean completion values", () => {
    expect(parseCompletion({ session_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8", done: true })).toEqual({
      session_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8", done: true,
    });
    expect(parseCompletion({ session_id: "not-a-uuid", done: true })).toBeNull();
    expect(parseCompletion({ session_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8", done: "true" })).toBeNull();
  });

  it("rejects malformed UUIDs and calendar dates", () => {
    expect(isUuid("6ba7b810-9dad-11d1-80b4-00c04fd430c8")).toBe(true);
    expect(isUuid("6ba7b810-9dad-11d1-80b4-00c04fd430c8' OR true--")).toBe(false);
    expect(isIsoDate("2026-02-29")).toBe(false);
    expect(isIsoDate("2024-02-29")).toBe(true);
  });
});
