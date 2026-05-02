from scripts.build_data import build_discipline_watch


def test_discipline_watch_flags_card_risk_players():
    players = {
        "Team A": [
            {"player": "Card Magnet", "min": 80, "crdy": 0.32},
            {"player": "Clean Player", "min": 85, "crdy": 0.03},
        ]
    }
    leagues = {"SP1": {"name": "La Liga", "teams": ["Team A"]}}

    payload = build_discipline_watch(players, leagues)

    assert payload["status"] == "risk_model_not_official_suspension_feed"
    assert payload["top"][0]["player"] == "Card Magnet"
    assert payload["top"][0]["risk"] == "alto"
    assert payload["top"][0]["official_suspension_status"] is False
    assert "Clean Player" not in [item["player"] for item in payload["top"]]


def test_discipline_watch_requires_meaningful_minutes():
    players = {
        "Team A": [
            {"player": "Low Minutes", "min": 12, "crdy": 0.5},
        ]
    }
    leagues = {"SP1": {"name": "La Liga", "teams": ["Team A"]}}

    payload = build_discipline_watch(players, leagues)

    assert payload["top"] == []
    assert payload["by_team"] == {}
