from app.data.assets import build_player_assets, build_team_assets
from app.data.health import build_data_health
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

    assert payload["season"] == "2026/27"
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
