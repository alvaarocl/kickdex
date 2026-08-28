"""
Clasificación y máximos goleadores vía football-data.org.

Mismo token que update_live_scores.py (mismo tier gratuito, mismas 7 ligas
cubiertas) pero un refresco propio y mucho menos frecuente: una tabla de
posiciones o una lista de goleadores no cambia salvo que se juegue una
jornada, así que un cron diario es de sobra — no hace falta cargar el
límite de 10 peticiones/min compartido con el marcador con retraso.

Free-first strategy (igual que el resto del pipeline): sin
FOOTBALL_DATA_API_KEY configurada, escribe el mismo contrato con
enabled=false y termina con éxito.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import FOOTBALL_DATA_ORG_COMPETITION_CODES
from app.data.loader import normalize_fd_org_team_name

API_BASE = "https://api.football-data.org/v4"
STANDINGS_PATH = ROOT / "docs" / "data" / "standings.json"
SCORERS_PATH = ROOT / "docs" / "data" / "scorers.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_contract(enabled: bool, note: str) -> dict[str, Any]:
    return {
        "updated_at": _now_iso(),
        "enabled": enabled,
        "source": "football-data.org",
        "note": note,
        "leagues_covered": sorted(FOOTBALL_DATA_ORG_COMPETITION_CODES.keys()),
        "leagues": {},
    }


def _request(path: str, key: str, timeout: int = 20) -> dict[str, Any]:
    res = requests.get(f"{API_BASE}{path}", headers={"X-Auth-Token": key}, timeout=timeout)
    res.raise_for_status()
    return res.json()


def _standings_for_league(payload: dict[str, Any]) -> dict[str, Any] | None:
    totals = next((s for s in payload.get("standings") or [] if s.get("type") == "TOTAL"), None)
    if not totals:
        return None
    season = payload.get("season") or {}
    return {
        "competition_name": (payload.get("competition") or {}).get("name"),
        "matchday": season.get("currentMatchday"),
        "season_start": season.get("startDate"),
        "season_end": season.get("endDate"),
        "table": [
            {
                "position": row.get("position"),
                "team": normalize_fd_org_team_name((row.get("team") or {}).get("name")),
                "played": row.get("playedGames"),
                "won": row.get("won"),
                "draw": row.get("draw"),
                "lost": row.get("lost"),
                "goals_for": row.get("goalsFor"),
                "goals_against": row.get("goalsAgainst"),
                "goal_diff": row.get("goalDifference"),
                "points": row.get("points"),
            }
            for row in totals.get("table") or []
        ],
    }


def _scorers_for_league(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "competition_name": (payload.get("competition") or {}).get("name"),
        "scorers": [
            {
                "rank": i + 1,
                "player": (row.get("player") or {}).get("name"),
                "team": normalize_fd_org_team_name((row.get("team") or {}).get("name")),
                "goals": row.get("goals"),
                "assists": row.get("assists"),
                "penalties": row.get("penalties"),
                "played_matches": row.get("playedMatches"),
            }
            for i, row in enumerate(payload.get("scorers") or [])
        ],
    }


def update_standings(leagues: list[str] | None = None, sleep_seconds: float = 6.5, limit_scorers: int = 20) -> None:
    key = os.getenv("FOOTBALL_DATA_API_KEY")
    leagues = leagues or list(FOOTBALL_DATA_ORG_COMPETITION_CODES.keys())

    if not key:
        note = "Clasificacion/goleadores desactivados: falta configurar FOOTBALL_DATA_API_KEY."
        for path in (STANDINGS_PATH, SCORERS_PATH):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(_empty_contract(False, note), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("SKIP standings/scorers: FOOTBALL_DATA_API_KEY no configurada")
        return

    standings_contract = _empty_contract(True, "Actualizado a diario, no en directo.")
    scorers_contract = _empty_contract(True, "Actualizado a diario, no en directo.")

    for i, code in enumerate(leagues):
        comp = FOOTBALL_DATA_ORG_COMPETITION_CODES.get(code)
        if not comp:
            print(f"SKIP {code}: no cubierta por el tier gratuito de football-data.org")
            continue
        try:
            standings_payload = _request(f"/competitions/{comp}/standings", key)
            league_standings = _standings_for_league(standings_payload)
            if league_standings:
                standings_contract["leagues"][code] = league_standings
        except Exception as exc:
            print(f"SKIP standings {code} ({comp}): {exc}")
        time.sleep(sleep_seconds)

        try:
            scorers_payload = _request(f"/competitions/{comp}/scorers?limit={limit_scorers}", key)
            scorers_contract["leagues"][code] = _scorers_for_league(scorers_payload)
        except Exception as exc:
            print(f"SKIP scorers {code} ({comp}): {exc}")
        print(f"OK {code} ({comp}): standings={code in standings_contract['leagues']} scorers={code in scorers_contract['leagues']}")
        if i < len(leagues) - 1:
            time.sleep(sleep_seconds)

    STANDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STANDINGS_PATH.write_text(json.dumps(standings_contract, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    SCORERS_PATH.write_text(json.dumps(scorers_contract, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK standings.json leagues={len(standings_contract['leagues'])} scorers.json leagues={len(scorers_contract['leagues'])}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(FOOTBALL_DATA_ORG_COMPETITION_CODES.keys()))
    parser.add_argument("--sleep", type=float, default=6.5, help="Pausa entre peticiones (10/min en el tier gratuito)")
    parser.add_argument("--limit-scorers", type=int, default=20)
    args = parser.parse_args()
    update_standings(args.leagues, args.sleep, args.limit_scorers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
