import type { Assessment, Catalog, Filters, RankedTrail, Trail } from "./types";

const verdictOrder = { ready: 0, cond: 1, hard: 2, toosoon: 3 } as const;

function isInSeason(trail: Trail, today: Date) {
  if (!trail.season) return true;
  const monthDay = `${String(today.getUTCMonth() + 1).padStart(2, "0")}-${String(today.getUTCDate()).padStart(2, "0")}`;
  const { start, end } = trail.season;
  return start <= end ? monthDay >= start && monthDay <= end : monthDay >= start || monthDay <= end;
}

export function assessmentFor(trail: Trail, fitness: number, weeks: number): Assessment | undefined {
  return trail.assessments[String(fitness)]?.[String(weeks)];
}

export function filterAndSortCatalog(trails: Trail[], assessments: Record<string, Assessment>, filters: Filters, today = new Date()): RankedTrail[] {
  return trails
    .filter((trail) => (!filters.region || trail.region === filters.region)
      && (!filters.length || (filters.length === "day" ? trail.days === 1 : trail.days > 1))
      && (!filters.max_grade || trail.grade <= filters.max_grade)
      && (!filters.hide_exposed || !trail.exposure)
      && (!filters.in_season || isInSeason(trail, today)))
    .map((trail) => ({ ...trail, assessment: assessments[trail.id] }))
    .filter((trail): trail is RankedTrail => Boolean(trail.assessment) && (!filters.reachable || trail.assessment.status !== "toosoon"))
    .sort((a, b) => verdictOrder[a.assessment.status] - verdictOrder[b.assessment.status]
      || a.diff - b.diff || a.km - b.km || a.id.localeCompare(b.id));
}


export async function fetchCatalog(signal?: AbortSignal): Promise<Catalog> {
  const response = await fetch("/catalog.json", { signal });
  if (!response.ok) throw new Error("The trail catalogue is unavailable. Please try again.");
  return response.json() as Promise<Catalog>;
}
