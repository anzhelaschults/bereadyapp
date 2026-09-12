import { NextRequest, NextResponse } from "next/server";
import { errorResponse, noStore, readJson, requireSameOrigin, HttpError } from "../../../lib/server/http";
import { requireUser } from "../../../lib/server/supabase";

export const dynamic = "force-dynamic";
const billingEnabled = process.env.BILLING_ENABLED === "true";

export async function GET() {
  try {
    const { supabase } = await requireUser();
    const { data, error } = await supabase.from("companies").select("id,name").maybeSingle();
    if (error) throw new HttpError(500, "STORAGE_ERROR", "Unable to load workspace.");
    return NextResponse.json({ company: data ?? null, billing_enabled: billingEnabled }, { headers: noStore });
  } catch (error) { return errorResponse(error); }
}

export async function POST(request: NextRequest) {
  try {
    requireSameOrigin(request);
    const { supabase } = await requireUser();
    const body = await readJson(request);
    const name = body && typeof body === "object" ? (body as Record<string, unknown>).name : null;
    if (typeof name !== "string" || name.trim().length < 1 || name.trim().length > 100) throw new HttpError(422, "VALIDATION_ERROR", "Workspace name must be 1 to 100 characters.");
    const { data, error } = await supabase.from("companies").insert({ name: name.trim() }).select("id,name").single();
    if (error) {
      if (error.code === "23505") throw new HttpError(409, "CONFLICT", "You already have a workspace.");
      throw new HttpError(500, "STORAGE_ERROR", "Unable to create workspace.");
    }
    return NextResponse.json({ company: data }, { status: 201, headers: noStore });
  } catch (error) { return errorResponse(error); }
}
