import json

from scripts import update_live_scores


def test_update_live_scores_without_key_writes_disabled_contract(tmp_path, monkeypatch):
    out = tmp_path / "live_scores.json"
    monkeypatch.setattr(update_live_scores, "OUT_PATH", out)
    monkeypatch.delenv("FOOTBALL_DATA_API_KEY", raising=False)

    contract = update_live_scores.update_live_scores(leagues=["SP1"])

    assert contract["enabled"] is False
    assert contract["matches"] == []
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk["enabled"] is False
    assert on_disk["source"] == "football-data.org"


def test_normalise_match_maps_in_play_status_and_score():
    raw = {
        "homeTeam": {"name": "Real Madrid CF"},
        "awayTeam": {"name": "FC Barcelona"},
        "status": "IN_PLAY",
        "minute": 63,
        "utcDate": "2026-08-27T18:00:00Z",
        "score": {"fullTime": {"home": 1, "away": 2}},
    }

    row = update_live_scores._normalise_match(raw, "SP1")

    assert row["league"] == "SP1"
    # football-data.org da nombres legales ("Real Madrid CF") — deben
    # normalizarse a los nombres cortos que usa el resto del motor.
    assert row["home"] == "Real Madrid"
    assert row["away"] == "Barcelona"
    assert row["status"] == "live"
    assert row["minute"] == 63
    assert row["home_score"] == 1
    assert row["away_score"] == 2


def test_normalise_match_does_not_confuse_espanyol_with_barcelona():
    # Bug real: un fuzzy-match generico mapeaba "RCD Espanyol de Barcelona"
    # a "Barcelona" porque termina literalmente en "de Barcelona".
    raw = {
        "homeTeam": {"name": "RCD Espanyol de Barcelona"},
        "awayTeam": {"name": "Getafe CF"},
        "status": "SCHEDULED",
        "utcDate": "2026-08-27T18:00:00Z",
        "score": {"fullTime": {"home": None, "away": None}},
    }
    row = update_live_scores._normalise_match(raw, "SP1")
    assert row["home"] == "Espanol"
    assert row["away"] == "Getafe"


def test_normalise_match_returns_none_without_team_names():
    assert update_live_scores._normalise_match({"status": "SCHEDULED"}, "SP1") is None


def test_fetch_live_scores_skips_uncovered_league_and_continues_on_error(monkeypatch):
    calls = []

    def fake_request(path, key, timeout=20):
        calls.append(path)
        if "PL" in path:
            raise RuntimeError("boom")
        return {
            "matches": [
                {
                    "homeTeam": {"name": "Real Madrid"},
                    "awayTeam": {"name": "Barcelona"},
                    "status": "FINISHED",
                    "score": {"fullTime": {"home": 2, "away": 1}},
                    "utcDate": "2026-08-27T18:00:00Z",
                }
            ]
        }

    monkeypatch.setattr(update_live_scores, "_request", fake_request)

    matches = update_live_scores.fetch_live_scores("test-key", ["SP1", "E0", "SP2"], sleep_seconds=0)

    # SP2 no está en FOOTBALL_DATA_ORG_COMPETITION_CODES -> nunca llama a la API.
    assert not any("SP2" in c for c in calls)
    # E0 (PL) falla pero no debe tumbar el resto.
    assert len(matches) == 1
    assert matches[0]["league"] == "SP1"
