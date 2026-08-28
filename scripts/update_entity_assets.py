"""Incrementally enrich team crests and player photos when a provider key exists."""

from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import APIFOOTBALL_LEAGUE_IDS, CURRENT_SEASON_YEAR
from app.data.assets import build_player_assets, build_team_assets
from app.data.loader import normalize_team_name

DATA_DIR = ROOT / "docs" / "data"
API_BASE = "https://v3.football.api-sports.io"


def _read(name: str, default):
    path = DATA_DIR / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write(name: str, value) -> None:
    (DATA_DIR / name).write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()


def api_get(path: str, key: str) -> list:
    response = requests.get(API_BASE + path, headers={"x-apisports-key": key}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(str(payload["errors"]))
    return payload.get("response") or []


def enrich(key: str, max_player_teams: int = 10, force: bool = False) -> tuple[int, int]:
    leagues = _read("leagues.json", {})
    players = _read("players.json", {})
    team_manifest = build_team_assets(leagues, _read("team_assets.json", {}))
    player_manifest = build_player_assets(players, _read("player_assets.json", {}))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    provider_teams: dict[str, dict] = {}
    for code in leagues:
        league_id = APIFOOTBALL_LEAGUE_IDS.get(code)
        if not league_id:
            continue
        try:
            rows = api_get(f"/teams?league={league_id}&season={CURRENT_SEASON_YEAR}", key)
        except Exception as exc:
            print(f"SKIP assets {code}: {exc}")
            continue
        for row in rows:
            provider = row.get("team") or {}
            canonical = normalize_team_name(provider.get("name"))
            provider_teams[_norm(canonical)] = provider

    teams_updated = 0
    team_ids: list[int] = []
    for name, asset in team_manifest["teams"].items():
        provider = provider_teams.get(_norm(name))
        if not provider:
            continue
        if asset.get("crest") and not force:
            # No pisar un escudo ya presente (p.ej. los arreglados a mano vía
            # update_team_crests.py) con lo que devuelva esta otra fuente.
            if provider.get("id"):
                team_ids.append(int(provider["id"]))
            continue
        asset.update({
            "id": provider.get("id"),
            "crest": provider.get("logo"),
            "source": "api-football",
            "source_updated_at": now,
        })
        if provider.get("id"):
            team_ids.append(int(provider["id"]))
        teams_updated += 1

    players_updated = 0
    missing_photo_teams = []
    for team_id in dict.fromkeys(team_ids):
        if len(missing_photo_teams) >= max_player_teams:
            break
        missing_photo_teams.append(team_id)
        try:
            squads = api_get(f"/players/squads?team={team_id}", key)
        except Exception as exc:
            print(f"SKIP player assets team={team_id}: {exc}")
            continue
        for block in squads:
            team_name = normalize_team_name((block.get("team") or {}).get("name"))
            for provider in block.get("players") or []:
                candidates = [
                    key_name for key_name, item in player_manifest["players"].items()
                    if _norm(item.get("team")) == _norm(team_name) and _norm(item.get("name")) == _norm(provider.get("name"))
                ]
                for key_name in candidates:
                    existing = player_manifest["players"][key_name]
                    if existing.get("photo") and not force:
                        # No pisar una foto ya presente (p.ej. Wikidata) con
                        # la de esta otra fuente.
                        continue
                    existing.update({
                        "id": provider.get("id"),
                        "photo": provider.get("photo"),
                        "source": "api-football",
                        "source_updated_at": now,
                    })
                    players_updated += 1

    _write("team_assets.json", team_manifest)
    _write("player_assets.json", player_manifest)
    return teams_updated, players_updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-player-teams", type=int, default=10)
    parser.add_argument("--force", action="store_true", help="Sobrescribe escudos/fotos ya presentes en vez de preservarlos")
    args = parser.parse_args()
    key = os.getenv("APIFOOTBALL_KEY") or os.getenv("API_FOOTBALL_KEY")
    if not key:
        print("SKIP entity assets: APIFOOTBALL_KEY is not configured")
        return 0
    teams, players = enrich(key, max_player_teams=max(0, args.max_player_teams), force=args.force)
    print(f"OK entity assets teams={teams} players={players}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
