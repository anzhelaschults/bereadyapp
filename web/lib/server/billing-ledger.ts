import "server-only";
import postgres from "postgres";
import { HttpError } from "./http";

export async function recordBillingEvent(eventId: string, eventType: string): Promise<boolean> {
  const url = process.env.BILLING_DATABASE_URL;
  if (!url) throw new HttpError(503, "BILLING_UNAVAILABLE", "Billing is not configured.");
  const sql = postgres(url, { max: 1, connect_timeout: 5, idle_timeout: 5, prepare: false });
  try {
    const rows = await sql<{ stripe_event_id: string }[]>`
      insert into private.billing_webhook_events (stripe_event_id, event_type)
      values (${eventId}, ${eventType})
      on conflict (stripe_event_id) do nothing
      returning stripe_event_id`;
    return rows.length === 1;
  } catch (cause) {
    console.error(JSON.stringify({ event: "billing_ledger_write_failed", error_type: cause instanceof Error ? cause.name : typeof cause }));
    throw new HttpError(503, "BILLING_UNAVAILABLE", "Billing is temporarily unavailable.");
  } finally { await sql.end({ timeout: 2 }); }
}

export async function readBoundedRawBody(request: Request, maximumBytes = 256 * 1024): Promise<string> {
  const reader = request.body?.getReader();
  if (!reader) throw new HttpError(400, "WEBHOOK_INVALID", "Invalid webhook.");
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > maximumBytes) { await reader.cancel(); throw new HttpError(413, "PAYLOAD_TOO_LARGE", "Webhook is too large."); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const body = new Uint8Array(total); let offset = 0;
  for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
  return new TextDecoder().decode(body);
}
