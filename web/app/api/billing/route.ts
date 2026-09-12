import { NextRequest, NextResponse } from "next/server";
import { errorResponse, noStore, requireSameOrigin, HttpError } from "../../../lib/server/http";
import { requireUser } from "../../../lib/server/supabase";

export const dynamic = "force-dynamic";

function billingConfig() {
  if (process.env.BILLING_ENABLED !== "true") throw new HttpError(503, "BILLING_DISABLED", "Billing is not enabled for this pilot.");
  const key = process.env.STRIPE_SECRET_KEY;
  const price = process.env.STRIPE_PRICE_ID;
  const appUrl = process.env.APP_URL;
  if (!key || !price || !appUrl || !process.env.STRIPE_WEBHOOK_SECRET || !process.env.BILLING_DATABASE_URL) throw new HttpError(503, "BILLING_UNAVAILABLE", "Billing is not configured.");
  let origin: string;
  try { origin = new URL(appUrl).origin; } catch { throw new HttpError(503, "BILLING_UNAVAILABLE", "Billing is not configured."); }
  return { key, price, origin };
}

export async function POST(request: NextRequest) {
  try {
    requireSameOrigin(request);
    const { user } = await requireUser();
    const { key, price, origin } = billingConfig();
    const { default: Stripe } = await import("stripe");
    const stripe = new Stripe(key);
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      line_items: [{ price, quantity: 1 }], // Price is exclusively selected by the server.
      client_reference_id: user.id,
      metadata: { supabase_user_id: user.id },
      success_url: `${origin}/workspace?checkout=success`,
      cancel_url: `${origin}/workspace?checkout=cancelled`,
    });
    if (!session.url) throw new HttpError(503, "BILLING_UNAVAILABLE", "Checkout is unavailable.");
    return NextResponse.json({ url: session.url }, { headers: noStore });
  } catch (error) { return errorResponse(error); }
}
