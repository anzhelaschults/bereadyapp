import "server-only";
import { randomUUID } from "node:crypto";

const routes = new Set(["plan", "progress", "conditions", "discover", "ask", "health"]);
const LIMIT = 64 * 1024;

function failure(status: number, code: string, message: string, requestId: string) {
  return Response.json({ error: { code, message } }, {
    status, headers: { "Cache-Control": "no-store", "X-Request-ID": requestId },
  });
}

async function boundedBody(request: Request | Response, limit = LIMIT): Promise<string> {
  if (!request.body) return "";
  const reader = request.body.getReader();
  const decoder = new TextDecoder();
  let size = 0;
  let body = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) throw new RangeError("payload");
      body += decoder.decode(value, { stream: true });
    }
    return body + decoder.decode();
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

/** Same-origin BFF. No caller-controlled upstream path, host, or forwarded cookies. */
export async function forwardPolicy(request: Request, endpoint: string) {
  const requestId = randomUUID();
  const started = performance.now();
  if (!routes.has(endpoint)) return failure(404, "NOT_FOUND", "Not found.", requestId);
  if (request.method === "POST") {
    const origin = request.headers.get("origin");
    const expected = new URL(process.env.APP_URL || request.url).origin;
    if (origin && origin !== expected) return failure(403, "FORBIDDEN", "Request origin is not allowed.", requestId);
    if (!request.headers.get("content-type")?.startsWith("application/json")) {
      return failure(415, "CONTENT_TYPE", "Send JSON data.", requestId);
    }
  }
  let body: string | undefined;
  try {
    if (request.method === "POST") {
      body = await boundedBody(request);
      JSON.parse(body);
    }
  } catch (error) {
    return failure(error instanceof RangeError ? 413 : 422, "VALIDATION_ERROR", "Check the request data.", requestId);
  }
  try {
    const upstream = new URL(`/${endpoint}`, process.env.BEREADY_API_URL || "http://127.0.0.1:8000");
    if (!["http:", "https:"].includes(upstream.protocol)) throw new Error("Invalid API configuration");
    if (endpoint === "conditions") {
      const query = new URL(request.url).searchParams;
      upstream.searchParams.set("trail", query.get("trail") || "");
      upstream.searchParams.set("date", query.get("date") || "");
    }
    const response = await fetch(upstream, {
      method: request.method, body, cache: "no-store", redirect: "error",
      headers: { "Content-Type": "application/json", "X-Request-ID": requestId },
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) {
      const status = response.status >= 400 && response.status < 500 ? response.status : 503;
      return failure(status, status === 503 ? "SERVICE_UNAVAILABLE" : "VALIDATION_ERROR",
        status === 503 ? "The preparation service is unavailable. Please try again." : "Check the trail, training level, weeks, and dates.", requestId);
    }
    // Backend responses can contain a complete catalog, so allow more than input.
    if (!response.headers.get("content-type")?.includes("application/json")) throw new Error("Invalid upstream content type");
    const text = await boundedBody(response, 8_000_000);
    const payload: unknown = JSON.parse(text);
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) throw new Error("Invalid upstream response");
    console.info(JSON.stringify({ event: "policy_request", request_id: requestId, route: endpoint,
      status: response.status, duration_ms: Math.round(performance.now() - started) }));
    return Response.json(payload, { headers: { "Cache-Control": "no-store", "X-Request-ID": requestId } });
  } catch {
    console.warn(JSON.stringify({ event: "policy_unavailable", request_id: requestId, route: endpoint,
      duration_ms: Math.round(performance.now() - started) }));
    return failure(503, "SERVICE_UNAVAILABLE", "The preparation service is unavailable. Your trail verdict still works. Please try again.", requestId);
  }
}
