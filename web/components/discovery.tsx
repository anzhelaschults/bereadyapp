"use client";

import Link from "next/link";
import type { Filters, Fitness, RankedTrail, Trail } from "../lib/types";

export const gradeName: Record<number, string> = { 1: "Easy", 2: "Moderate", 3: "Demanding", 4: "Very demanding" };

export function DiscoverList({ trails, selected, onSelect, assessed, filtered }: {
  trails: (Trail | RankedTrail)[]; selected: string[]; onSelect: (id: string) => void;
  assessed: boolean; filtered: boolean;
}) {
  return <>
    <p className="sort-note">{assessed ? "Ranked by your readiness, then difficulty and distance." : "Choose your training level to see personalized verdicts."} {filtered ? "Only your explicit filters hide trails." : "All nine trails stay visible."}</p>
    {!trails.length && <p role="status">No trails match these filters. Widen them to see more options.</p>}
    <ul className="trail-list">{trails.map((trail) => {
      const assessment = assessed && "assessment" in trail ? trail.assessment : null;
      return <li key={trail.id} className={`trail-row ${assessment?.status ?? ""}`}>
        <div><h2>{trail.name}</h2><p>{trail.region}, {trail.km} km, {trail.days} {trail.days === 1 ? "day" : "days"}, {gradeName[trail.grade]}</p>
          <p>{trail.content.worth_it}</p></div>
        <div>{assessment && <><span className={`status ${assessment.status}`}>{assessment.head}</span><p>{assessment.comfortable ? `Comfortable preparation is about ${assessment.comfortable} weeks.` : "Your current training matches the fitness requirement."}</p></>}
          <label><input type="checkbox" aria-label={`Compare ${trail.name}`} checked={selected.includes(trail.id)} onChange={() => onSelect(trail.id)} disabled={!assessed || (!selected.includes(trail.id) && selected.length >= 3)} /> Compare</label>
          <Link href={`/quickcheck?trail=${encodeURIComponent(trail.id)}`}>View check</Link></div>
      </li>;
    })}</ul>
  </>;
}

export function FiltersPanel({ filters, onChange }: { filters: Filters; onChange: (filters: Filters) => void }) {
  const update = (key: keyof Filters, value: Filters[keyof Filters]) => onChange({ ...filters, [key]: value || undefined });
  return <fieldset className="filters"><legend>Refine the list</legend>
    <label>Region<select value={filters.region ?? ""} onChange={(e) => update("region", e.target.value)}><option value="">All regions</option><option>Norway</option><option>Iceland</option></select></label>
    <label>Length<select value={filters.length ?? ""} onChange={(e) => update("length", e.target.value as Filters["length"])}><option value="">Any length</option><option value="day">Day hike</option><option value="multi">Multi-day</option></select></label>
    <label>Difficulty ceiling<select value={filters.max_grade ?? ""} onChange={(e) => update("max_grade", e.target.value ? Number(e.target.value) : undefined)}><option value="">Any grade</option>{[1, 2, 3].map((grade) => <option key={grade} value={grade}>Up to {gradeName[grade]}</option>)}</select></label>
    <label><input type="checkbox" checked={filters.hide_exposed ?? false} onChange={(e) => update("hide_exposed", e.target.checked)} /> Hide exposed trails</label>
    <label><input type="checkbox" checked={filters.in_season ?? false} onChange={(e) => update("in_season", e.target.checked)} /> In typical season now</label>
    <label><input type="checkbox" checked={filters.reachable ?? false} onChange={(e) => update("reachable", e.target.checked)} /> Reachable in my time</label>
  </fieldset>;
}

export function CompareTrails({ trails, fitness, weeks }: { trails: RankedTrail[]; fitness: Fitness; weeks: number }) {
  const soonest = Math.min(...trails.map((trail) => trail.assessment.comfortable));
  return <section className="card"><h1>Compare trails</h1><p>You have {weeks} {weeks === 1 ? "week" : "weeks"}. The same Python assessments power Quick check and this comparison.</p>
    <div className="compare-table" tabIndex={0} role="region" aria-label="Scrollable trail comparison"><table><caption className="sr-only">Personalized comparison of {trails.length} trails</caption>
      <thead><tr><th scope="col">Trail</th>{trails.map((trail) => <th scope="col" key={trail.id}>{trail.name}</th>)}</tr></thead>
      <tbody>
        <tr><th scope="row">Region</th>{trails.map((t) => <td key={t.id}>{t.region}</td>)}</tr>
        <tr><th scope="row">Verdict for you</th>{trails.map((t) => <td key={t.id}><span className={`status ${t.assessment.status}`}>{t.assessment.head}</span></td>)}</tr>
        <tr><th scope="row">Weeks needed</th>{trails.map((t) => <td key={t.id}>{t.assessment.comfortable === 0 ? "No fitness gap" : `About ${t.assessment.comfortable} weeks for a comfortable build`}{t.assessment.comfortable === soonest && <strong className="soonest">Soonest</strong>}</td>)}</tr>
        <tr><th scope="row">Length</th>{trails.map((t) => <td key={t.id}>{t.km} km, {t.days} {t.days === 1 ? "day" : "days"}</td>)}</tr>
        <tr><th scope="row">Official grade</th>{trails.map((t) => <td key={t.id}>{gradeName[t.grade]}</td>)}</tr>
        <tr><th scope="row">The hard part</th>{trails.map((t) => <td key={t.id}>{t.content.challenges[String(fitness)].map((c) => <p key={c.title}><b>{c.title}.</b> {c.text}</p>)}</td>)}</tr>
        <tr><th scope="row">Why it is worth it</th>{trails.map((t) => <td key={t.id}>{t.content.worth_it}</td>)}</tr>
        <tr><th scope="row">Typical season</th>{trails.map((t) => <td key={t.id}>{t.season_note}</td>)}</tr>
      </tbody></table></div><p className="muted">Content review pending. Typical season is not a live access report.</p>
  </section>;
}
