import { describe, expect, it } from "vitest";
import type { Trail } from "../lib/types";
import { filterAndSortCatalog } from "../lib/catalog";
import { initialFitness } from "../components/assessment";

const assessment = (status: "ready" | "cond" | "hard" | "toosoon") => ({
  status, head: status, why: "", plan: [], inputs: [], weeks: 8, floor: 4, comfortable: 8,
});
const trail = (id: string, diff: number, km: number, overrides: Partial<Trail> = {}): Trail => ({
  id, name: id, region: "Norway", km, days: 1, grade: diff, diff, risk: "", exposure: false,
  season: null, season_note: "", latitude: 0, longitude: 0, elevation_m: 0, sources: [],
  content: { challenges: {}, worth_it: "", typical_conditions: "", review_status: "" }, assessments: {}, ...overrides,
});

describe("assessment input defaults", () => {
  it("does not preselect a fitness level", () => {
    expect(initialFitness).toBeNull();
  });
});

describe("filterAndSortCatalog", () => {
  it("keeps all matching trails and ranks verdict, difficulty, distance, then id", () => {
    const trails = [trail("zeta", 2, 9), trail("beta", 2, 4), trail("alpha", 1, 12), trail("hard", 1, 1)];
    const results = filterAndSortCatalog(trails, { zeta: assessment("cond"), beta: assessment("cond"), alpha: assessment("ready"), hard: assessment("hard") }, {});
    expect(results.map((result) => result.id)).toEqual(["alpha", "beta", "zeta", "hard"]);
  });

  it("retains trails with no seasonal window when filtering for season", () => {
    const unknownSeason = trail("unknown", 1, 3, { season: null });
    const results = filterAndSortCatalog([unknownSeason], { unknown: assessment("ready") }, { in_season: true }, new Date("2026-01-01"));
    expect(results.map((result) => result.id)).toEqual(["unknown"]);
  });

  it("keeps all trails normally but removes only too-soon trails when reachable is requested", () => {
    const trails = [trail("ready", 1, 3), trail("later", 3, 10)];
    const scores = { ready: assessment("ready"), later: assessment("toosoon") };
    expect(filterAndSortCatalog(trails, scores, {}).map((result) => result.id)).toEqual(["ready", "later"]);
    expect(filterAndSortCatalog(trails, scores, { reachable: true }).map((result) => result.id)).toEqual(["ready"]);
  });

  it("applies region, length, grade, exposure, and season filters without scoring in the browser", () => {
    const trails = [
      trail("short", 1, 3, { region: "Norway", days: 1, grade: 1, exposure: false, season: { start: "01-01", end: "12-31" } }),
      trail("long", 2, 30, { region: "Iceland", days: 3, grade: 2, exposure: true, season: { start: "06-01", end: "09-01" } }),
    ];
    const results = filterAndSortCatalog(trails, { short: assessment("ready"), long: assessment("cond") }, { region: "Norway", length: "day", max_grade: 1, hide_exposed: true, in_season: true }, new Date("2026-07-01"));
    expect(results.map((result) => result.id)).toEqual(["short"]);
  });
});
