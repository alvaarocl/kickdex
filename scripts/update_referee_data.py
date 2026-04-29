"""
Incremental referee updater.

Free-first strategy:
- If APIFOOTBALL_KEY is configured, fetch finished fixtures and match stats from
  API-Football's free tier and append them to datos/referees_matches.csv.
- Without a key, exit successfully so the daily data workflow keeps working.

The generated CSV is intentionally small and append-only. build_data.py merges it
with football-data.co.uk and manual fallbacks.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import APIFOOTBALL_LEAGUE_IDS, CURRENT_SEASON_START, DATA_DIR, LEAGUES
from app.data.loader import normalize_team_name

API_BASE = "https://v3.football.api-sports.io"
OUT_PATH = Path(DATA_DIR) / "referees_matches.csv"
FIELDNAMES = [
    "fixture_id",
    "date",
    "league",
    "league_name",
    "referee",
    "home",
    "away",
    "home_score",
    "away_score",
    "yellow_cards",
    "red_cards",
    "fouls",
    "penalties",
    "source",
    "updated_at",
]


def _request(path: str, params: dict[str, Any], key: str, timeout: int = 25) -> dict[str, Any]:
    res = requests.get(
        f"{API_BASE}{path}",
        params=params,
        headers={"x-apisports-key": key},
        timeout=timeout,
    )
    res.raise_for_status()
    payload = res.json()
    if payload.get("errors"):
        raise RuntimeError(f"API-Football error on {path}: {payload['errors']}")
    return payload


def _stat_value(stats: list[dict[str, Any]], stat_type: str) -> int:
    total = 0
    for team_stats in stats or []:
        for item in team_stats.get("statistics") or []:
            if str(item.get("type", "")).lower() == stat_type.lower():
                value = item.get("value")
                if isinstance(value, str) and value.endswith("%"):
                    continue
                try:
                    total += int(value or 0)
                except (TypeError, ValueError):
                    pass
    return total


def _load_existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row["fixture_id"] for row in csv.DictReader(fh) if row.get("fixture_id")}


def _append_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def _fixture_row(fixture: dict[str, Any], stats: list[dict[str, Any]], league_code: str) -> dict[str, Any] | None:
    fx = fixture.get("fixture") or {}
    referee = (fx.get("referee") or "").strip()
    if not referee:
        return None

    teams = fixture.get("teams") or {}
    goals = fixture.get("goals") or {}
    fixture_id = fx.get("id")
    if not fixture_id:
        return None

    return {
        "fixture_id": str(fixture_id),
        "date": str(fx.get("date") or "")[:10],
        "league": league_code,
        "league_name": LEAGUES.get(league_code, league_code),
        "referee": referee,
        "home": normalize_team_name((teams.get("home") or {}).get("name") or ""),
        "away": normalize_team_name((teams.get("away") or {}).get("name") or ""),
        "home_score": goals.get("home") if goals.get("home") is not None else "",
        "away_score": goals.get("away") if goals.get("away") is not None else "",
        "yellow_cards": _stat_value(stats, "Yellow Cards"),
        "red_cards": _stat_value(stats, "Red Cards"),
        "fouls": _stat_value(stats, "Fouls"),
        "penalties": _stat_value(stats, "Penalty") + _stat_value(stats, "Penalties"),
        "source": "api-football",
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def update_referees(days_back: int, leagues: list[str], sleep_seconds: float, max_fixtures: int | None = None) -> int:
    key = os.getenv("APIFOOTBALL_KEY") or os.getenv("API_FOOTBALL_KEY")
    if not key:
        print("APIFOOTBALL_KEY no configurada; se mantiene fallback gratuito football-data/manual.")
        return 0

    existing = _load_existing_ids(OUT_PATH)
    season_start = date.fromisoformat(CURRENT_SEASON_START)
    start = max(season_start, date.today() - timedelta(days=days_back))
    end = date.today()
    rows: list[dict[str, Any]] = []

    for code in leagues:
        if max_fixtures is not None and len(rows) >= max_fixtures:
            print(f"STOP max fixtures reached: {max_fixtures}")
            break
        api_id = APIFOOTBALL_LEAGUE_IDS.get(code)
        if not api_id:
            print(f"SKIP {code}: sin id API-Football")
            continue
        print(f"Fetching referees {code} {start} -> {end}")
        fixtures = _request(
            "/fixtures",
            {
                "league": api_id,
                "season": season_start.year,
                "from": start.isoformat(),
                "to": end.isoformat(),
                "status": "FT",
            },
            key,
        ).get("response") or []

        for fixture in fixtures:
            if max_fixtures is not None and len(rows) >= max_fixtures:
                print(f"STOP max fixtures reached: {max_fixtures}")
                break
            fixture_id = str((fixture.get("fixture") or {}).get("id") or "")
            if not fixture_id or fixture_id in existing:
                continue
            stats = _request("/fixtures/statistics", {"fixture": fixture_id}, key).get("response") or []
            row = _fixture_row(fixture, stats, code)
            if row:
                rows.append(row)
                existing.add(fixture_id)
            time.sleep(sleep_seconds)

    if rows:
        _append_rows(OUT_PATH, rows)
    print(f"OK referees appended={len(rows)} path={OUT_PATH}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=21)
    parser.add_argument("--leagues", nargs="*", default=list(APIFOOTBALL_LEAGUE_IDS.keys()))
    parser.add_argument("--sleep", type=float, default=0.35)
    parser.add_argument(
        "--max-fixtures",
        type=int,
        default=80,
        help="Maximum new fixtures to enrich with statistics in one run. Keep <=80 for API-Football free tier.",
    )
    args = parser.parse_args()
    update_referees(args.days_back, args.leagues, args.sleep, args.max_fixtures)


if __name__ == "__main__":
    main()
