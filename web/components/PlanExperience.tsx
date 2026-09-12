"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, post } from "../lib/client";
import type { Conditions, Fitness, Plan, Trail } from "../lib/types";
import { LiveConditions, PrepPlan } from "./plan";
import { VerdictCard } from "./assessment";

type Auth = { configured: boolean; user: null | { id: string; email?: string } };

export function PlanExperience({ trail, fitness, weeks, inline = false }: {
  trail: Trail;
  fitness: Fitness;
  weeks: number;
  inline?: boolean;
}) {
  const [tripDate, setTripDate] = useState("");
  const [plan, setPlan] = useState<Plan>();
  const [conditions, setConditions] = useState<Conditions | null>(null);
  const [conditionError, setConditionError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedId, setSavedId] = useState("");
  const [email, setEmail] = useState("");
  const [needsEmail, setNeedsEmail] = useState(false);
  const [notice, setNotice] = useState("");
  const requestId = useRef(0);
  const controller = useRef<AbortController | null>(null);

  const buildPlan = useCallback(async () => {
    controller.current?.abort();
    const current = ++requestId.current;
    const signalController = new AbortController();
    controller.current = signalController;
    setLoading(true); setError(""); setPlan(undefined); setConditions(null); setConditionError(""); setSavedId("");
    try {
      const value = await post<Plan>("/api/plan", { trail_id: trail.id, fitness, weeks, ...(tripDate ? { trip_date: tripDate } : {}) }, signalController.signal);
      if (current !== requestId.current) return;
      setPlan(value);
      if (tripDate) {
        api<Conditions>(`/api/conditions?trail=${encodeURIComponent(trail.id)}&date=${encodeURIComponent(tripDate)}`, { signal: signalController.signal })
          .then((value) => { if (current === requestId.current) setConditions(value); })
          .catch((cause: Error) => { if (current === requestId.current && cause.name !== "AbortError") setConditionError("We could not load dated conditions. Your plan is still available."); });
      }
    } catch (cause) {
      if ((cause as Error).name !== "AbortError" && current === requestId.current) setError((cause as Error).message);
    } finally { if (current === requestId.current) setLoading(false); }
  }, [fitness, trail.id, tripDate, weeks]);

  // Requesting this resource on mount is deliberate; state updates occur after the API resolves.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void buildPlan(); return () => controller.current?.abort(); }, [buildPlan]);

  const save = async () => {
    if (!plan) return;
    setSaving(true); setError(""); setNotice("");
    try {
      const auth = await api<Auth>("/api/auth");
      if (!auth.configured) throw new Error("Saving is unavailable while managed email sign-in is being configured.");
      if (!auth.user) {
        setNeedsEmail(true);
        if (!email.trim()) { setNotice("Enter your email below, then choose Save this plan to receive a sign-in link."); return; }
        sessionStorage.setItem("beready:pending-plan", JSON.stringify(plan));
        await post<{ message: string }>("/api/auth", { email });
        setNotice("Check your email. Open the sign-in link in this tab so Workspace can restore your draft.");
        return;
      }
      const result = await post<{ id: string }>("/api/plans", { plan });
      sessionStorage.removeItem("beready:pending-plan");
      setSavedId(result.id);
    } catch (cause) { setError((cause as Error).message); } finally { setSaving(false); }
  };

  return <section className={inline ? "stack plan-experience" : "stack"}>
    {!inline && <header className="page-intro"><p className="eyebrow">Free preparation plan</p><h1>Build towards the trail</h1><p>Adding a hike date recalculates the available full weeks.</p></header>}
    <section className="card"><label>Optional hike date<input type="date" disabled={saving} value={tripDate} onChange={(event) => setTripDate(event.target.value)} /></label><button onClick={() => void buildPlan()} disabled={loading || saving}>{loading ? "Updating…" : "Update plan"}</button></section>
    {error && <p role="alert">{error} <button className="text-button" onClick={() => void (plan ? save() : buildPlan())}>Retry</button></p>}
    {notice && <p role="status">{notice}</p>}
    {plan && tripDate && <VerdictCard trail={trail} assessment={plan.assessment} fitness={fitness} />}
    {loading ? <p aria-busy="true">Building your plan…</p> : plan && <><PrepPlan plan={plan} onSave={() => void save()} saving={saving} savedId={savedId} />
      {!savedId && needsEmail && <section className="card"><label>Email to save this plan<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /></label><p className="muted">A managed email sign-in is only used to save and track your plan.</p></section>}
      {tripDate && <LiveConditions conditions={conditions} error={conditionError} />}</>}
  </section>;
}
