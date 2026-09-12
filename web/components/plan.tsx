"use client";

import type { CSSProperties } from "react";
import type { Conditions, Plan, Progress } from "../lib/types";

export function PrepPlan({ plan, onSave, saving, savedId }: {
  plan: Plan;
  onSave?: () => void;
  saving?: boolean;
  savedId?: string;
}) {
  const weeks = [...new Set(plan.sessions.map((session) => session.week))];
  return <section className="card">
    <p className="eyebrow">Your free plan</p>
    <h2>{plan.weeks}-week preparation plan</h2>
    <p>Trip date: {plan.trip_date}</p>
    {plan.assessment.status === "toosoon" && <p className="warning">This timeframe is not enough to imply this trail is achievable. Start with the base work and reassess with more time.</p>}
    {plan.notes.length > 0 && <ul className="notes">{plan.notes.map((note) => <li key={note}>{note}</li>)}</ul>}
    {weeks.map((week) => <section className="plan-week" key={week}>
      <h3>Week {week}</h3>
      <ul>{plan.sessions.filter((session) => session.week === week).map((session) => <li key={session.id}>
        <time dateTime={session.date}>{session.date}</time> {session.label}{session.adapted ? " (adapted after a missed week)" : ""}
      </li>)}</ul>
    </section>)}
    {savedId ? <p role="status">Plan saved. <a href="/workspace">Open workspace</a></p> : onSave && <button className="button" disabled={saving} onClick={onSave}>{saving ? "Saving…" : "Save this plan"}</button>}
  </section>;
}

export function ProgressRing({ progress }: { progress: Progress }) {
  return <section className="progress">
    <div className="ring" style={{ "--progress": `${progress.score}%` } as CSSProperties}><span>{progress.score}%</span></div>
    <div><p className="eyebrow">Plan progress</p><h2>{progress.label}</h2>
      <p>{progress.completed} of {progress.total} planned sessions completed. This is plan progress, not physiological fitness.</p>
      <p>{progress.streak} week streak, {progress.this_week_completed} of {progress.this_week_total} this week</p>
    </div>
  </section>;
}

export function LiveConditions({ conditions, error }: { conditions: Conditions | null; error?: string }) {
  const live = conditions?.status === "live";
  return <section className="card">
    <p className="eyebrow">Conditions for your date</p>
    <h2>{live ? "Forecast available" : "Live conditions unavailable"}</h2>
    <p>{error ?? conditions?.summary ?? "Typical conditions are shown until a dated forecast is available."}</p>
    {live && conditions && <>
      <p>Forecast date: <time dateTime={conditions.date}>{conditions.date}</time></p>
      <dl className="weather-metrics">
        <div><dt>Temperature</dt><dd>{conditions.temperature_min} to {conditions.temperature_max} °C</dd></div>
        <div><dt>Precipitation</dt><dd>{conditions.precipitation_mm} mm</dd></div>
        <div><dt>Maximum wind</dt><dd>{conditions.wind_kmh} km/h</dd></div>
      </dl>
      <p className="muted">Source: <a href="https://open-meteo.com/">Open-Meteo</a>. Retrieved <time dateTime={conditions.checked_at}>{new Date(conditions.checked_at).toLocaleString("en-GB", { timeZone: "UTC" })} UTC</time>.</p>
    </>}
    {conditions && <p className="muted">{conditions.season_note} Closure status is unknown. Verify locally before travel.</p>}
  </section>;
}
