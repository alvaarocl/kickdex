"""
Check player-data coverage for the static frontend.

Uses docs/data/player_coverage.json when available, otherwise compares
docs/data/players.json with docs/data/leagues.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"


def _read_json(name: str, default):
    path = DATA_DIR / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _coverage_from_static_json() -> dict:
    players = _read_json("players.json", {})
    leagues = _read_json("leagues.json", {})
    covered_teams = set(players.keys()) if isinstance(players, dict) else set()
    by_league = {}

    for code, info in leagues.items():
        teams = set(info.get("teams", []))
        matched = teams & covered_teams
        by_league[code] = {
            "name": info.get("name", code),
            "teams_with_players": len(matched),
            "expected_teams": len(teams),
            "coverage_rate": round(len(matched) / len(teams), 3) if teams else None,
            "missing_teams": sorted(teams - covered_teams),
            "player_rows": sum(len(players.get(team, [])) for team in matched),
        }

    return {
        "total_teams_with_players": len(covered_teams),
        "total_player_rows": sum(len(v) for v in players.values()) if isinstance(players, dict) else 0,
        "by_league": by_league,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-under", type=float, default=None, help="Fail if any league coverage is below this rate.")
    parser.add_argument(
        "--required-leagues",
        nargs="*",
        default=None,
        help="Optional league codes that must be present and pass --fail-under.",
    )
    args = parser.parse_args()

    coverage = _read_json("player_coverage.json", None) or _coverage_from_static_json()
    print("PLAYER COVERAGE")
    print(f"teams_with_players={coverage.get('total_teams_with_players', 0)}")
    print(f"player_rows={coverage.get('total_player_rows', 0)}")

    failed = False
    by_league = coverage.get("by_league") or {}
    required = set(args.required_leagues or by_league.keys())

    for code, info in sorted(by_league.items()):
        rate = info.get("coverage_rate")
        rate_text = "n/a" if rate is None else f"{rate:.1%}"
        print(
            f"{code:>3} {info.get('name', code):<24} "
            f"{info.get('teams_with_players', 0):>2}/{info.get('expected_teams', 0):<2} teams "
            f"{rate_text:>6} rows={info.get('player_rows', 0)}"
        )
        if code in required and args.fail_under is not None and (rate is None or rate < args.fail_under):
            failed = True

    missing_required = sorted(required - set(by_league))
    if missing_required:
        print(f"missing_required_leagues={','.join(missing_required)}")
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
