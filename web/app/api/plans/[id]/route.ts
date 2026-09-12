import { NextRequest, NextResponse } from "next/server";
import { errorResponse, noStore, readJson, requireSameOrigin, HttpError } from "../../../../lib/server/http";
import { recomputeProgress } from "../../../../lib/server/beready-api";
import { loadOwnedPlan } from "../../../../lib/server/saved-plans";
import { requireUser } from "../../../../lib/server/supabase";
import { isUuid, parseCompletion, utcToday } from "../../../../lib/server/validation";

export const dynamic = "force-dynamic";
type Context = { params: Promise<{ id: string }> };

async function detail(id: string) {
  const { supabase } = await requireUser();
  const { plan, logs } = await loadOwnedPlan(supabase, id);
  const computed = await recomputeProgress(plan, logs);
  return { id, plan: computed.plan, logs, progress: computed.progress };
}

export async function GET(_: NextRequest, context: Context) {
  try { return NextResponse.json(await detail((await context.params).id), { headers: noStore }); }
  catch (error) { return errorResponse(error); }
}

export async function PATCH(request: NextRequest, context: Context) {
  try {
    requireSameOrigin(request);
    const id = (await context.params).id;
    if (!isUuid(id)) throw new HttpError(422, "VALIDATION_ERROR", "Invalid plan id.");
    const mutation = parseCompletion(await readJson(request));
    if (!mutation) throw new HttpError(422, "VALIDATION_ERROR", "Invalid session completion.");
    const { supabase } = await requireUser();
    const { plan } = await loadOwnedPlan(supabase, id); // RLS verifies plan ownership before mutation.
    const session = plan.sessions.find((item) => item.id === mutation.session_id);
    if (!session) throw new HttpError(422, "VALIDATION_ERROR", "Session does not belong to this plan.");
    if (mutation.done && session.date > utcToday()) throw new HttpError(422, "VALIDATION_ERROR", "Future sessions cannot be completed.");
    if (mutation.done) {
      const { error } = await supabase.from("session_logs").upsert({ plan_id: id, session_id: mutation.session_id, done_at: utcToday() }, { onConflict: "plan_id,session_id" });
      if (error) throw new HttpError(500, "STORAGE_ERROR", "Unable to update session.");
    } else {
      const { error } = await supabase.from("session_logs").delete().eq("plan_id", id).eq("session_id", mutation.session_id);
      if (error) throw new HttpError(500, "STORAGE_ERROR", "Unable to update session.");
    }
    return NextResponse.json(await detail(id), { headers: noStore });
  } catch (error) { return errorResponse(error); }
}

export async function DELETE(request: NextRequest, context: Context) {
  try {
    requireSameOrigin(request);
    const { supabase } = await requireUser();
    const id = (await context.params).id;
    if (!isUuid(id)) throw new HttpError(422, "VALIDATION_ERROR", "Invalid plan id.");
    const { error } = await supabase.from("prep_plans").delete().eq("id", id);
    if (error) throw new HttpError(500, "STORAGE_ERROR", "Unable to delete plan.");
    return NextResponse.json({ ok: true }, { headers: noStore });
  } catch (error) { return errorResponse(error); }
}
