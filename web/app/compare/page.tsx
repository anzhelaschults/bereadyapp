"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fetchCatalog, assessmentFor } from "../../lib/catalog";
import type { Catalog, Fitness, RankedTrail } from "../../lib/types";
import { CompareTrails } from "../../components/discovery";

function CompareContent() {
  const params = useSearchParams();
  const [catalog, setCatalog] = useState<Catalog>();
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetchCatalog(controller.signal).then(setCatalog).catch((cause: Error) => { if (cause.name !== "AbortError") setError(cause.message); });
    return () => controller.abort();
  }, []);
  if (error) return <main><p role="alert">{error}</p><button onClick={() => location.reload()}>Retry</button></main>;
  if (!catalog) return <main><p aria-busy="true">Loading comparison…</p></main>;
  const ids = (params.get("trails") ?? "").split(",").filter(Boolean);
  const fitness = Number(params.get("fitness")) as Fitness;
  const weeks = Number(params.get("weeks"));
  const valid = ids.length >= 2 && ids.length <= 3 && new Set(ids).size === ids.length && [1, 2, 3].includes(fitness) && Number.isInteger(weeks) && weeks >= 1 && weeks <= 52;
  const trails: RankedTrail[] = valid ? ids.flatMap((id) => {
    const trail = catalog.trails.find((item) => item.id === id);
    const assessment = trail && assessmentFor(trail, fitness, weeks);
    return trail && assessment ? [{ ...trail, assessment }] : [];
  }) : [];
  return <main className="stack comparison-page">{trails.length === ids.length && valid ? <CompareTrails trails={trails} fitness={fitness} weeks={weeks} /> : <section className="card"><h1>Choose two or three trails</h1><p>Choose a training level and weeks in Discover. We do not assume missing inputs.</p></section>}<Link href="/discover">Back to discovery</Link></main>;
}

export default function ComparePage() {
  return <Suspense fallback={<main><p>Loading comparison…</p></main>}><CompareContent /></Suspense>;
}
