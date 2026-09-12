import "server-only";
import type { Plan, Progress, SessionLog } from "../types";
import { HttpError } from "./http";
import { isIsoDate } from "./validation";

const API_URL = process.env.BEREADY_API_URL ?? "http://localhost:8000";
const TIMEOUT_MS = 10_000;

function endpoint(path: "/plan" | "/progress"): URL {
  let base: URL;
  try { base = new URL(API_URL); } catch { throw new HttpError(503, "DEPENDENCY_UNAVAILABLE", "Planning service is unavailable."); }
  if (!/^https?:$/.test(base.protocol)) throw new HttpError(503, "DEPENDENCY_UNAVAILABLE", "Planning service is unavailable.");
  return new URL(path, base);
}

async function post<T>(path: "/plan" | "/progress", payload: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(endpoint(path), {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify(payload), signal: AbortSignal.timeout(TIMEOUT_MS), cache: "no-store",
    });
  } catch (cause) {
    console.warn(JSON.stringify({ event: "planning_upstream_failed", path, reason: cause instanceof Error ? cause.name : "unknown" }));
    throw new HttpError(503, "DEPENDENCY_UNAVAILABLE", "Planning service is unavailable. Try again shortly.");
  }
  let value: unknown;
  try { value = await response.json(); } catch { throw new HttpError(503, "DEPENDENCY_UNAVAILABLE", "Planning service returned an invalid response."); }
  if (!response.ok || !value || typeof value !== "object") {
    throw new HttpError(response.status === 422 ? 422 : 503, response.status === 422 ? "VALIDATION_ERROR" : "DEPENDENCY_UNAVAILABLE", response.status === 422 ? "Invalid plan input." : "Planning service is unavailable.");
  }
  return value as T;
}

function assertPlan(value: unknown): asserts value is Plan {
  const plan = value as Partial<Plan>;
  if (!plan || plan.version !== 1 || typeof plan.trail_id !== "string" || !Array.isArray(plan.sessions) || !Array.isArray(plan.notes)) {
    throw new HttpError(503, "DEPENDENCY_UNAVAILABLE", "Planning service returned an invalid plan.");
  }
}

export async function regeneratePlan(input: Pick<Plan, "trail_id" | "fitness" | "start_date" | "trip_date">): Promise<Plan> {
  if (!isIsoDate(input.start_date) || !isIsoDate(input.trip_date)) throw new HttpError(422, "VALIDATION_ERROR", "Invalid plan dates.");
  const start = Date.parse(`${input.start_date}T00:00:00.000Z`);
  const trip = Date.parse(`${input.trip_date}T00:00:00.000Z`);
  const days = (trip - start) / 86_400_000;
  const weeks = Math.floor(days / 7);
  if (!Number.isInteger(days) || days < 7 || days > 364 || weeks < 1 || weeks > 52) {
    throw new HttpError(422, "VALIDATION_ERROR", "Plan dates must be 7 to 364 days apart.");
  }
  // Python requires weeks as an input but recomputes available weeks from these dates.
  const plan = await post<Plan>("/plan", { ...input, weeks });
  assertPlan(plan);
  return plan;
}

export async function recomputeProgress(plan: Plan, logs: SessionLog[]): Promise<{ plan: Plan; progress: Progress }> {
  const result = await post<{ plan: Plan; progress: Progress }>("/progress", { plan, logs });
  assertPlan(result?.plan);
  if (!result.progress || typeof result.progress.score !== "number") throw new HttpError(503, "DEPENDENCY_UNAVAILABLE", "Planning service returned invalid progress.");
  return result;
}
