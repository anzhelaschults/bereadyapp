import type { SupabaseClient } from "@supabase/supabase-js";
import type { Plan, SessionLog } from "../types";
import { HttpError } from "./http";
import { isUuid } from "./validation";

export async function loadOwnedPlan(supabase: SupabaseClient, id: string): Promise<{ plan: Plan; logs: SessionLog[] }> {
  if (!isUuid(id)) throw new HttpError(422, "VALIDATION_ERROR", "Invalid plan id.");
  const { data: record, error } = await supabase.from("prep_plans").select("plan").eq("id", id).maybeSingle();
  if (error) throw new HttpError(500, "STORAGE_ERROR", "Unable to load this plan.");
  if (!record) throw new HttpError(404, "NOT_FOUND", "Plan not found.");
  const { data: sessions, error: sessionError } = await supabase.from("plan_sessions").select("session").eq("plan_id", id).order("week").order("day");
  if (sessionError) throw new HttpError(500, "STORAGE_ERROR", "Unable to load this plan.");
  const { data: logs, error: logError } = await supabase.from("session_logs").select("session_id,done_at").eq("plan_id", id);
  if (logError) throw new HttpError(500, "STORAGE_ERROR", "Unable to load this plan.");
  const metadata = record.plan as Omit<Plan, "sessions">;
  if (!metadata || metadata.version !== 1 || !Array.isArray(sessions)) throw new HttpError(500, "STORAGE_ERROR", "Stored plan is invalid.");
  return { plan: { ...metadata, sessions: sessions.map((entry: { session: unknown }) => entry.session) as Plan["sessions"] }, logs: (logs ?? []) as SessionLog[] };
}

export async function saveCanonicalPlan(supabase: SupabaseClient, ownerId: string, plan: Plan): Promise<string> {
  const { data, error } = await supabase.rpc("save_prep_plan", { p_plan: plan, p_owner_id: ownerId });
  if (error || !isUuid(data)) {
    console.error(JSON.stringify({ event: "plan_save_failed", reason: error?.code ?? "invalid_result" }));
    throw new HttpError(500, "STORAGE_ERROR", "Unable to save this plan.");
  }
  return data;
}
