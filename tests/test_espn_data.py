from scripts.update_espn_data import TeamMatcher, _tokens, match_row


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


def test_player_rows_compute_minutes_from_subs_and_red_cards():
    from scripts.update_espn_data import player_rows

    event = {"id": "9", "date": "2026-09-20T19:00Z"}

    def athlete(pid, starter=False, sub_in=False, stats=None):
        base = {"appearances": "1", "totalGoals": "0", "goalAssists": "0", "totalShots": "0", "shotsOnTarget": "0",
                "foulsCommitted": "0", "foulsSuffered": "0", "yellowCards": "0", "redCards": "0", "ownGoals": "0"}
        base.update(stats or {})
        return {"athlete": {"id": pid, "displayName": f"P{pid}"}, "starter": starter, "subbedIn": sub_in,
                "position": {"abbreviation": "F"}, "stats": [{"name": k, "displayValue": v} for k, v in base.items()]}

    summary = {
        "rosters": [
            {"homeAway": "home", "team": {"id": "10"}, "roster": [
                athlete("1", starter=True, stats={"totalGoals": "2", "totalShots": "4", "shotsOnTarget": "3"}),
                athlete("2", starter=True), athlete("3", sub_in=True),
                {"athlete": {"id": "4", "displayName": "Bench"}, "starter": False, "subbedIn": False,
                 "stats": [{"name": "appearances", "displayValue": "0"}]},
            ]},
            {"homeAway": "away", "team": {"id": "20"}, "roster": [athlete("5", starter=True, stats={"redCards": "1"})]},
        ],
        "keyEvents": [
            {"type": {"text": "Substitution"}, "clock": {"value": 3900.0, "displayValue": "65'"},
             "participants": [{"athlete": {"id": "3"}}, {"athlete": {"id": "2"}}]},
            {"type": {"text": "Red Card"}, "clock": {"value": 2400.0, "displayValue": "40'"},
             "participants": [{"athlete": {"id": "5"}}]},
        ],
    }
    rows = {r["player_id"]: r for r in player_rows("SP1", event, summary, {"10": "Real Madrid", "20": "Barcelona"}, None)}
    assert set(rows) == {"1", "2", "3", "5"}                      # el suplente sin jugar no cuenta
    assert (rows["1"]["minutes"], rows["2"]["minutes"], rows["3"]["minutes"], rows["5"]["minutes"]) == (90, 65, 25, 40)
    assert (rows["1"]["gls"], rows["1"]["sot"], rows["1"]["team"], rows["1"]["opponent"]) == (2, 3, "Real Madrid", "Barcelona")
    assert rows["5"]["venue"] == "A" and rows["5"]["crdr"] == 1


def test_build_players_from_matches_contract():
    import pandas as pd
    from scripts.build_data import build_players_detail_from_matches, build_players_from_matches

    df = pd.DataFrame([
        {"event_id": "1", "date": pd.Timestamp("2026-09-01"), "team": "PSG", "opponent": "Lyon", "venue": "H",
         "player_id": "7", "player": "Dembélé", "position": "F", "starter": 1, "minutes": 90,
         "gls": 1, "ast": 0, "sh": 4, "sot": 2, "fls": 1, "fld": 2, "crdy": 0, "crdr": 0},
        {"event_id": "2", "date": pd.Timestamp("2026-09-08"), "team": "PSG", "opponent": "Lens", "venue": "A",
         "player_id": "7", "player": "Dembélé", "position": "F", "starter": 0, "minutes": 30,
         "gls": 0, "ast": 1, "sh": 2, "sot": 1, "fls": 0, "fld": 0, "crdy": 1, "crdr": 0},
    ])
    p = build_players_from_matches(df)["PSG"][0]
    assert (p["mp"], p["starts"], p["min_total"], p["min"], p["gls_tot"], p["sot"], p["crdy_tot"]) == (2, 1, 120, 60.0, 1, 1.5, 1)
    detail = build_players_detail_from_matches(df)
    rows = detail["teams"]["PSG"]["Dembélé"]
    assert detail["columns"][:3] == ["date", "opp", "venue"]
    assert rows[0][:4] == ["2026-09-08", "Lens", "A", 30]          # más reciente primero
