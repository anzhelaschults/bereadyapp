import { NextRequest, NextResponse } from "next/server";

export const MAX_JSON_BYTES = 64 * 1024;

export class HttpError extends Error {
  constructor(public readonly status: number, public readonly code: string, message: string) { super(message); }
}

function requestId(): string {
  return crypto.randomUUID();
}

export function errorResponse(error: unknown, id = requestId()): NextResponse {
  if (error instanceof HttpError) {
    return NextResponse.json({ error: { code: error.code, message: error.message } }, { status: error.status, headers: { "Cache-Control": "no-store", "X-Request-Id": id } });
  }
  // Log only a stable classification: Error.message can contain provider secrets.
  console.error(JSON.stringify({ event: "server_error", request_id: id, error_type: error instanceof Error ? error.name : typeof error }));
  return NextResponse.json({ error: { code: "INTERNAL", message: "Unable to complete this request." } }, { status: 500, headers: { "Cache-Control": "no-store", "X-Request-Id": id } });
}

export async function readJson(request: Request): Promise<unknown> {
  const contentType = request.headers.get("content-type");
  if (!contentType?.toLowerCase().startsWith("application/json")) throw new HttpError(415, "UNSUPPORTED_MEDIA_TYPE", "Request must use application/json.");
  const contentLength = request.headers.get("content-length");
  if (contentLength && (!/^\d+$/.test(contentLength) || Number(contentLength) > MAX_JSON_BYTES)) throw new HttpError(413, "PAYLOAD_TOO_LARGE", "Request body is too large.");
  if (!request.body) throw new HttpError(422, "VALIDATION_ERROR", "Invalid JSON input.");
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_JSON_BYTES) {
        await reader.cancel();
        throw new HttpError(413, "PAYLOAD_TOO_LARGE", "Request body is too large.");
      }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const raw = new TextDecoder().decode(concat(chunks, total));
  try { return JSON.parse(raw); } catch { throw new HttpError(422, "VALIDATION_ERROR", "Invalid JSON input."); }
}

function concat(chunks: Uint8Array[], total: number): Uint8Array {
  const result = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.byteLength; }
  return result;
}

function applicationOrigin(): string {
  try { return new URL(process.env.APP_URL ?? "http://localhost:3000").origin; }
  catch { return ""; }
}

/** Cookie-authenticated mutations must be initiated by the configured application origin, never Host. */
export function requireSameOrigin(request: NextRequest): void {
  const origin = request.headers.get("origin");
  if (!origin || !applicationOrigin() || origin !== applicationOrigin()) throw new HttpError(403, "FORBIDDEN", "This request origin is not allowed.");
}

export const noStore = { "Cache-Control": "no-store" };
