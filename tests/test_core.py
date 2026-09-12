from datetime import date, datetime

import pytest

from beready.core import adapt_plan, assess, build_plan, discover, readiness
from beready.trails import TRAILS


@pytest.mark.parametrize("trail_id,fitness,weeks,status,floor,comfortable", [
    ("dalsnuten", 1, 1, "ready", 0, 0),
    ("gaustatoppen", 1, 2, "toosoon", 3, 6),
    ("gaustatoppen", 1, 3, "hard", 3, 6),
    ("gaustatoppen", 1, 6, "cond", 3, 6),
    ("laugavegur", 1, 5, "toosoon", 6, 12),
    ("laugavegur", 1, 6, "hard", 6, 12),
    ("laugavegur", 1, 12, "cond", 6, 12),
    ("trolltunga", 1, 11, "toosoon", 12, 20),
    ("trolltunga", 1, 12, "hard", 12, 20),
    ("trolltunga", 1, 20, "cond", 12, 20),
    ("trolltunga", 3, 1, "toosoon", 3, 6),
    ("trolltunga", 3, 3, "hard", 3, 6),
    ("trolltunga", 3, 6, "cond", 3, 6),
])
def test_scorer_parity_boundaries(trail_id, fitness, weeks, status, floor, comfortable):
    result = assess(trail_id, fitness, weeks)
    assert result["status"] == status
    assert result["floor"] == floor
    assert result["comfortable"] == comfortable


@pytest.mark.parametrize("trail_id,fitness,weeks", [
    ("unknown", 1, 1), ("dalsnuten", True, 1), ("dalsnuten", 1.0, 1),
    ("dalsnuten", 0, 1), ("dalsnuten", 4, 1), ("dalsnuten", 1, True),
    ("dalsnuten", 1, 1.0), ("dalsnuten", 1, 0), ("dalsnuten", 1, 53),
])
def test_assess_rejects_strict_invalid_inputs(trail_id, fitness, weeks):
    with pytest.raises((ValueError, TypeError)):
        assess(trail_id, fitness, weeks)


def test_plan_is_immutable_deterministic_and_conservative():
    plan = build_plan("laugavegur", 1, "2026-06-01", "2026-06-29")
    assert plan == build_plan("laugavegur", 1, date(2026, 6, 1), date(2026, 6, 29))
    assert plan["weeks"] == 4
    assert len(plan["sessions"]) == 12
    assert all(session["day"] in (1, 3, 5) for session in plan["sessions"])
    assert all(session["date"] < plan["trip_date"] for session in plan["sessions"])
    assert all(s["label"].startswith("Lighter") for s in plan["sessions"] if s["week"] == 4)
    assert all(s["date"] not in ("2026-06-27", "2026-06-28") for s in plan["sessions"])


@pytest.mark.parametrize("start,trip", [("2026-01-01", "2026-01-07"), ("2026-01-01", "2027-01-01")])
def test_plan_requires_7_to_364_days(start, trip):
    with pytest.raises(ValueError):
        build_plan("dalsnuten", 1, start, trip)


def test_adaptation_repeats_a_fully_missed_completed_week_without_new_ids():
    plan = build_plan("dalsnuten", 1, "2026-01-05", "2026-02-02")
    adapted = adapt_plan(plan, [], "2026-01-12")
    assert adapted is not plan
    assert [s["id"] for s in adapted["sessions"]] == [s["id"] for s in plan["sessions"]]
    assert sum(s["adapted"] for s in adapted["sessions"]) == 1
    assert next(s for s in adapted["sessions"] if s["adapted"])["week"] == 2


def test_readiness_streak_ends_at_last_fully_ended_week():
    plan = build_plan("dalsnuten", 1, "2026-01-05", "2026-02-02")
    first_week = [s for s in plan["sessions"] if s["week"] == 1]
    logs = [{"session_id": s["id"], "done_at": s["date"]} for s in first_week]
    assert readiness(plan, logs, "2026-01-18")["streak"] == 1
    assert readiness(plan, logs, "2026-01-19")["streak"] == 0


def test_readiness_ignores_bad_logs_and_is_monotonic_at_fixed_today():
    plan = build_plan("dalsnuten", 1, "2026-01-05", "2026-02-02")
    first = plan["sessions"][0]["id"]
    valid = readiness(plan, [{"session_id": first, "done_at": "2026-01-06"}], "2026-01-12")
    noisy = readiness(plan, [
        {"session_id": first, "done_at": "2026-01-06"},
        {"session_id": first, "done_at": "2026-01-06"},
        {"session_id": "unknown", "done_at": "2026-01-06"},
        {"session_id": plan["sessions"][1]["id"], "done_at": "2026-01-01"},
        {"session_id": plan["sessions"][1]["id"], "done_at": "2026-02-01"},
        {"session_id": first, "done_at": "not-a-date"},
    ], "2026-01-12")
    assert noisy == valid
    assert valid["label"] == "Plan progress"
    assert valid["score"] == 8
    assert not valid["on_track"]


def test_adaptation_waits_for_calendar_week_and_adapts_one_upcoming_session_only():
    plan = build_plan("dalsnuten", 1, "2026-01-05", "2026-02-02")
    assert adapt_plan(plan, [], "2026-01-10") == plan
    adapted = adapt_plan(plan, [], "2026-01-12")
    changed = [s for s in adapted["sessions"] if s["adapted"]]
    assert len(changed) == 1
    assert changed[0]["week"] == 2 and changed[0]["kind"] == "base"
    assert changed[0]["id"] == next(s["id"] for s in plan["sessions"] if s["week"] == 2 and s["day"] == 1)
    assert plan["sessions"] != adapted["sessions"]
    assert all(not s["adapted"] for s in plan["sessions"])


@pytest.mark.parametrize("value", [datetime(2026, 1, 1), "2026-01-01T00:00:00"])
def test_dates_reject_datetimes(value):
    with pytest.raises(ValueError):
        build_plan("dalsnuten", 1, value, "2026-02-02")


def test_discovery_filters_and_deterministic_ranking():
    all_trails = discover(1, 1, today="2026-01-15")
    assert len(all_trails) == len(TRAILS)
    assert [t["id"] for t in all_trails] == [t["id"] for t in discover(1, 1, today="2026-01-15")]
    assert all(not t["exposure"] for t in discover(1, 52, {"hide_exposed": True}, "2026-07-15"))
    assert {t["id"] for t in discover(1, 52, {"in_season": True}, "2026-01-15")} == {"dalsnuten"}
    assert all(t["days"] == 1 for t in discover(1, 52, {"length": "day"}))
    assert all(t["days"] > 1 for t in discover(1, 52, {"length": "multi"}))
    assert all(t["region"] == "Iceland" for t in discover(1, 52, {"region": "Iceland"}))
    assert all(t["grade"] <= 2 for t in discover(1, 52, {"max_grade": 2}))
    assert all(t["assessment"]["status"] != "toosoon" for t in discover(1, 1, {"reachable": True}))
    assert len(discover(1, 1, {"reachable": False})) == len(TRAILS)


@pytest.mark.parametrize("filters", [
    {"region": "Sweden"}, {"length": "week"}, {"max_grade": True},
    {"hide_exposed": "yes"}, {"in_season": 1}, {"reachable": None}, {"unknown": True},
])
def test_discovery_rejects_unknown_filter_keys_and_invalid_types(filters):
    with pytest.raises(ValueError):
        discover(1, 52, filters)


def test_discovery_year_wrapped_season_and_unknown_season_are_distinct(monkeypatch):
    monkeypatch.setitem(TRAILS, "dalsnuten", {**TRAILS["dalsnuten"], "season": {"start": "11-01", "end": "02-01"}})
    assert any(t["id"] == "dalsnuten" for t in discover(1, 52, {"in_season": True}, "2026-01-15"))
    monkeypatch.setitem(TRAILS, "dalsnuten", {**TRAILS["dalsnuten"], "season": None})
    assert any(t["id"] == "dalsnuten" for t in discover(1, 52, {"in_season": True}, "2026-04-15"))
