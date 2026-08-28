import json

from scripts import update_standings


def _standings_payload():
    return {
        "competition": {"name": "Primera Division"},
        "season": {"startDate": "2026-08-16", "endDate": "2027-05-30", "currentMatchday": 3},
        "standings": [
            {
                "type": "TOTAL",
                "table": [
                    {
                        "position": 1,
                        "team": {"name": "FC Barcelona"},
                        "playedGames": 2,
                        "won": 2,
                        "draw": 0,
                        "lost": 0,
                        "goalsFor": 7,
                        "goalsAgainst": 0,
                        "goalDifference": 7,
                        "points": 6,
                    },
                    {
                        "position": 2,
                        "team": {"name": "RCD Espanyol de Barcelona"},
                        "playedGames": 2,
                        "won": 1,
                        "draw": 0,
                        "lost": 1,
                        "goalsFor": 3,
                        "goalsAgainst": 2,
                        "goalDifference": 1,
                        "points": 3,
                    },
                ],
            }
        ],
    }


def _scorers_payload():
    return {
        "competition": {"name": "Primera Division"},
        "scorers": [
            {
                "player": {"name": "Raphinha"},
                "team": {"name": "FC Barcelona"},
                "goals": 3,
                "assists": None,
                "penalties": 1,
                "playedMatches": 2,
            }
        ],
    }


def test_standings_for_league_normalizes_team_names_without_collision():
    result = update_standings._standings_for_league(_standings_payload())
    teams = [row["team"] for row in result["table"]]
    assert teams == ["Barcelona", "Espanol"]
    assert result["matchday"] == 3


def test_scorers_for_league_assigns_rank_and_normalizes_team():
    result = update_standings._scorers_for_league(_scorers_payload())
    assert result["scorers"][0]["rank"] == 1
    assert result["scorers"][0]["team"] == "Barcelona"


def test_update_standings_without_key_writes_disabled_contracts(tmp_path, monkeypatch):
    standings_out = tmp_path / "standings.json"
    scorers_out = tmp_path / "scorers.json"
    monkeypatch.setattr(update_standings, "STANDINGS_PATH", standings_out)
    monkeypatch.setattr(update_standings, "SCORERS_PATH", scorers_out)
    monkeypatch.delenv("FOOTBALL_DATA_API_KEY", raising=False)

    update_standings.update_standings(leagues=["SP1"])

    standings = json.loads(standings_out.read_text(encoding="utf-8"))
    scorers = json.loads(scorers_out.read_text(encoding="utf-8"))
    assert standings["enabled"] is False
    assert scorers["enabled"] is False


def test_update_standings_writes_populated_contracts(tmp_path, monkeypatch):
    standings_out = tmp_path / "standings.json"
    scorers_out = tmp_path / "scorers.json"
    monkeypatch.setattr(update_standings, "STANDINGS_PATH", standings_out)
    monkeypatch.setattr(update_standings, "SCORERS_PATH", scorers_out)
    monkeypatch.setenv("FOOTBALL_DATA_API_KEY", "test-key")

    def fake_request(path, key, timeout=20):
        if "standings" in path:
            return _standings_payload()
        return _scorers_payload()

    monkeypatch.setattr(update_standings, "_request", fake_request)

    update_standings.update_standings(leagues=["SP1"], sleep_seconds=0)

    standings = json.loads(standings_out.read_text(encoding="utf-8"))
    scorers = json.loads(scorers_out.read_text(encoding="utf-8"))
    assert standings["enabled"] is True
    assert standings["leagues"]["SP1"]["table"][0]["team"] == "Barcelona"
    assert scorers["leagues"]["SP1"]["scorers"][0]["player"] == "Raphinha"


def test_update_standings_skips_uncovered_league(tmp_path, monkeypatch):
    standings_out = tmp_path / "standings.json"
    scorers_out = tmp_path / "scorers.json"
    monkeypatch.setattr(update_standings, "STANDINGS_PATH", standings_out)
    monkeypatch.setattr(update_standings, "SCORERS_PATH", scorers_out)
    monkeypatch.setenv("FOOTBALL_DATA_API_KEY", "test-key")

    calls = []

    def fake_request(path, key, timeout=20):
        calls.append(path)
        return _standings_payload()

    monkeypatch.setattr(update_standings, "_request", fake_request)

    update_standings.update_standings(leagues=["SP2"], sleep_seconds=0)

    assert calls == []
