import { NextRequest, NextResponse } from "next/server";
import { errorResponse, noStore, readJson, requireSameOrigin, HttpError } from "../../../lib/server/http";
import { createSupabaseServerClient, supabaseConfigured } from "../../../lib/server/supabase";

export const dynamic = "force-dynamic";

function appUrl(): string {
  const value = process.env.APP_URL;
  if (!value) throw new HttpError(503, "AUTH_UNAVAILABLE", "Account saving is not configured.");
  try { return new URL(value).origin; } catch { throw new HttpError(503, "AUTH_UNAVAILABLE", "Account saving is not configured."); }
}

export async function GET() {
  if (!supabaseConfigured()) return NextResponse.json({ configured: false, user: null }, { headers: noStore });
  try {
    const supabase = await createSupabaseServerClient();
    const { data: { user } } = await supabase.auth.getUser();
    return NextResponse.json({ configured: true, user: user ? { id: user.id, email: user.email ?? undefined } : null }, { headers: noStore });
  } catch { return NextResponse.json({ configured: true, user: null }, { headers: noStore }); }
}

export async function POST(request: NextRequest) {
  try {
    requireSameOrigin(request);
    if (!supabaseConfigured()) throw new HttpError(503, "AUTH_UNAVAILABLE", "Account saving is not configured.");
    const input = await readJson(request);
    const email = input && typeof input === "object" ? (input as Record<string, unknown>).email : null;
    if (typeof email !== "string" || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new HttpError(422, "VALIDATION_ERROR", "Enter a valid email address.");
    }
    const supabase = await createSupabaseServerClient();
    const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: `${appUrl()}/auth/callback` } });
    if (error) console.warn(JSON.stringify({ event: "otp_request_failed", reason: error.name }));
    // Avoid account enumeration and provider internals.
    return NextResponse.json({ message: "If this email can sign in, a link is on its way." }, { headers: noStore });
  } catch (error) { return errorResponse(error); }
}

export async function DELETE(request: NextRequest) {
  try {
    requireSameOrigin(request);
    const supabase = await createSupabaseServerClient();
    const { error } = await supabase.auth.signOut();
    if (error) throw new HttpError(503, "AUTH_UNAVAILABLE", "Sign-out could not be confirmed. Please try again.");
    return NextResponse.json({ ok: true }, { headers: noStore });
  } catch (error) { return errorResponse(error); }
}
