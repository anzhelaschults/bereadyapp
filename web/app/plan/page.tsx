"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fetchCatalog } from "../../lib/catalog";
import type { Catalog, Fitness } from "../../lib/types";
import { PlanExperience } from "../../components/PlanExperience";

function PlanContent() {
  const params = useSearchParams();
  const [catalog, setCatalog] = useState<Catalog>();
  const [error, setError] = useState("");
  const trailId = params.get("trail") ?? "";
  const fitness = Number(params.get("fitness"));
  const weeks = Number(params.get("weeks"));

  useEffect(() => { const controller = new AbortController(); fetchCatalog(controller.signal).then(setCatalog).catch((cause: Error) => { if (cause.name !== "AbortError") setError(cause.message); }); return () => controller.abort(); }, []);
  if (!trailId || ![1, 2, 3].includes(fitness) || !Number.isInteger(weeks) || weeks < 1 || weeks > 52) return <main><section className="card"><h1>Plan details are incomplete</h1><p>Choose a trail, training level, and one to 52 weeks in Quick Check first.</p><a href="/quickcheck">Go to Quick Check</a></section></main>;
  if (error) return <main><p role="alert">{error}</p><button onClick={() => location.reload()}>Retry</button></main>;
  if (!catalog) return <main><p aria-busy="true">Loading plan details…</p></main>;
  const trail = catalog.trails.find((item) => item.id === trailId);
  if (!trail) return <main><section className="card"><h1>That trail is not in the catalogue</h1><a href="/quickcheck">Choose a listed trail</a></section></main>;
  return <main><PlanExperience trail={trail} fitness={fitness as Fitness} weeks={weeks} /></main>;
}
export default function PlanPage() { return <Suspense fallback={<main><p>Loading plan…</p></main>}><PlanContent /></Suspense>; }
