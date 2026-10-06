import requests

from scripts.update_worldsoccerdata_referee_data import (
    _parse_cards, _parse_match_log, _parse_referee_links, _request, fetch_league,
)


def test_parse_worldsoccerdata_referee_links():
    html = """
    <table class="stat-time">
      <tr><th>Referee</th><th>Total Matches</th></tr>
      <tr>
        <td><a class="ref-link" href="/stats/germany/bundesliga/referees/test-ref">Test Ref</a></td>
        <td>16</td>
      </tr>
      <tr>
        <td><a class="ref-link" href="/stats/germany/bundesliga/referees/test-ref">Test Ref</a></td>
        <td>9</td>
      </tr>
    </table>
    """

    assert _parse_referee_links(html) == [
        {
            "referee": "Test Ref",
            "href": "https://www.worldsoccerdata.com/stats/germany/bundesliga/referees/test-ref",
            "matches": 16,
        }
    ]


def test_parse_worldsoccerdata_markdown_referee_links():
    markdown = """
    | Referee | Total Games | Avg Goals |
    | --- | --- | --- |
    | [Test Ref](https://www.worldsoccerdata.com/stats/spain/laliga/referees/test-ref) | 10 | 2.4 |
    | [Test Ref](https://www.worldsoccerdata.com/stats/spain/laliga/referees/test-ref) | 8 | 2.1 |
    """

    assert _parse_referee_links(markdown) == [
        {
            "referee": "Test Ref",
            "href": "https://www.worldsoccerdata.com/stats/spain/laliga/referees/test-ref",
            "matches": 10,
        }
    ]


def test_parse_worldsoccerdata_cards():
    html = """
    <section>
      <h4>Cards (avg)</h4>
      <div>4.13 YC · 0.19 RC</div>
      <p>Totals: 66Y / 3R</p>
    </section>
    """

    assert _parse_cards(html) == (66, 3)


def test_parse_worldsoccerdata_markdown_cards():
    markdown = """
    #### Cards (avg)

    4.79 YC · 0.26 RC

    Totals: 91Y / 5R
    """

    assert _parse_cards(markdown) == (91, 5)


def test_fetch_league_combines_list_and_profile(monkeypatch):
    list_html = """
    <table class="stat-time">
      <tr><th>Referee</th><th>Total Matches</th></tr>
      <tr>
        <td><a class="ref-link" href="/stats/spain/laliga/referees/test-ref">Test Ref</a></td>
        <td>10</td>
      </tr>
    </table>
    """
    profile_html = "<h4>Cards (avg)</h4><span>5.2 YC · 0.3 RC</span><p>Totals: 52Y / 3R</p>"

    def fake_request(url, timeout):
        return profile_html if "test-ref" in url else list_html

    monkeypatch.setattr("scripts.update_worldsoccerdata_referee_data._request", fake_request)

    rows, matches, refreshed = fetch_league("SP1", "spain/laliga", season=2025, timeout=1, sleep_seconds=0, concurrency=1)
    assert refreshed == {"Test Ref"}

    assert rows == [
        {
            "league": "SP1",
            "league_name": "La Liga",
            "referee": "Test Ref",
            "matches": 10,
            "yellow_cards": 52,
            "second_yellow_cards": 0,
            "red_cards": 3,
            "source": "worldsoccerdata",
            "updated_at": rows[0]["updated_at"],
        }
    ]


def test_request_falls_back_to_reader_on_forbidden(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code} error")

    def fake_get(url, headers, timeout):
        calls.append(url)
        if len(calls) == 1:
            return FakeResponse(403, "")
        return FakeResponse(200, "reader ok")

    monkeypatch.setattr("scripts.update_worldsoccerdata_referee_data.requests.get", fake_get)

    assert _request("https://www.worldsoccerdata.com/stats/spain/laliga/referees/2025", timeout=1) == "reader ok"
    assert calls[1] == "https://r.jina.ai/https://www.worldsoccerdata.com/stats/spain/laliga/referees/2025"


def test_request_retries_reader_rate_limit(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code} error")

    def fake_get(url, headers, timeout):
        calls.append(url)
        if len(calls) == 1:
            return FakeResponse(403, "")
        if len(calls) == 2:
            return FakeResponse(429, "")
        return FakeResponse(200, "reader ok")

    monkeypatch.setattr("scripts.update_worldsoccerdata_referee_data.requests.get", fake_get)
    monkeypatch.setattr("scripts.update_worldsoccerdata_referee_data.time.sleep", lambda seconds: None)

    assert _request("https://www.worldsoccerdata.com/stats/spain/laliga/referees/2025", timeout=1) == "reader ok"
    assert len(calls) == 3


def test_request_falls_back_to_reader_on_mod_security_406(monkeypatch):
    # Desde 2026-08 el WAF responde 406 a los runners; antes eso abortaba la liga.
    calls = []

    class FakeResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code} error")

    def fake_get(url, headers, timeout):
        calls.append(url)
        return FakeResponse(406, "") if len(calls) == 1 else FakeResponse(200, "reader ok")

    monkeypatch.setattr("scripts.update_worldsoccerdata_referee_data.requests.get", fake_get)
    assert _request("https://www.worldsoccerdata.com/x", timeout=1) == "reader ok"


PROFILE_MD = """
#### Cards (avg)

4.2 YC · 0.6 RC

Totals: 9Y / 1R

### Matches 2026-2027

| Date | Match | FT (HT) | BTTS | Over 2.5 | Over 1.5 HT | HT/FT | Cards |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20 Sep 2026 | [Atletico Madrid vs Real Madrid](http://www.worldsoccerdata.com/m/1) | 2-1 (0-0) | ✓ | ✓ | – | X/1 | 4 1 |
| 17 Sep 2026 | [Malaga vs Villarreal](http://www.worldsoccerdata.com/m/2) | 1-3 (1-2) | ✓ | ✓ | ✓ | 2/2 | 5 0 |

| [Atletico Madrid](http://www.worldsoccerdata.com/t/1) | 1 |

### Matches 2025-2026

| 17 May 2026 | [Osasuna vs Espanyol](http://www.worldsoccerdata.com/m/3) | 1-2 (0-1) | ✓ | ✓ | – | 2/2 | 3 0 |
"""


def test_parse_match_log_reads_every_season_table():
    log = _parse_match_log(PROFILE_MD)
    assert [m["season"] for m in log] == [2026, 2026, 2025]
    assert log[0] == {"date": "2026-09-20", "home": "Atletico Madrid", "away": "Real Madrid",
                      "home_score": 2, "away_score": 1, "yellow_cards": 4, "red_cards": 1, "season": 2026}


def test_fetch_league_is_incremental(monkeypatch):
    list_md = (
        "| [Same Ref](https://www.worldsoccerdata.com/stats/spain/laliga/referees/same) | 2 | 4.0 |\n"
        "| [New Ref](https://www.worldsoccerdata.com/stats/spain/laliga/referees/new) | 2 | 4.0 |\n"
    )
    fetched = []

    def fake_request(url, timeout):
        fetched.append(url)
        return PROFILE_MD if "/referees/new" in url or "/referees/same" in url else list_md

    monkeypatch.setattr("scripts.update_worldsoccerdata_referee_data._request", fake_request)
    prev = {"Same Ref": {"league": "SP1", "referee": "Same Ref", "matches": "2", "yellow_cards": "8"}}
    rows, matches, refreshed = fetch_league(
        "SP1", "spain/laliga", season=2026, timeout=1, sleep_seconds=0, concurrency=1,
        existing_season=prev, existing_logged={"Same Ref": 2},
    )
    assert refreshed == {"New Ref"}
    assert not any("/referees/same" in u for u in fetched)  # no se vuelve a descargar
    new = next(r for r in rows if r["referee"] == "New Ref")
    # Totales desde el registro partido a partido de esta temporada (4+5 / 1+0).
    assert (new["yellow_cards"], new["red_cards"]) == (9, 1)
    assert len(matches) == 3


def test_parse_match_log_from_direct_html():
    html = """<html><body>
    <h3>Matches 2026-2027</h3>
    <table><tr><th>Date</th><th>Match</th><th>FT (HT)</th><th>BTTS</th><th>Cards</th></tr>
    <tr><td>20 Sep 2026</td><td><a href="/m/1">Atletico Madrid vs Real Madrid</a></td><td>2-1 (0-0)</td><td>✓</td><td>4 1</td></tr>
    </table></body></html>"""
    assert _parse_match_log(html) == [{"date": "2026-09-20", "home": "Atletico Madrid", "away": "Real Madrid",
                                       "home_score": 2, "away_score": 1, "yellow_cards": 4, "red_cards": 1,
                                       "season": 2026}]
