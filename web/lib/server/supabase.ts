import "server-only";
import { createServerClient } from "@supabase/ssr";
import { createClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { HttpError } from "./http";

function supabaseEnvironment(): { url: string; publishableKey: string } | null {
  // Prefer server-only names; NEXT_PUBLIC aliases support Supabase's legacy setup.
  const url = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.SUPABASE_PUBLISHABLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  return url && publishableKey ? { url, publishableKey } : null;
}

export function sessionCookieOptions(appUrl = process.env.APP_URL): { httpOnly: true; secure: boolean; sameSite: "lax"; path: "/" } {
  let localHttp = false;
  try {
    const url = new URL(appUrl ?? "http://localhost:3000");
    localHttp = url.protocol === "http:" && (url.hostname === "localhost" || url.hostname === "127.0.0.1" || url.hostname === "::1");
  } catch { /* An invalid APP_URL is not a reason to weaken cookies. */ }
  return { httpOnly: true, secure: process.env.NODE_ENV === "production" || !localHttp, sameSite: "lax", path: "/" };
}

export function supabaseConfigured(): boolean {
  return supabaseEnvironment() !== null;
}

export function createTrustedSupabaseClient() {
  const config = supabaseEnvironment();
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!config || !serviceRoleKey) throw new HttpError(503, "AUTH_UNAVAILABLE", "Account saving is not configured.");
  return createClient(config.url, serviceRoleKey, { auth: { autoRefreshToken: false, persistSession: false, detectSessionInUrl: false } });
}

export async function createSupabaseServerClient() {
  const config = supabaseEnvironment();
  if (!config) throw new HttpError(503, "AUTH_UNAVAILABLE", "Account saving is not configured.");
  const cookieStore = await cookies();
  return createServerClient(config.url, config.publishableKey, {
    cookies: {
      getAll: () => cookieStore.getAll(),
      setAll: (entries) => {
        const required = sessionCookieOptions();
        entries.forEach(({ name, value, options }) => cookieStore.set(name, value, { ...options, ...required }));
      },
    },
  });
}

export async function requireUser() {
  const supabase = await createSupabaseServerClient();
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) throw new HttpError(401, "UNAUTHENTICATED", "Sign in to save a plan.");
  return { supabase, user };
}
