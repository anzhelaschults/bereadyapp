export const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_RE.test(value);
}

/** Calendar-date validation, intentionally not Date.parse's permissive parsing. */
export function isIsoDate(value: unknown): value is string {
  if (typeof value !== "string" || !ISO_DATE_RE.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

export function utcToday(): string {
  return new Date().toISOString().slice(0, 10);
}

export function parseCompletion(value: unknown): { session_id: string; done: boolean } | null {
  if (!value || typeof value !== "object") return null;
  const input = value as Record<string, unknown>;
  return isUuid(input.session_id) && typeof input.done === "boolean"
    ? { session_id: input.session_id, done: input.done }
    : null;
}

export function validFitness(value: unknown): value is 1 | 2 | 3 {
  return value === 1 || value === 2 || value === 3;
}
