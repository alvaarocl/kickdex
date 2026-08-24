"""Fail CI only for broken essential static contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import CURRENT_SEASON_LABEL, LEAGUES


DATA_DIR = ROOT / "docs" / "data"


def read_json(name: str):
    path = DATA_DIR / name
    if not path.exists():
        raise AssertionError(f"missing {name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AssertionError(f"invalid {name}: {exc}") from exc


def validate(require_calendar: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        meta = read_json("meta.json")
        leagues = read_json("leagues.json")
        fixtures = read_json("fixtures.json")
        teams = read_json("teams.json")
        health = read_json("data_health.json")
        team_assets = read_json("team_assets.json")
        player_assets = read_json("player_assets.json")
    except AssertionError as exc:
        return [str(exc)]

    if meta.get("season") != CURRENT_SEASON_LABEL:
        errors.append(f"meta season={meta.get('season')!r}, expected={CURRENT_SEASON_LABEL!r}")
    if (fixtures.get("meta") or {}).get("season") != CURRENT_SEASON_LABEL:
        errors.append("fixtures season does not match current season")
    if health.get("season") != CURRENT_SEASON_LABEL:
        errors.append("data_health season does not match current season")
    missing_leagues = sorted(set(LEAGUES) - set(leagues))
    if missing_leagues:
        errors.append(f"missing leagues: {','.join(missing_leagues)}")
    incomplete_rosters = sorted(
        code for code in LEAGUES if (leagues.get(code) or {}).get("roster_status") != "complete"
    )
    if incomplete_rosters:
        errors.append(f"incomplete rosters: {','.join(incomplete_rosters)}")
    if not isinstance(teams, list) or not teams:
        errors.append("teams.json must be a non-empty list")
    roster_teams = {team for info in leagues.values() for team in info.get("teams") or []}
    missing_search_teams = sorted(roster_teams - set(teams))
    if missing_search_teams:
        errors.append(f"teams.json misses roster clubs: {','.join(missing_search_teams)}")
    current_team_count = sum(len(info.get("teams") or []) for info in leagues.values())
    if current_team_count != len(set(team for info in leagues.values() for team in info.get("teams") or [])):
        errors.append("the same canonical team appears in more than one current league")
    fixture_count = len(fixtures.get("recent") or []) + len(fixtures.get("upcoming") or [])
    if require_calendar and fixture_count == 0:
        errors.append("calendar is empty")
    complete_calendar = fixtures.get("calendar")
    if not isinstance(complete_calendar, list) or not complete_calendar:
        errors.append("fixtures.json must expose a non-empty complete calendar")
    else:
        fixture_sources = ((fixtures.get("meta") or {}).get("fixture_download") or {}).get("leagues") or {}
        for code, source_info in fixture_sources.items():
            if not isinstance(source_info, dict) or not source_info.get("ok"):
                continue
            league_calendar = [item for item in complete_calendar if item.get("league") == code]
            source_total = int(source_info.get("total") or 0)
            if source_total and len(league_calendar) != source_total:
                errors.append(
                    f"{code} complete calendar has {len(league_calendar)} matches, expected {source_total}"
                )
            pair_counts: dict[tuple[str, str], int] = {}
            for item in league_calendar:
                pair = tuple(sorted((str(item.get("home") or ""), str(item.get("away") or ""))))
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
            invalid_pairs = [pair for pair, count in pair_counts.items() if count != 2]
            if invalid_pairs:
                errors.append(f"{code} calendar has invalid home/away pair counts")
    if not isinstance((team_assets.get("teams") or {}), dict):
        errors.append("team_assets.json has an invalid contract")
    if not isinstance((player_assets.get("players") or {}), dict):
        errors.append("player_assets.json has an invalid contract")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-calendar", action="store_true")
    args = parser.parse_args()
    errors = validate(require_calendar=args.require_calendar)
    if errors:
        print("STATIC DATA VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"STATIC DATA OK season={CURRENT_SEASON_LABEL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
