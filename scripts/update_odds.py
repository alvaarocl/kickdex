"""
Cuotas de partidos futuros vía The Odds API (the-odds-api.com) — Fase 4.

El edge histórico de KICKDEX se calcula con las cuotas de cierre Bet365 que
football-data.co.uk publica DESPUÉS de cada partido. Para tener edge en
partidos que aún no se han jugado hace falta una fuente de cuotas en vivo;
este script la conecta y escribe docs/data/odds.json.

Free-first (igual que update_live_scores.py / update_standings.py): sin
THE_ODDS_API_KEY configurada escribe el mismo contrato con enabled=false y
termina con éxito — el pipeline y el frontend siguen funcionando, el edge
simplemente sigue siendo solo retrospectivo.

Contrato de odds.json:
{
  "updated_at": "2026-08-28T10:00:00Z",
  "enabled": true,
  "source": "the-odds-api.com",
  "note": "...",
  "leagues_covered": ["SP1", "E0", ...],
  "matches": {
    "<league>|<YYYY-MM-DD>|<home_key>|<away_key>": {
      "commence_time": "2026-08-29T19:00:00Z",
      "bookmaker_count": 8,
      "markets": {
        "h2h":    {"home": 1.95, "draw": 3.60, "away": 3.80},
        "totals": {"2.5": {"over": 1.90, "under": 1.95}}
      },
      "fetched_at": "2026-08-28T10:00:00Z"
    }
  }
}
Las cuotas guardadas son la MEJOR (más alta) disponible entre casas para cada
selección — coherente con "mejor cuota disponible" que muestra la UI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import THE_ODDS_API_SPORT_KEYS
from app.data.loader import normalize_team_name

API_BASE = "https://api.the-odds-api.com/v4"
ODDS_PATH = ROOT / "docs" / "data" / "odds.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_contract(enabled: bool, note: str) -> dict:
    return {
        "updated_at": _now_iso(),
        "enabled": enabled,
        "source": "the-odds-api.com",
        "note": note,
        "leagues_covered": sorted(THE_ODDS_API_SPORT_KEYS.keys()),
        "matches": {},
    }


def _best(prices: list[float]) -> float | None:
    prices = [p for p in prices if isinstance(p, (int, float)) and p > 1]
    return round(max(prices), 3) if prices else None


def _parse_event(event: dict, league_code: str) -> tuple[str, dict] | None:
    home_raw = event.get("home_team") or ""
    away_raw = event.get("away_team") or ""
    if not home_raw or not away_raw:
        return None
    home = normalize_team_name(home_raw)
    away = normalize_team_name(away_raw)
    commence = event.get("commence_time") or ""
    date = commence[:10]
    if not date:
        return None

    h2h_home, h2h_draw, h2h_away = [], [], []
    totals: dict[str, dict[str, list[float]]] = {}
    books = event.get("bookmakers") or []
    for book in books:
        for market in book.get("markets") or []:
            key = market.get("key")
            outcomes = market.get("outcomes") or []
            if key == "h2h":
                for o in outcomes:
                    name, price = o.get("name"), o.get("price")
                    if name == home_raw:
                        h2h_home.append(price)
                    elif name == away_raw:
                        h2h_away.append(price)
                    elif name and name.lower() in ("draw", "tie"):
                        h2h_draw.append(price)
            elif key == "totals":
                for o in outcomes:
                    point = o.get("point")
                    side = (o.get("name") or "").lower()
                    if point is None or side not in ("over", "under"):
                        continue
                    line = f"{point}"
                    totals.setdefault(line, {"over": [], "under": []})[side].append(o.get("price"))

    markets: dict = {}
    h2h = {
        "home": _best(h2h_home),
        "draw": _best(h2h_draw),
        "away": _best(h2h_away),
    }
    if any(h2h.values()):
        markets["h2h"] = {k: v for k, v in h2h.items() if v is not None}
    totals_out = {}
    for line, sides in totals.items():
        o, u = _best(sides["over"]), _best(sides["under"])
        if o and u:
            totals_out[line] = {"over": o, "under": u}
    if totals_out:
        markets["totals"] = totals_out

    if not markets:
        return None

    key = f"{league_code}|{date}|{home}|{away}"
    return key, {
        "commence_time": commence,
        "bookmaker_count": len(books),
        "markets": markets,
        "fetched_at": _now_iso(),
    }


def update_odds(leagues: list[str] | None = None, regions: str = "eu", markets: str = "h2h,totals") -> None:
    key = os.getenv("THE_ODDS_API_KEY")
    leagues = leagues or list(THE_ODDS_API_SPORT_KEYS.keys())

    if not key:
        note = "Cuotas de partidos futuros desactivadas: falta configurar THE_ODDS_API_KEY."
        ODDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ODDS_PATH.write_text(json.dumps(_empty_contract(False, note), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("SKIP odds: THE_ODDS_API_KEY no configurada")
        return

    contract = _empty_contract(True, "Mejor cuota disponible entre casas. Actualizado por cron; no es un feed en vivo minuto a minuto.")
    requests_used = None

    for code in leagues:
        sport = THE_ODDS_API_SPORT_KEYS.get(code)
        if not sport:
            continue
        try:
            res = requests.get(
                f"{API_BASE}/sports/{sport}/odds",
                params={"apiKey": key, "regions": regions, "markets": markets, "oddsFormat": "decimal"},
                timeout=25,
            )
            res.raise_for_status()
            requests_used = res.headers.get("x-requests-remaining", requests_used)
            for event in res.json():
                parsed = _parse_event(event, code)
                if parsed:
                    contract["matches"][parsed[0]] = parsed[1]
            print(f"OK odds {code} ({sport}): {sum(1 for k in contract['matches'] if k.startswith(code + '|'))} partidos")
        except Exception as exc:
            print(f"SKIP odds {code} ({sport}): {exc}")

    if requests_used is not None:
        contract["note"] += f" · peticiones restantes este mes: {requests_used}"

    ODDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ODDS_PATH.write_text(json.dumps(contract, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK odds.json — {len(contract['matches'])} partidos con cuotas")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(THE_ODDS_API_SPORT_KEYS.keys()))
    parser.add_argument("--regions", default="eu")
    parser.add_argument("--markets", default="h2h,totals")
    args = parser.parse_args()
    update_odds(args.leagues, args.regions, args.markets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
