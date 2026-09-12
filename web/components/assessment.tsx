"use client";

import type { Assessment, Fitness, Trail } from "../lib/types";

export const initialFitness: Fitness | null = null;
const labels: Record<Fitness, string> = { 1: "I don’t train", 2: "Sometimes active", 3: "I train regularly" };

export function FitnessRadios({ value, onChange }: { value: Fitness | null; onChange: (value: Fitness) => void }) {
  return <fieldset className="fitness"><legend>Your training level</legend><p>Choose the option that is true today.</p><div>{([1, 2, 3] as Fitness[]).map((fitness) => <label key={fitness} className="radio-card"><input type="radio" name="fitness" checked={value === fitness} onChange={() => onChange(fitness)} /><span>{labels[fitness]}</span></label>)}</div></fieldset>;
}

export function VerdictCard({ assessment }: { trail: Trail; assessment?: Assessment; fitness?: Fitness }) {
  if (!assessment) return <section className="card verdict empty" aria-live="polite"><p className="eyebrow">Your verdict</p><h2>Choose your training level</h2><p>Your verdict will appear here, with the time this trip needs.</p></section>;
  const { floor, comfortable, weeks } = assessment;
  const extent = Math.max(comfortable + 6, weeks + 1);
  const position = (value: number) => value / extent * 100;
  return <section className={`card verdict ${assessment.status}`} aria-live="polite">
    <p className="eyebrow">Verdict</p><h2>{assessment.head}</h2><p>{assessment.why}</p>
    {comfortable > floor && <div className="runway" aria-label={`You have ${weeks} weeks. Minimum preparation is ${floor} weeks. Comfortable preparation is about ${comfortable} weeks.`}>
      <p><b>You have {weeks} weeks</b></p>
      <div className="runway-track" aria-hidden="true">
        <span className="soon" style={{ width: `${position(floor)}%` }} />
        <span className="tight" style={{ left: `${position(floor)}%`, width: `${position(comfortable - floor)}%` }} />
        <i data-testid="runway-marker" style={{ left: `${position(weeks)}%` }} />
      </div>
      <div className="runway-scale"><span style={{ left: `${position(floor)}%` }}>{floor} wk minimum</span><span style={{ left: `${position(comfortable)}%` }}>{comfortable} wk comfortable</span></div>
      <p className="muted">These weeks count only if you train. Conditions and mountain skills are separate.</p>
    </div>}
    <ul>{assessment.plan.map((item) => <li key={item}>{item}</li>)}</ul>
    <p className="facts">Computed from {assessment.inputs.join(", ")}.</p>
    <p className="disclaimer">Fitness preparation only, not medical or mountain-safety clearance.</p>
  </section>;
}

export function HardWorthIt({ trail, fitness }: { trail: Trail; fitness: Fitness | null }) {
  const challenges = fitness ? trail.content.challenges[String(fitness)] ?? [] : [];
  return <section className="card motivation"><p className="eyebrow">This trail</p><h2>What is hard, and why it is worth it</h2>
    <ul className="challenge-list">{challenges.map((item) => <li key={item.title}><b>{item.title}</b><span>{item.text}</span></li>)}</ul>
    <div className="worth"><p className="eyebrow">Why it is worth it</p><p>{trail.content.worth_it}</p></div>
  </section>;
}

export function TrailConditionsStatic({ trail }: { trail: Trail }) {
  return <section className="card"><p className="eyebrow">Typical conditions, not live</p><h2>Plan for the trail, not a promise</h2><p>{trail.content.typical_conditions}</p><p>{trail.season_note}</p>
    <p className="muted">Content {trail.content.review_status}. Seasons and exposure still need content-owner sign-off.</p>
    <ul className="source-links">{trail.sources.map((source, index) => <li key={source}><a href={source} rel="noreferrer">Route source {index + 1}</a></li>)}</ul>
  </section>;
}
