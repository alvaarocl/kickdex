import json

from app.data.assets import build_player_assets, build_team_assets
from app.data.health import build_data_health
from scripts import build_data
from scripts.build_data import build_player_coverage

import pandas as pd


def test_asset_manifests_have_stable_fallbacks():
    teams = build_team_assets({"SP1": {"teams": ["Real Madrid"]}})
    players = build_player_assets({"Real Madrid": [{"player": "Kylian Mbappe"}]})

    assert teams["teams"]["Real Madrid"]["initials"] == "RM"
    assert teams["teams"]["Real Madrid"]["crest"] is None
    assert players["players"]["Real Madrid::Kylian Mbappe"]["initials"] == "KM"
    assert players["players"]["Real Madrid::Kylian Mbappe"]["photo"] is None


def test_data_health_marks_partial_enrichments_without_hiding_calendar():
    payload = build_data_health(
        {"updated_at": "2026-08-23T00:00:00Z"},
        {
            "recent": [],
            "upcoming": [{"home": "A", "away": "B"}],
            "meta": {"updated_at": "2026-08-23T00:00:00Z", "fixture_download": {"leagues": {}}},
        },
        {
            "updated_at": "2026-08-23T00:00:00Z",
            "total_player_rows": 10,
            "by_league": {"SP1": {"coverage_rate": 0.8}},
        },
        [{"name": "Ref"}],
        {"items": [], "updated_at": "2026-08-23T00:00:00Z"},
        {"SP1": {"teams": ["A", "B"], "expected_teams": 2}},
    )

    from app.config import CURRENT_SEASON_LABEL
    assert payload["season"] == CURRENT_SEASON_LABEL
    assert payload["domains"]["calendar"]["status"] == "fresh"
    assert payload["domains"]["players"]["status"] == "partial"
    assert payload["overall"] == "partial"


def test_player_coverage_keeps_leagues_without_player_rows_visible():
    players = pd.DataFrame([{"league": "SP1", "team": "A", "player": "One"}])
    leagues = {
        "SP1": {"name": "La Liga", "teams": ["A", "B"], "expected_teams": 2},
        "E0": {"name": "Premier League", "teams": [], "expected_teams": 20},
    }

    coverage = build_player_coverage(players, leagues)

    assert coverage["by_league"]["SP1"]["coverage_rate"] == 0.5
    assert coverage["by_league"]["E0"]["coverage_rate"] == 0.0
    assert coverage["by_league"]["E0"]["unresolved_team_slots"] == 20


def test_preserved_calendar_is_returned_for_health_checks(tmp_path, monkeypatch):
    existing = {
        "recent": [],
        "upcoming": [{"home": "A", "away": "B"}],
        "meta": {"season": "2026/27"},
    }
    (tmp_path / "fixtures.json").write_text(json.dumps(existing), encoding="utf-8")
    monkeypatch.setattr(build_data, "OUTPUT_DIR", tmp_path)

    actual = build_data.write_fixtures_json({
        "recent": [],
        "upcoming": [],
        "meta": {
            "season": "2026/27",
            "fixture_download": {"skipped": True, "leagues": {}},
        },
    })

    assert actual == existing


def test_player_json_merges_per_team_instead_of_freezing(tmp_path, monkeypatch):
    # Antes: 96 equipos frescos < 109 viejos (con descendidos) → se descartaba todo.
    monkeypatch.setattr(build_data, "OUTPUT_DIR", tmp_path)
    old = {f"T{i}": [{"player": "old"}] for i in range(5)}
    old["Relegated"] = [{"player": "gone"}]
    (tmp_path / "players.json").write_text(json.dumps(old), encoding="utf-8")
    fresh = {"T0": [{"player": "new", "mp": 7}], "T1": [{"player": "new"}]}

    build_data.write_player_json(fresh, "players.json", current_teams={f"T{i}" for i in range(5)})
    out = json.loads((tmp_path / "players.json").read_text(encoding="utf-8"))

    assert out["T0"] == [{"player": "new", "mp": 7}]   # fresco manda
    assert out["T4"] == [{"player": "old"}]            # equipo actual sin scrape: se conserva
    assert "Relegated" not in out                      # fuera de la temporada: se retira


def test_player_json_keeps_existing_when_scrape_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(build_data, "OUTPUT_DIR", tmp_path)
    (tmp_path / "players.json").write_text(json.dumps({"A": []}), encoding="utf-8")
    build_data.write_player_json({}, "players.json", current_teams={"A"})
    assert json.loads((tmp_path / "players.json").read_text(encoding="utf-8")) == {"A": []}
