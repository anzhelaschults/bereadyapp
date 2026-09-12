import type { ApiError } from "./types";

export class RequestError extends Error {
  constructor(public code: string, message: string) { super(message); }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { ...init, headers: { "content-type": "application/json", ...init.headers } });
  const body = await response.json().catch(() => null) as T | ApiError | null;
  if (!response.ok) {
    const error = body && typeof body === "object" && "error" in body ? body.error : undefined;
    throw new RequestError(error?.code ?? "request_failed", error?.message ?? "Something went wrong. Please try again.");
  }
  return body as T;
}

export function post<T>(path: string, body: unknown, signal?: AbortSignal) {
  return api<T>(path, { method: "POST", body: JSON.stringify(body), signal });
}
