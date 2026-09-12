import json
from pathlib import Path

from beready.catalog import compile_catalog
from beready.trails import TRAILS


def test_all_trails_have_complete_review_pending_content():
    assert len(TRAILS) == 9
    for trail_id, trail in TRAILS.items():
        assert trail_id == trail_id.lower()
        assert trail["content"]["review_status"] == "review pending"
        assert len(trail["sources"]) >= 1
        assert isinstance(trail["exposure"], bool)
        assert "season" in trail and "season_note" in trail
        assert trail["latitude"] and trail["longitude"]
        for level in ("1", "2", "3"):
            assert trail["content"]["challenges"][level]


def test_streamlit_quick_check_contains_only_catalog_lookup_policy():
    source = (Path(__file__).parents[1] / "app.py").read_text()
    assert "function verdict" not in source
    assert "const THRESH" not in source
    assert "function planFor" not in source


def test_catalog_is_complete_and_matches_compiler():
    catalog_path = Path(__file__).parents[1] / "web/public/catalog.json"
    catalog = json.loads(catalog_path.read_text())
    assert catalog == compile_catalog()
    assert catalog["schema_version"] == 1
    assert catalog["weeks"] == list(range(1, 53))
    assert len(catalog["trails"]) == 9
    for trail in catalog["trails"]:
        assert set(trail["assessments"]) == {"1", "2", "3"}
        assert set(trail["assessments"]["1"]) == {str(i) for i in range(1, 53)}
