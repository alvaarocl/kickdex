from scripts.update_statbunker_referee_data import fetch_league


def test_fetch_league_parses_statbunker_referee_table(monkeypatch):
    html = """
    <table>
      <thead>
        <tr>
          <th>Referee</th><th>P</th><th>Yellow Card</th>
          <th>Red and Yellow Card</th><th>Red Card</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Test Ref</td><td>10</td><td>52</td><td>2</td><td>1</td></tr>
        <tr><td></td><td>234</td><td>988</td><td>25</td><td>43</td></tr>
      </tbody>
    </table>
    """
    monkeypatch.setattr("scripts.update_statbunker_referee_data._download_html", lambda comp_id, timeout: html)

    rows = fetch_league("SP1", 777, timeout=1)

    assert rows == [
        {
            "league": "SP1",
            "league_name": "La Liga",
            "referee": "Test Ref",
            "matches": 10,
            "yellow_cards": 52,
            "second_yellow_cards": 2,
            "red_cards": 1,
            "source": "statbunker",
            "updated_at": rows[0]["updated_at"],
        }
    ]
