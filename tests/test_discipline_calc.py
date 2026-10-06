from app.engine.discipline_calc import compute_discipline
from app.engine.suspensions import merge_calculated


def _row(league, date, team, pid, y=0, r=0, red_type="", ev=None):
    return {"league": league, "event_id": ev or f"{team}-{date}", "date": date, "team": team, "opponent": "X",
            "venue": "H", "player_id": pid, "player": f"P{pid}", "crdy": str(y), "crdr": str(r), "red_type": red_type}


def _season(league, team, dates, cards):
    """cards: {pid: {date: (y, r, red_type)}} — todos juegan todos los partidos."""
    rows = []
    for pid, by_date in cards.items():
        for d in dates:
            y, r, rt = by_date.get(d, (0, 0, ""))
            rows.append(_row(league, d, team, pid, y, r, rt))
    return rows


DATES = [f"2026-09-{d:02d}" for d in (1, 8, 15, 22, 29)]
UPCOMING = [{"league": "SP1", "date": "2026-10-04", "home": "Betis", "away": "Getafe"},
            {"league": "SP1", "date": "2026-10-11", "home": "Getafe", "away": "Elche"}]


def test_laliga_fifth_yellow_suspends_next_match_and_fourth_is_warning():
    rows = _season("SP1", "Betis", DATES, {
        "1": {d: (1, 0, "") for d in DATES},            # 5 amarillas → sancionado
        "2": {d: (1, 0, "") for d in DATES[:4]},        # 4 amarillas → apercibido
    })
    items = {i["player_id"]: i for i in compute_discipline(rows, UPCOMING, today="2026-10-01")}
    assert items["1"]["status"] == "suspended" and items["1"]["reason"] == "5ª amarilla"
    assert items["1"]["misses"][0]["opponent"] == "Getafe"
    assert items["2"]["status"] == "at_risk" and (items["2"]["cards"], items["2"]["threshold"]) == (4, 5)


def test_ban_is_served_once_the_team_plays_again():
    rows = _season("SP1", "Betis", DATES, {"1": {DATES[2]: (0, 1, "2y")}})
    items = {i["player_id"]: i for i in compute_discipline(rows, UPCOMING, today="2026-10-01")}
    assert items["1"]["status"] == "served"


def test_red_card_types_and_double_yellow_do_not_accumulate():
    rows = _season("SP1", "Betis", DATES, {
        "1": {DATES[-1]: (0, 1, "direct")},
        "2": {DATES[-1]: (0, 1, "2y")},
    })
    items = {i["player_id"]: i for i in compute_discipline(rows, UPCOMING, today="2026-10-01")}
    assert items["1"]["reason"] == "roja directa" and items["1"]["min_only"] is True
    assert items["2"]["reason"] == "doble amarilla" and items["2"]["cards"] == 0


def test_premier_league_five_yellow_rule_expires_after_matchweek_19():
    dates = [f"2026-{m:02d}-{d:02d}" for m in (8, 9, 10, 11, 12) for d in (1, 8, 15, 22)][:20]
    late = {d: (1, 0, "") for d in dates[15:20]}          # 5ª amarilla en el partido 20 del club
    rows = _season("E0", "Fulham", dates, {"1": late})
    items = [i for i in compute_discipline(rows, [], today="2027-01-01") if i["player_id"] == "1"]
    assert not items or items[0]["status"] != "suspended"


def test_ligue1_three_yellows_within_ten_matches():
    rows = _season("F1", "Lens", DATES, {"1": {DATES[0]: (1, 0, ""), DATES[2]: (1, 0, ""), DATES[4]: (1, 0, "")},
                                          "2": {DATES[1]: (1, 0, ""), DATES[3]: (1, 0, "")}})
    items = {i["player_id"]: i for i in compute_discipline(rows, [], today="2026-10-01")}
    assert items["1"]["status"] == "suspended"
    assert items["2"]["status"] == "at_risk"


def test_stale_official_suspension_is_dropped_when_already_served():
    official = [{"player": "Tim Kleindienst", "team": "M'gladbach", "league": "D1", "status": "suspended",
                 "official": True}]
    calculated = [{"player": "Tim Kleindienst", "team": "M'gladbach", "league": "D1", "status": "served"},
                  {"player": "Other", "team": "Bayern", "league": "D1", "status": "at_risk", "cards": 4}]
    merged = merge_calculated(official, calculated, {"D1": {"name": "Bundesliga"}})
    assert [m["player"] for m in merged] == ["Other"]
