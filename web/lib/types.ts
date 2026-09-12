export type Fitness = 1 | 2 | 3;
export type VerdictStatus = "ready" | "cond" | "hard" | "toosoon";
export interface Assessment {
  status: VerdictStatus; head: string; why: string; plan: string[];
  inputs: string[]; weeks: number; floor: number; comfortable: number;
}
export interface Challenge { title: string; icon: string; text: string }
export interface TrailContent {
  challenges: Record<string, Challenge[]>; worth_it: string;
  typical_conditions: string; review_status: string;
}
export interface Trail {
  id: string; name: string; region: "Norway" | "Iceland";
  km: number; days: number; grade: number; diff: number; risk: string;
  exposure: boolean; season: {start: string; end: string} | null;
  season_note: string; latitude: number; longitude: number;
  elevation_m: number; sources: string[]; content: TrailContent;
  assessments: Record<string, Record<string, Assessment>>;
}
export interface Catalog { schema_version: 1; weeks: number[]; trails: Trail[] }
export interface Filters {
  region?: string; length?: "day" | "multi"; max_grade?: number;
  hide_exposed?: boolean; in_season?: boolean; reachable?: boolean;
}
export interface RankedTrail extends Trail { assessment: Assessment }
export interface PlanSession {
  id: string; week: number; day: number; date: string;
  kind: "base" | "strength" | "hike"; label: string; adapted: boolean;
}
export interface Plan {
  version: 1; trail_id: string; fitness: Fitness; start_date: string;
  trip_date: string; weeks: number; assessment: Assessment;
  sessions: PlanSession[]; notes: string[];
}
export interface SessionLog { session_id: string; done_at: string }
export interface Progress {
  score: number; completed: number; total: number; on_track: boolean;
  streak: number; this_week_completed: number; this_week_total: number;
  label: string;
}
export interface SavedPlan { id: string; plan: Plan; logs: SessionLog[]; progress: Progress }
export interface Conditions {
  status: "live" | "unavailable" | "outside_forecast" | "disabled";
  date: string; checked_at: string; source: string; source_url: string;
  summary: string; season_note: string; closure_status: "unknown";
  temperature_min: number | null; temperature_max: number | null;
  precipitation_mm: number | null; wind_kmh: number | null;
}
export interface ApiError { error: {code: string; message: string} }
