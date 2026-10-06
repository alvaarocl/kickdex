from scripts.update_espn_referee_matches import TeamMatcher, _tokens, match_row


def _matcher():
    m = TeamMatcher.__new__(TeamMatcher)
    m.by_league = {"SP1": [(k, [_tokens(k), _tokens(d)]) for k, d in [
        ("Ath Madrid", "Atlético de Madrid"), ("Real Madrid", "Real Madrid"), ("Malaga", "Málaga CF")]],
        "D1": [("FC Koln", [_tokens("FC Koln")])]}
    return m


def test_team_matcher_maps_espn_names_to_canonical_keys():
    m = _matcher()
    assert m.match("SP1", "Atlético Madrid") == "Ath Madrid"
    assert m.match("SP1", "Málaga") == "Malaga"
    assert m.match("D1", "FC Cologne") == "FC Koln"
    assert m.match("SP1", "Unknown United") is None


def test_match_row_extracts_referee_cards_and_fouls():
    event = {"id": "1", "date": "2026-09-20T19:00Z", "competitions": [{"competitors": [
        {"homeAway": "home", "score": "2", "team": {"id": "10", "displayName": "Atlético Madrid"}},
        {"homeAway": "away", "score": "1", "team": {"id": "20", "displayName": "Real Madrid"}},
    ]}]}
    summary = {
        "gameInfo": {"officials": [{"displayName": "Jesus Gil Manzano", "position": {"name": "Referee"}, "order": 1}]},
        "boxscore": {"teams": [
            {"team": {"id": "10"}, "statistics": [{"name": "yellowCards", "displayValue": "3"},
                                                  {"name": "redCards", "displayValue": "0"},
                                                  {"name": "foulsCommitted", "displayValue": "14"}]},
            {"team": {"id": "20"}, "statistics": [{"name": "yellowCards", "displayValue": "2"},
                                                  {"name": "redCards", "displayValue": "1"},
                                                  {"name": "foulsCommitted", "displayValue": "11"}]},
        ]},
    }
    row = match_row("SP1", event, summary, _matcher())
    assert row["fixture_id"] == "espn:1"
    assert row["referee"] == "Jesus Gil Manzano"
    assert (row["home"], row["away"]) == ("Ath Madrid", "Real Madrid")
    assert (row["yellow_cards"], row["red_cards"], row["fouls"]) == (5, 1, 25)
    assert row["penalties"] == ""


def test_match_row_skips_matches_without_referee():
    event = {"id": "2", "date": "2026-09-20T19:00Z", "competitions": [{"competitors": [
        {"homeAway": "home", "team": {"id": "1"}}, {"homeAway": "away", "team": {"id": "2"}}]}]}
    assert match_row("SP1", event, {"gameInfo": {}}, _matcher()) is None


def test_cards_are_counted_from_key_events_when_available():
    # Doble amarilla: el boxscore dice 0+1 amarillas; los eventos, 2 amarillas + 1 roja.
    event = {"id": "3", "date": "2026-08-30T17:30Z", "competitions": [{"competitors": [
        {"homeAway": "home", "score": "3", "team": {"id": "1", "displayName": "Real Madrid"}},
        {"homeAway": "away", "score": "1", "team": {"id": "2", "displayName": "Málaga"}}]}]}
    summary = {
        "gameInfo": {"officials": [{"displayName": "Ref", "order": 1}]},
        "boxscore": {"teams": [
            {"team": {"id": "1"}, "statistics": [{"name": "yellowCards", "displayValue": "0"}, {"name": "redCards", "displayValue": "1"}]},
            {"team": {"id": "2"}, "statistics": [{"name": "yellowCards", "displayValue": "1"}, {"name": "redCards", "displayValue": "0"}]}]},
        "keyEvents": [{"type": {"text": "Yellow Card"}}, {"type": {"text": "Yellow Card"}},
                      {"type": {"text": "Red Card"}}, {"type": {"text": "Goal"}}],
    }
    row = match_row("SP1", event, summary, _matcher())
    assert (row["yellow_cards"], row["red_cards"]) == (2, 1)
