import { NextRequest, NextResponse } from "next/server";
import type { Plan } from "../../../lib/types";
import { errorResponse, noStore, readJson, requireSameOrigin, HttpError } from "../../../lib/server/http";
import { createTrustedSupabaseClient, requireUser } from "../../../lib/server/supabase";
import { regeneratePlan } from "../../../lib/server/beready-api";
import { isIsoDate, validFitness } from "../../../lib/server/validation";
import { saveCanonicalPlan } from "../../../lib/server/saved-plans";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const { supabase } = await requireUser();
    const { data, error } = await supabase.from("prep_plans").select("id,trail_id,fitness,start_date,trip_date,created_at").order("created_at", { ascending: false });
    if (error) throw new HttpError(500, "STORAGE_ERROR", "Unable to load plans.");
    return NextResponse.json({ plans: data ?? [] }, { headers: noStore });
  } catch (error) { return errorResponse(error); }
}

export async function POST(request: NextRequest) {
  try {
    requireSameOrigin(request);
    const { user } = await requireUser();
    const body = await readJson(request);
    const supplied = body && typeof body === "object" ? (body as { plan?: Partial<Plan> }).plan : null;
    if (!supplied || typeof supplied.trail_id !== "string" || supplied.trail_id.length < 1 || supplied.trail_id.length > 100 || !/^[a-z0-9-]+$/.test(supplied.trail_id) || !validFitness(supplied.fitness) || !isIsoDate(supplied.start_date) || !isIsoDate(supplied.trip_date)) {
      throw new HttpError(422, "VALIDATION_ERROR", "Invalid plan input.");
    }
    // The only persisted content is regenerated on the server; client sessions/assessment are discarded.
    const plan = await regeneratePlan({ trail_id: supplied.trail_id, fitness: supplied.fitness, start_date: supplied.start_date, trip_date: supplied.trip_date });
    const id = await saveCanonicalPlan(createTrustedSupabaseClient(), user.id, plan);
    return NextResponse.json({ id }, { status: 201, headers: noStore });
  } catch (error) { return errorResponse(error); }
}
