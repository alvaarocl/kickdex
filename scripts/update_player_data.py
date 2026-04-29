"""
Update static player JSONs without rebuilding all match data.

This is useful when the historical football-data CSVs are unavailable locally,
but FBref/soccerdata can provide player match logs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data.loader import load_players
from app.data.player_scraper import update_players
from scripts.build_data import (
    OUTPUT_DIR,
    build_player_coverage,
    build_player_coverage_from_json,
    build_data_status,
    build_players,
    build_players_detail,
    write_json,
    write_player_json,
)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--leagues",
        nargs="*",
        default=None,
        help="Optional football-data league codes to update, e.g. SP1 E0 I1.",
    )
    parser.add_argument("--skip-scrape", action="store_true", help="Only rebuild JSON from existing datos/players CSVs.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not args.skip_scrape:
        ok = update_players(leagues=args.leagues)
        if not ok:
            print("Warning: player scrape produced no fresh rows; using existing local/player JSON data when available.")

    df_players = load_players()
    players = build_players(df_players)
    players_detail = build_players_detail(df_players)
    leagues = _read_json(OUTPUT_DIR / "leagues.json", {})

    write_player_json(players, "players.json")
    write_player_json(players_detail, "players_detail.json")

    coverage = build_player_coverage_from_json(leagues) if df_players.empty else build_player_coverage(df_players, leagues)
    write_json(coverage, "player_coverage.json")
    write_json(build_data_status(coverage, source="update_player_data"), "data_status.json")

    print(
        "Player update complete: "
        f"{coverage.get('total_teams_with_players', 0)} teams, "
        f"{coverage.get('total_player_rows', 0)} player rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
