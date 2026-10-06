"""Build stable entity/asset manifests without requiring a paid provider."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _initials(value: str) -> str:
    words = [word for word in re.split(r"\s+", value.strip()) if word]
    return "".join(word[0] for word in words[:2]).upper() or "KD"


def build_team_assets(leagues: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing_teams = (existing or {}).get("teams") or {}
    teams: dict[str, Any] = {}
    for league, info in leagues.items():
        for name in info.get("teams") or []:
            previous = existing_teams.get(name) or {}
            teams[name] = {
                "id": previous.get("id"),
                "name": name,
                "slug": _slug(name),
                "initials": _initials(name),
                "league": league,
                "crest": previous.get("crest"),
                "crest_local": previous.get("crest_local"),
                "source": previous.get("source"),
                "source_updated_at": previous.get("source_updated_at"),
            }
    return {"version": 1, "updated_at": _now(), "teams": teams}


def _name_key(name: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", str(name or ""))
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).lower().split())


def build_player_assets(players: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing_players = (existing or {}).get("players") or {}
    # Respaldo por nombre (sin acentos) cuando cambia el equipo o su clave
    # (traspasos, "Paris Saint Germain" -> "Paris SG"): solo si es inequívoco.
    by_name: dict[str, list] = {}
    for prev in existing_players.values():
        if prev.get("photo") or prev.get("photo_local"):
            by_name.setdefault(_name_key(prev.get("name")), []).append(prev)
    assets: dict[str, Any] = {}
    for team, rows in players.items():
        for row in rows if isinstance(rows, list) else []:
            name = str(row.get("player") or "").strip()
            if not name:
                continue
            key = f"{team}::{name}"
            previous = existing_players.get(key) or {}
            if not (previous.get("photo") or previous.get("photo_local")):
                same = by_name.get(_name_key(name), [])
                if len({(p.get("photo") or p.get("photo_local")) for p in same}) == 1:
                    previous = {**same[0], **{k: v for k, v in previous.items() if v}}
            assets[key] = {
                "id": previous.get("id"),
                "name": name,
                "team": team,
                "slug": _slug(name),
                "initials": _initials(name),
                "photo": previous.get("photo"),
                "photo_local": previous.get("photo_local"),
                "source": previous.get("source"),
                "source_updated_at": previous.get("source_updated_at"),
            }
    return {"version": 1, "updated_at": _now(), "players": assets}
