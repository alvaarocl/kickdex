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
    monkeypatch.setattr(update_standings, "ESPN_STANDINGS_PATH", tmp_path / "none.json")
    monkeypatch.setattr(update_standings, "ESPN_PLAYERS_PATH", tmp_path / "none.csv")

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


def test_update_standings_falls_back_to_espn_for_uncovered_leagues(tmp_path, monkeypatch):
    # Segunda no está en el plan gratuito de football-data.org: tabla y
    # goleadores salen de ESPN; la zona de cada fila viaja con el dato.
    standings_out = tmp_path / "standings.json"
    scorers_out = tmp_path / "scorers.json"
    espn = tmp_path / "espn_standings.json"
    espn.write_text(json.dumps({"leagues": {"SP2": {"competition_name": "LALIGA 2", "matchday": 8, "source": "espn",
        "table": [{"position": 1, "team": "Eibar", "played": 8, "points": 21, "zone": "promo"}]}}}), encoding="utf-8")
    players = tmp_path / "players.csv"
    players.write_text("event_id,date,league,team,player_id,player,gls,ast\n"
                       "1,2026-09-01,SP2,Tenerife,9,Enric Gallego,2,0\n"
                       "2,2026-09-08,SP2,Tenerife,9,Enric Gallego,1,1\n", encoding="utf-8")
    monkeypatch.setattr(update_standings, "STANDINGS_PATH", standings_out)
    monkeypatch.setattr(update_standings, "SCORERS_PATH", scorers_out)
    monkeypatch.setattr(update_standings, "ESPN_STANDINGS_PATH", espn)
    monkeypatch.setattr(update_standings, "ESPN_PLAYERS_PATH", players)
    monkeypatch.delenv("FOOTBALL_DATA_API_KEY", raising=False)

    update_standings.update_standings(leagues=["SP1"])

    standings = json.loads(standings_out.read_text(encoding="utf-8"))
    scorers = json.loads(scorers_out.read_text(encoding="utf-8"))
    assert standings["enabled"] is True
    assert standings["leagues"]["SP2"]["table"][0]["zone"] == "promo"
    assert scorers["leagues"]["SP2"]["scorers"][0] == {
        "rank": 1, "player": "Enric Gallego", "team": "Tenerife", "goals": 3, "assists": 1,
        "penalties": None, "played_matches": 2}
