"""Compile the static browser lookup catalog from the one Python policy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import assess
from .trails import TRAILS

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "web" / "public" / "catalog.json"


def compile_catalog() -> dict:
    weeks = list(range(1, 53))
    trails = []
    for trail_id in sorted(TRAILS):
        record = {"id": trail_id, **TRAILS[trail_id]}
        record["assessments"] = {
            str(fitness): {str(week): assess(trail_id, fitness, week) for week in weeks}
            for fitness in (1, 2, 3)
        }
        trails.append(record)
    return {"schema_version": 1, "weeks": weeks, "trails": trails}


def _serialized() -> str:
    return json.dumps(compile_catalog(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = _serialized()
    if args.write:
        CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CATALOG_PATH.write_text(expected, encoding="utf-8")
        return 0
    return 0 if CATALOG_PATH.exists() and CATALOG_PATH.read_text(encoding="utf-8") == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
