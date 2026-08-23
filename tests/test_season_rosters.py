import pandas as pd

from app.config import LEAGUE_TEAM_COUNTS
from app.data.season_rosters import CURRENT_SEASON_ROSTERS, all_roster_teams
from scripts.build_data import build_leagues


def test_every_configured_roster_is_complete_and_unique():
    assigned = []
    for code, expected in LEAGUE_TEAM_COUNTS.items():
        teams = CURRENT_SEASON_ROSTERS[code]["teams"]
        assert len(teams) == expected
        assert len(set(teams)) == expected
        assigned.extend(teams)

    assert len(assigned) == len(set(assigned))


def test_laliga_roster_does_not_depend_on_played_matches():
    matches = pd.DataFrame([
        {
            "Date": pd.Timestamp("2026-08-15"),
            "Div": "SP1",
            "HomeTeam": "Alaves",
            "AwayTeam": "Getafe",
        }
    ])

    laliga = build_leagues(matches, ["Alaves", "Getafe"])["SP1"]

    assert laliga["roster_status"] == "complete"
    assert laliga["observed_team_count"] == 2
    assert len(laliga["teams"]) == 20
    assert {"Barcelona", "Real Madrid", "Athletic Club"} <= set(laliga["teams"])


def test_rosters_exist_even_when_results_feed_is_empty():
    leagues = build_leagues(pd.DataFrame(), [])

    assert set(leagues) == set(LEAGUE_TEAM_COUNTS)
    assert all(info["roster_status"] == "complete" for info in leagues.values())


def test_global_roster_includes_all_laliga_clubs():
    teams = set(all_roster_teams())

    assert {"Malaga", "Santander", "Dep. A Coruna", "Osasuna"} <= teams
