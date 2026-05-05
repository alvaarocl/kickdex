from app.engine.suspensions import build_suspensions_payload, normalise_suspension_rows
from scripts.update_suspensions import parse_bundesliga_article, parse_premierleague_article


def test_suspensions_payload_groups_official_rows_by_team_and_league():
    leagues = {"SP1": {"name": "La Liga", "teams": ["Betis"]}}
    rows = [
        {
            "team": "Betis",
            "player": "Example Player",
            "status": "apercibido",
            "cards": "4",
            "threshold": "5",
            "source_name": "RFEF",
            "source_url": "https://rfef.es/example.pdf",
            "official": "true",
        }
    ]

    payload = build_suspensions_payload(rows, leagues)

    assert payload["status"] == "ok"
    assert payload["totals"]["at_risk"] == 1
    assert payload["totals"]["official"] == 1
    assert payload["by_team"]["Betis"]["at_risk"][0]["status_label"] == "A una amarilla"
    assert payload["by_league"]["SP1"]["name"] == "La Liga"


def test_suspensions_payload_keeps_suspended_separate_from_at_risk():
    rows = [
        {"league": "E0", "team": "Arsenal", "player": "Banned Player", "status": "suspended", "verified": "1"},
        {"league": "E0", "team": "Arsenal", "player": "Warned Player", "status": "at_risk", "verified": "1"},
    ]

    payload = build_suspensions_payload(rows, {"E0": {"name": "Premier League", "teams": ["Arsenal"]}})

    assert [item["player"] for item in payload["by_team"]["Arsenal"]["suspended"]] == ["Banned Player"]
    assert [item["player"] for item in payload["by_team"]["Arsenal"]["at_risk"]] == ["Warned Player"]


def test_suspensions_rejects_incomplete_or_unknown_status_rows():
    rows = [
        {"team": "Betis", "player": "No Status", "status": ""},
        {"team": "Betis", "player": "", "status": "at_risk"},
        {"team": "Betis", "player": "Stat Risk Only", "status": "risk"},
    ]

    assert normalise_suspension_rows(rows, {}) == []


def test_parse_premierleague_article_suspended_table_text():
    html = """
    <h6>Players suspended</h6>
    <p>Player Club Position Suspended for</p>
    <p>Martinez MUN DEF GW35</p>
    <h6>Ineligible players</h6>
    <p>Grealish EVE MCI GW35</p>
    """

    rows = parse_premierleague_article(html, {"league": "E0", "name": "Premier League", "url": "https://example.com", "official": True})

    assert rows == [{
        "league": "E0",
        "source_name": "Premier League",
        "source_url": "https://example.com",
        "official": True,
        "verified": True,
        "player": "Martinez",
        "team": "Man United",
        "status": "suspended",
        "matchday": "GW35",
    }]


def test_parse_bundesliga_article_suspended_and_at_risk_sections():
    html = """
    <p>Players suspended for Bundesliga Matchday 32</p>
    <p>Ritsu Dōan (Eintracht Frankfurt) – Five yellow cards – Suspension of one game</p>
    <p>Players on nine yellow cards who will miss the next game if booked</p>
    <p>Dominik Kohr (Mainz)</p>
    <p>Players on four yellow cards who will miss the next game if booked</p>
    <p>Leon Goretzka (Bayern Munich)</p>
    <p>Get the latest probable line-ups here</p>
    """

    rows = parse_bundesliga_article(html, {"league": "D1", "name": "Bundesliga", "url": "https://example.com", "official": True})

    assert [(row["player"], row["team"], row["status"], row.get("cards"), row.get("threshold")) for row in rows] == [
        ("Ritsu Dōan", "Ein Frankfurt", "suspended", None, None),
        ("Dominik Kohr", "Mainz", "at_risk", 9, 10),
        ("Leon Goretzka", "Bayern Munich", "at_risk", 4, 5),
    ]
