"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { assessmentFor, fetchCatalog, filterAndSortCatalog } from "../lib/catalog";
import { post } from "../lib/client";
import type { Assessment, Catalog, Filters, Fitness, RankedTrail } from "../lib/types";
import { FitnessRadios, initialFitness } from "./assessment";
import { DiscoverList, FiltersPanel } from "./discovery";

type Answer = { message: string; trails?: RankedTrail[]; assessment?: Assessment };

export function Discover() {
  const [catalog, setCatalog] = useState<Catalog>();
  const [fitness, setFitness] = useState<Fitness | null>(initialFitness);
  const [weeks, setWeeks] = useState(12);
  const [filters, setFilters] = useState<Filters>({});
  const [selected, setSelected] = useState<string[]>([]);
  const [catalogError, setCatalogError] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer>();
  const [askError, setAskError] = useState("");
  const [asking, setAsking] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetchCatalog(controller.signal).then(setCatalog).catch((error: Error) => {
      if (error.name !== "AbortError") setCatalogError(error.message);
    });
    return () => controller.abort();
  }, []);

  const ask = async (event: FormEvent) => {
    event.preventDefault();
    if (!question.trim() || asking) return;
    setAsking(true); setAskError(""); setAnswer(undefined);
    try { setAnswer(await post<Answer>("/api/ask", { query: question })); }
    catch (error) { setAskError((error as Error).message); }
    finally { setAsking(false); }
  };
  if (catalogError) return <main><p role="alert">{catalogError}</p><button onClick={() => location.reload()}>Retry</button></main>;
  if (!catalog) return <main><p aria-busy="true">Loading trail catalogue…</p></main>;
  const assessments = fitness ? Object.fromEntries(catalog.trails.map((trail) => [trail.id, assessmentFor(trail, fitness, weeks)!])) : {};
  const displayed = fitness ? filterAndSortCatalog(catalog.trails, assessments, filters) : catalog.trails;
  const filtered = Object.values(filters).some(Boolean);

  return <main className="stack discover-page">
    <header className="page-intro"><p className="eyebrow">Ask BeReady</p><h1>What can you handle?</h1><p>Find a trail you can prepare for, in the time you have.</p></header>
    <section className="card"><FitnessRadios value={fitness} onChange={setFitness} />
      <label className="slider-label">Weeks until your hike <output>{weeks} weeks</output><input aria-label="Weeks until your hike" type="range" min="1" max="52" value={weeks} onChange={(e) => setWeeks(Number(e.target.value))} /></label>
      <fieldset disabled={!fitness}><FiltersPanel filters={filters} onChange={setFilters} /></fieldset>
    </section>
    <DiscoverList trails={displayed} selected={selected} assessed={fitness !== null} filtered={filtered} onSelect={(id) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 3 ? [...current, id] : current)} />
    {selected.length > 0 && <aside className="compare-bar"><span>{selected.length} of 3 selected</span><button className="light" onClick={() => setSelected([])}>Clear</button>{selected.length >= 2 && fitness && <Link className="button light" href={`/compare?trails=${selected.join(",")}&fitness=${fitness}&weeks=${weeks}`}>Compare selected trails</Link>}</aside>}
    <section className="card"><h2>Ask in your own words</h2><form onSubmit={ask}>
      <label>Your question<input value={question} maxLength={1000} onChange={(event) => setQuestion(event.target.value)} placeholder="Norway, I don't train, 8 weeks" /></label>
      <p className="muted">Try “What can I handle in Norway in eight weeks? I don’t train.” This tool asks when it cannot interpret your request.</p>
      <button disabled={asking || !question.trim()}>{asking ? "Checking…" : "Ask BeReady"}</button>
      {askError && <p role="alert">{askError} The catalog above still works.</p>}
      {answer && <div role="status" aria-label="Discovery answer"><p>{answer.message}</p>{answer.trails && <ul>{answer.trails.map((trail) => <li key={trail.id}>{trail.name}: {trail.assessment.head}</li>)}</ul>}</div>}
    </form></section>
  </main>;
}
