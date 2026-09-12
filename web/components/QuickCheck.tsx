"use client";

import { useEffect, useState } from "react";
import { assessmentFor, fetchCatalog } from "../lib/catalog";
import type { Catalog, Fitness } from "../lib/types";
import { FitnessRadios, HardWorthIt, initialFitness, TrailConditionsStatic, VerdictCard } from "./assessment";
import { PlanExperience } from "./PlanExperience";
import { gradeName } from "./discovery";

export function QuickCheck({ initialTrail }: { initialTrail?: string }) {
  const [catalog, setCatalog] = useState<Catalog>();
  const [error, setError] = useState("");
  const [trailId, setTrailId] = useState(initialTrail ?? "");
  const [fitness, setFitness] = useState<Fitness | null>(initialFitness);
  const [weeks, setWeeks] = useState(12);
  const [showPlan, setShowPlan] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchCatalog(controller.signal).then((data) => {
      setCatalog(data);
      setTrailId((current) => current && data.trails.some((trail) => trail.id === current) ? current : data.trails[0]?.id ?? "");
    }).catch((cause: Error) => { if (cause.name !== "AbortError") setError(cause.message); });
    return () => controller.abort();
  }, []);

  if (error) return <section className="card error"><p>{error}</p><button onClick={() => location.reload()}>Retry</button></section>;
  if (!catalog) return <p aria-busy="true">Loading trail catalogue…</p>;
  const trail = catalog.trails.find((item) => item.id === trailId)!;
  const assessment = fitness ? assessmentFor(trail, fitness, weeks) : undefined;
  const resetPlan = () => setShowPlan(false);

  return <main className="stack">
    <header className="page-intro"><p className="eyebrow">BeReady</p><h1>Can you be ready?</h1><p>A quiet, practical check for a trail you have in mind.</p></header>
    <section className="card"><label>Trail<select value={trailId} onChange={(event) => { setTrailId(event.target.value); resetPlan(); }}>{catalog.trails.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
      <p className="facts">{trail.km} km, {trail.days} {trail.days === 1 ? "day" : "days"}, {gradeName[trail.grade]}. Watch: {trail.risk}</p>
      <FitnessRadios value={fitness} onChange={(value) => { setFitness(value); resetPlan(); }} />
      <label className="slider-label">Weeks until your hike <output>{weeks} weeks</output><input aria-label="Weeks until your hike" type="range" min="1" max="52" value={weeks} onChange={(event) => { setWeeks(Number(event.target.value)); resetPlan(); }} /></label>
    </section>
    <VerdictCard trail={trail} assessment={assessment} fitness={fitness ?? undefined} />
    {fitness && <><HardWorthIt trail={trail} fitness={fitness} /><TrailConditionsStatic trail={trail} /></>}
    {fitness && assessment && !showPlan && <button className="button" onClick={() => setShowPlan(true)}>See my prep plan</button>}
    {showPlan && fitness && <PlanExperience trail={trail} fitness={fitness} weeks={weeks} inline />}
  </main>;
}
