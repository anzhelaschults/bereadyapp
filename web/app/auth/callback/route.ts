import { NextRequest, NextResponse } from "next/server";
import { createSupabaseServerClient, supabaseConfigured } from "../../../lib/server/supabase";
import { errorResponse, HttpError } from "../../../lib/server/http";

export const dynamic = "force-dynamic";

/** OAuth/OTP callback intentionally accepts no caller-controlled redirect target. */
export async function GET(request: NextRequest) {
  let destination: URL;
  try {
    const configured = new URL(process.env.APP_URL ?? "");
    if (!/^https?:$/.test(configured.protocol) || configured.username || configured.password) throw new Error("invalid origin");
    destination = new URL("/workspace", configured.origin);
  } catch {
    return errorResponse(new HttpError(503, "AUTH_UNAVAILABLE", "Account sign-in is not configured."));
  }
  if (supabaseConfigured()) {
    const code = request.nextUrl.searchParams.get("code");
    if (code && code.length <= 4096) {
      try {
        const supabase = await createSupabaseServerClient();
        await supabase.auth.exchangeCodeForSession(code);
      } catch { /* Redirect remains fixed and reveals no provider failure. */ }
    }
  }
  const response = NextResponse.redirect(destination);
  response.headers.set("Cache-Control", "no-store");
  return response;
}
