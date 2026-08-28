"""
Marcador con retraso (no en directo) vía football-data.org.

Contexto: ninguna API gratuita real ofrece minuto a minuto para las ligas de
KICKDEX. football-data.org es gratis pero su plan gratuito no incluye datos
en vivo, solo consulta normal — así que este script pide "los partidos de
hoy" cada ~15 min (vía cron, ver .github/workflows/update_live_scores.yml) y
el frontend lo etiqueta honestamente como "con retraso", nunca como directo.

Free-first strategy (mismo patrón que update_referee_data.py):
- Si FOOTBALL_DATA_API_KEY no está configurada, escribe el mismo contrato
  con enabled=false y termina con éxito (nunca rompe el build).
- Con clave, una petición por competición cubierta (7 ligas en el tier
  gratuito), con una pausa entre peticiones para respetar el límite de
  10 peticiones/min.
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
from app.data.loader import normalize_team_name

API_BASE = "https://api.football-data.org/v4"
OUT_PATH = ROOT / "docs" / "data" / "live_scores.json"

# football-data.org status -> etiqueta interna que ya usa el resto de KICKDEX.
STATUS_MAP = {
    "SCHEDULED": "scheduled",
    "TIMED": "scheduled",
    "IN_PLAY": "live",
    "PAUSED": "live",
    "FINISHED": "finished",
    "SUSPENDED": "suspended",
    "POSTPONED": "postponed",
    "CANCELLED": "cancelled",
    "AWARDED": "finished",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_contract(enabled: bool, note: str) -> dict[str, Any]:
    return {
        "updated_at": _now_iso(),
        "enabled": enabled,
        "delayed": True,
        "source": "football-data.org",
        "note": note,
        "leagues_covered": sorted(FOOTBALL_DATA_ORG_COMPETITION_CODES.keys()),
        "matches": [],
    }


def _request(path: str, key: str, timeout: int = 20) -> dict[str, Any]:
    res = requests.get(
        f"{API_BASE}{path}",
        headers={"X-Auth-Token": key},
        timeout=timeout,
    )
    res.raise_for_status()
    return res.json()


def _normalise_match(raw: dict[str, Any], league_code: str) -> dict[str, Any] | None:
    home = (raw.get("homeTeam") or {}).get("name")
    away = (raw.get("awayTeam") or {}).get("name")
    if not home or not away:
        return None
    score = raw.get("score") or {}
    full_time = score.get("fullTime") or {}
    live_score = full_time if full_time.get("home") is not None else (score.get("halfTime") or {})
    status_raw = str(raw.get("status") or "SCHEDULED").upper()
    minute = None
    if status_raw in ("IN_PLAY", "PAUSED"):
        minute = (raw.get("minute") if isinstance(raw.get("minute"), int) else None)

    return {
        "league": league_code,
        "home": normalize_team_name(home),
        "away": normalize_team_name(away),
        "status": STATUS_MAP.get(status_raw, "scheduled"),
        "utc_date": raw.get("utcDate"),
        "minute": minute,
        "home_score": live_score.get("home"),
        "away_score": live_score.get("away"),
    }


def fetch_live_scores(key: str, leagues: list[str], sleep_seconds: float) -> list[dict[str, Any]]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    matches: list[dict[str, Any]] = []
    for i, code in enumerate(leagues):
        comp = FOOTBALL_DATA_ORG_COMPETITION_CODES.get(code)
        if not comp:
            print(f"SKIP {code}: no cubierta por el tier gratuito de football-data.org")
            continue
        try:
            payload = _request(
                f"/competitions/{comp}/matches?dateFrom={today}&dateTo={today}",
                key,
            )
        except Exception as exc:
            print(f"SKIP {code} ({comp}): {exc}")
            continue
        for raw in payload.get("matches") or []:
            row = _normalise_match(raw, code)
            if row:
                matches.append(row)
        print(f"OK {code} ({comp}): {len(payload.get('matches') or [])} partidos hoy")
        if i < len(leagues) - 1:
            time.sleep(sleep_seconds)
    return matches


def update_live_scores(leagues: list[str] | None = None, sleep_seconds: float = 6.5) -> dict[str, Any]:
    key = os.getenv("FOOTBALL_DATA_API_KEY")
    leagues = leagues or list(FOOTBALL_DATA_ORG_COMPETITION_CODES.keys())

    if not key:
        contract = _empty_contract(
            enabled=False,
            note="Directo desactivado: falta configurar FOOTBALL_DATA_API_KEY.",
        )
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(contract, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("SKIP live scores: FOOTBALL_DATA_API_KEY no configurada")
        return contract

    matches = fetch_live_scores(key, leagues, sleep_seconds)
    contract = _empty_contract(
        enabled=True,
        note="Datos con retraso (actualización cada ~15 min), no es un feed minuto a minuto.",
    )
    contract["matches"] = matches
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(contract, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK live_scores.json matches={len(matches)} path={OUT_PATH}")
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(FOOTBALL_DATA_ORG_COMPETITION_CODES.keys()))
    parser.add_argument("--sleep", type=float, default=6.5, help="Pausa entre peticiones (10/min en el tier gratuito)")
    args = parser.parse_args()
    update_live_scores(args.leagues, args.sleep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
