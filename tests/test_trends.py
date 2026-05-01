import pandas as pd

from app.engine.trends import detect_team_trends, build_trends_payload


def _df(rows):
    data = pd.DataFrame(rows)
    data["Date"] = pd.to_datetime(data["Date"])
    return data


MATCHES = _df([
    {"Date": "2026-01-01", "HomeTeam": "A", "AwayTeam": "B", "FTHG": 2, "FTAG": 1, "HC": 5, "AC": 4, "HY": 2, "AY": 2},
    {"Date": "2026-01-08", "HomeTeam": "C", "AwayTeam": "A", "FTHG": 1, "FTAG": 2, "HC": 4, "AC": 5, "HY": 1, "AY": 3},
    {"Date": "2026-01-15", "HomeTeam": "A", "AwayTeam": "D", "FTHG": 3, "FTAG": 1, "HC": 6, "AC": 3, "HY": 2, "AY": 2},
    {"Date": "2026-01-22", "HomeTeam": "E", "AwayTeam": "A", "FTHG": 1, "FTAG": 1, "HC": 3, "AC": 5, "HY": 2, "AY": 1},
    {"Date": "2026-01-29", "HomeTeam": "A", "AwayTeam": "F", "FTHG": 2, "FTAG": 0, "HC": 7, "AC": 2, "HY": 2, "AY": 2},
    {"Date": "2026-02-05", "HomeTeam": "G", "AwayTeam": "A", "FTHG": 2, "FTAG": 2, "HC": 5, "AC": 4, "HY": 3, "AY": 1},
    {"Date": "2026-02-12", "HomeTeam": "A", "AwayTeam": "H", "FTHG": 1, "FTAG": 0, "HC": 5, "AC": 3, "HY": 1, "AY": 2},
    {"Date": "2026-02-19", "HomeTeam": "A", "AwayTeam": "I", "FTHG": 2, "FTAG": 2, "HC": 6, "AC": 4, "HY": 2, "AY": 2},
])


def test_detect_team_trends_finds_scoring_run():
    trends = detect_team_trends(MATCHES, "A", "all")
    texts = [trend["text"] for trend in trends]
    assert any("marca +0.5 goles" in text for text in texts)
    assert any(trend["key"] == "scored_1" and trend["hits"] == trend["window"] for trend in trends)


def test_detect_team_trends_respects_venue():
    trends = detect_team_trends(MATCHES, "A", "home")
    assert trends
    assert all(trend["venue"] == "home" for trend in trends)


def test_build_trends_payload_shape():
    payload = build_trends_payload(MATCHES, ["A", "B"], season_start="2026-01-01")
    assert "teams" in payload
    assert set(payload["teams"]["A"].keys()) == {"all", "home", "away"}
