from scripts.update_worldsoccerdata_referee_data import _parse_cards, _parse_referee_links, fetch_league


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


def test_parse_worldsoccerdata_cards():
    html = """
    <section>
      <h4>Cards (avg)</h4>
      <div>4.13 YC · 0.19 RC</div>
      <p>Totals: 66Y / 3R</p>
    </section>
    """

    assert _parse_cards(html) == (66, 3)


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

    rows = fetch_league("SP1", "spain/laliga", season=2025, timeout=1, sleep_seconds=0, concurrency=1)

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
