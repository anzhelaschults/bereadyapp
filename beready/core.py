"""Single deterministic readiness and conservative plan policy."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import copy
import uuid
from typing import Any

from .trails import TRAILS

GRADE_WORD = {1: "Easy", 2: "Moderate", 3: "Demanding", 4: "Very demanding"}
FIT_WORD = {1: "not training", 2: "sometimes active", 3: "training regularly"}
GAP_WORD = {1: "one step short", 2: "two steps short", 3: "a big jump up"}
THRESH = {1: (3, 6), 2: (6, 12), 3: (12, 20)}
_STATUS_WEIGHT = {"ready": 0, "cond": 1, "hard": 2, "toosoon": 3}
_NAMESPACE = uuid.UUID("b2b5b40f-bb9d-4e65-a0ac-f771f7b92bd1")


def _strict_int(value: Any, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer from {low} to {high}")
    return value


def _trail(trail_id: str) -> dict:
    if type(trail_id) is not str or trail_id not in TRAILS:
        raise ValueError("unknown trail")
    return TRAILS[trail_id]


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def _plan_for(weeks: int, multiday: bool) -> list[str]:
    if weeks < 8:
        plan = [
            "Start with regular easy walks and one general strength session each week.",
            "Use a weekend hike to practise time on your feet and your pack.",
            "Practise descents early and ease off in the final few days.",
        ]
    elif weeks < 20:
        plan = [
            "First weeks: establish steady easy activity and general strength.",
            "Middle weeks: use longer hikes and terrain practice as conditions allow.",
            "Final weeks: rehearse gear and terrain, then ease off before departure.",
        ]
    else:
        plan = [
            "Early months: build consistent easy activity and general strength.",
            "Middle months: add hill and terrain practice gradually.",
            "Final months: rehearse long days and terrain, then ease off before departure.",
        ]
    if multiday:
        plan.insert(2, "Practise back-to-back hiking days before a consecutive-day trek.")
    return plan


def assess(trail_id: str, fitness: int, weeks: int) -> dict:
    """Return the canonical MVP verdict for strict, complete inputs."""
    rec = _trail(trail_id)
    fitness = _strict_int(fitness, 1, 3, "fitness")
    weeks = _strict_int(weeks, 1, 52, "weeks")
    gap = rec["diff"] - fitness
    multiday = rec["diff"] > rec["grade"]
    grade = GRADE_WORD[rec["grade"]].lower()
    inputs = [rec["name"], f"{GRADE_WORD[rec['grade']]} grade"]
    if multiday:
        inputs.append(_plural(rec["days"], "day"))
    inputs.extend([FIT_WORD[fitness], _plural(weeks, "week")])
    if gap <= 0:
        return {"status": "ready", "head": "You're ready", "plan": ["Hold your current activity level until the start.", "Do one trial hike with your pack to test gear and footwear."] + (["Practise a back-to-back weekend so consecutive days are not a surprise."] if multiday else []), "why": f"Your fitness matches this {grade} trail. Keep it up and do one trial hike with a full pack.", "inputs": inputs, "weeks": weeks, "floor": 0, "comfortable": 0}
    floor, comfortable = THRESH[gap]
    if multiday:
        reason = f"Technically {rec['name']} is a {grade} trail, but {_plural(rec['days'], 'day')} back to back are the real load for your level."
    else:
        reason = f"You are {GAP_WORD[gap]} for a {grade} trail ({rec['risk']})."
    if weeks < floor:
        return {"status": "toosoon", "head": "Too soon this time", "plan": ["Choose a lower-difficulty trail this season.", "Start regular walks and strength now, then reassess with more time."], "why": f"{reason} From your level that takes around {comfortable} weeks of preparation, well past the {weeks} you have. Pick an easier trail this season, or give it more runway. Training does not make this trip safe.", "inputs": inputs, "weeks": weeks, "floor": floor, "comfortable": comfortable}
    if weeks < comfortable:
        return {"status": "hard", "head": "Tough but doable", "plan": _plan_for(weeks, multiday), "why": f"{reason} {_plural(weeks, 'week')} clears the {floor}-week floor but sits under the {comfortable} weeks a comfortable build needs. This is a tight plan, not a safety clearance.", "inputs": inputs, "weeks": weeks, "floor": floor, "comfortable": comfortable}
    return {"status": "cond", "head": "Enough time to prepare", "plan": _plan_for(weeks, multiday), "why": f"{reason} {_plural(weeks, 'week')} is enough runway for the plan if you start now. It is not a medical or mountain-safety clearance.", "inputs": inputs, "weeks": weeks, "floor": floor, "comfortable": comfortable}


def _date(value: str | date, label: str = "date") -> date:
    if type(value) is datetime:
        raise ValueError(f"{label} must be an ISO calendar date")
    if type(value) is date:
        return value
    if type(value) is str:
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise ValueError(f"{label} must be an ISO date")


def build_plan(trail_id: str, fitness: int, start_date: str | date, trip_date: str | date) -> dict:
    start, trip = _date(start_date, "start_date"), _date(trip_date, "trip_date")
    days = (trip - start).days
    if not 7 <= days <= 364:
        raise ValueError("trip date must be 7 to 364 days after start date")
    weeks = days // 7
    assessment = assess(trail_id, fitness, weeks)
    sessions = []
    for week in range(1, weeks + 1):
        for day_number, kind in ((1, "base"), (3, "strength"), (5, "hike")):
            session_date = start + timedelta(days=(week - 1) * 7 + day_number - 1)
            if session_date >= trip or (trip - session_date).days <= 2:
                continue
            final_week = week == weeks
            phase = week / weeks
            if final_week:
                label = {"base": "Lighter easy base walk", "strength": "Lighter controlled strength and mobility", "hike": "Lighter local walk and gear check"}[kind]
            elif assessment["status"] == "toosoon":
                label = {"base": "Easy base walk", "strength": "Controlled step-ups, lunges, and core", "hike": "Easy local walk and gear check"}[kind]
            elif phase <= 0.25:
                label = {"base": "Easy aerobic walk", "strength": "Controlled step-ups, lunges, and core", "hike": "Easy local walk"}[kind]
            elif phase <= 0.7:
                label = {"base": "Easy aerobic walk", "strength": "General leg strength and core", "hike": "Terrain practice walk with controlled descents"}[kind]
            else:
                label = {"base": "Easy recovery walk", "strength": "Controlled strength maintenance", "hike": "Trail terrain and optional pack trial"}[kind]
            session_id = str(uuid.uuid5(_NAMESPACE, f"{trail_id}|{fitness}|{start.isoformat()}|{trip.isoformat()}|{week}|{day_number}"))
            sessions.append({"id": session_id, "week": week, "day": day_number, "date": session_date.isoformat(), "kind": kind, "label": label, "adapted": False})
    notes = ["Three sessions per week with rest days between sessions.", "The final week is lighter and the final two full days before the trip are rest.", "This plan supports plan progress only. It is not fitness, medical, or mountain-safety clearance."]
    if assessment["status"] == "toosoon":
        notes.append("Base-only plan. It does not progress toward the selected trip or make the trip safe.")
    elif TRAILS[trail_id]["diff"] > TRAILS[trail_id]["grade"]:
        notes.append("Optional paired walking rehearsal can be considered only when conditions and recovery allow. It is not scheduled automatically.")
    return {"version": 1, "trail_id": trail_id, "fitness": fitness, "start_date": start.isoformat(), "trip_date": trip.isoformat(), "weeks": weeks, "assessment": assessment, "sessions": sessions, "notes": notes}


def _valid_completion_ids(plan: dict, logs: list, today: date) -> set[str]:
    sessions = {s["id"]: s for s in plan.get("sessions", [])}
    completed = set()
    if type(logs) is not list:
        return completed
    for log in logs:
        if type(log) is not dict or type(log.get("session_id")) is not str or type(log.get("done_at")) is not str:
            continue
        try:
            done_at = date.fromisoformat(log["done_at"])
        except ValueError:
            continue
        if log["session_id"] in sessions and _date(sessions[log["session_id"]]["date"]) <= done_at <= today:
            completed.add(log["session_id"])
    return completed


def adapt_plan(plan: dict, logs: list, today: str | date) -> dict:
    """Repeat base work in the next week after a wholly missed completed week."""
    today_date = _date(today, "today")
    result = copy.deepcopy(plan)
    completed = _valid_completion_ids(plan, logs, today_date)
    sessions = result.get("sessions", [])
    by_week: dict[int, list[dict]] = {}
    for session in sessions:
        by_week.setdefault(session["week"], []).append(session)
    start = _date(plan["start_date"], "start_date")
    current_week = (today_date - start).days // 7 + 1
    previous = by_week.get(current_week - 1, [])
    current = by_week.get(current_week, [])
    # Only the immediately preceding full week can trigger recovery. Once the
    # user resumes this week, an old gap must not keep rewriting later sessions.
    if previous and current and not any(s["id"] in completed for s in previous + current):
        upcoming = next((s for s in current if _date(s["date"]) >= today_date), None)
        if upcoming is not None:
            upcoming["kind"] = "base"
            prefix = "Lighter repeat" if current_week == plan["weeks"] else "Repeat"
            upcoming["label"] = f"{prefix} easy base walk after a missed week"
            upcoming["adapted"] = True
    return result


def readiness(plan: dict, logs: list, today: str | date) -> dict:
    today_date = _date(today, "today")
    sessions = plan.get("sessions", [])
    completed = _valid_completion_ids(plan, logs, today_date)
    total = len(sessions)
    complete_count = sum(s["id"] in completed for s in sessions)
    due = [s for s in sessions if _date(s["date"]) < today_date]
    by_week: dict[int, list[dict]] = {}
    for s in sessions:
        by_week.setdefault(s["week"], []).append(s)
    start = _date(plan["start_date"], "start_date")
    ended_weeks = [week for week in by_week if start + timedelta(days=week * 7) <= today_date]
    streak = 0
    for week in sorted(ended_weeks, reverse=True):
        if all(s["id"] in completed for s in by_week[week]):
            streak += 1
        else:
            break
    current_week = ((_date(today, "today") - _date(plan["start_date"])).days // 7) + 1
    this_week = by_week.get(current_week, [])
    return {"score": int(complete_count * 100 / total) if total else 0, "completed": complete_count, "total": total, "on_track": all(s["id"] in completed for s in due), "streak": streak, "this_week_completed": sum(s["id"] in completed for s in this_week), "this_week_total": len(this_week), "label": "Plan progress"}


def _in_season(season: dict | None, today: date) -> bool:
    if season is None:
        return True
    marker, start, end = today.strftime("%m-%d"), season["start"], season["end"]
    return start <= marker <= end if start <= end else marker >= start or marker <= end


def discover(fitness: int, weeks: int, filters: dict | None = None, today: str | date | None = None) -> list[dict]:
    fitness, weeks = _strict_int(fitness, 1, 3, "fitness"), _strict_int(weeks, 1, 52, "weeks")
    filters = {} if filters is None else filters
    if type(filters) is not dict:
        raise ValueError("filters must be an object")
    allowed = {"region", "length", "max_grade", "hide_exposed", "in_season", "reachable"}
    if set(filters) - allowed:
        raise ValueError("unknown filter")
    if "region" in filters and filters["region"] not in ("Norway", "Iceland"):
        raise ValueError("region must be Norway or Iceland")
    if "length" in filters and filters["length"] not in ("day", "multi"):
        raise ValueError("length must be day or multi")
    if "max_grade" in filters and (type(filters["max_grade"]) is not int or not 1 <= filters["max_grade"] <= 4):
        raise ValueError("max_grade must be an integer from 1 to 4")
    for key in ("hide_exposed", "in_season", "reachable"):
        if key in filters and type(filters[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
    today_date = date.today() if today is None else _date(today, "today")
    results = []
    for trail_id, rec in TRAILS.items():
        if filters.get("region") is not None and filters["region"] != rec["region"]:
            continue
        if filters.get("length") == "day" and rec["days"] != 1:
            continue
        if filters.get("length") == "multi" and rec["days"] <= 1:
            continue
        if filters.get("max_grade") is not None and rec["grade"] > filters["max_grade"]:
            continue
        if filters.get("hide_exposed") is True and rec["exposure"]:
            continue
        if filters.get("in_season") is True and not _in_season(rec["season"], today_date):
            continue
        result = {"id": trail_id, **copy.deepcopy(rec), "assessment": assess(trail_id, fitness, weeks)}
        if filters.get("reachable") is True and result["assessment"]["status"] == "toosoon":
            continue
        results.append(result)
    return sorted(results, key=lambda r: (_STATUS_WEIGHT[r["assessment"]["status"]], r["diff"], r["km"], r["id"]))
