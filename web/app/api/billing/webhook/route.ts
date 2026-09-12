import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { HttpError, errorResponse } from "../../../../lib/server/http";
import { readBoundedRawBody, recordBillingEvent } from "../../../../lib/server/billing-ledger";

export const dynamic = "force-dynamic";

function webhookConfigured(): boolean {
  return process.env.BILLING_ENABLED === "true" && Boolean(process.env.STRIPE_SECRET_KEY && process.env.STRIPE_WEBHOOK_SECRET && process.env.BILLING_DATABASE_URL);
}

export async function POST(request: NextRequest) {
  if (!webhookConfigured()) return NextResponse.json({ error: { code: "BILLING_DISABLED", message: "Billing is not enabled for this pilot." } }, { status: 503, headers: { "Cache-Control": "no-store" } });
  try {
    const signature = request.headers.get("stripe-signature");
    if (!signature || signature.length > 4096) throw new HttpError(400, "WEBHOOK_INVALID", "Invalid webhook.");
    const payload = await readBoundedRawBody(request);
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
    const event = stripe.webhooks.constructEvent(payload, signature, process.env.STRIPE_WEBHOOK_SECRET!);
    const inserted = await recordBillingEvent(event.id, event.type);
    console.info(JSON.stringify({ event: "stripe_webhook_recorded", stripe_event_id: event.id, type: event.type, duplicate: !inserted }));
    // A verified event is a ledger fact only; user entitlements are never inferred here.
    return NextResponse.json({ received: true }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    if (error instanceof HttpError && error.status === 503) return errorResponse(error);
    return NextResponse.json({ error: { code: "WEBHOOK_INVALID", message: "Invalid webhook." } }, { status: error instanceof HttpError ? error.status : 400, headers: { "Cache-Control": "no-store" } });
  }
}
