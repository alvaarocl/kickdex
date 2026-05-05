"""Build the official/verified suspension feed used by the static frontend.

The important rule in this module is product honesty: a statistical card-risk
model never becomes an "apercibido". Rows only enter this payload when they
come from an official source, or from a manually verified source explicitly
marked as such.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable


VALID_STATUSES = {"at_risk", "suspended"}
STATUS_LABELS = {
    "at_risk": "A una amarilla",
    "suspended": "Sancionado",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text(value) -> str:
    return str(value or "").strip()


def _number(value):
    try:
        if value in (None, ""):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def _bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "si", "sí", "official"}


def _league_lookup(leagues: dict) -> dict:
    lookup = {}
    for code, info in (leagues or {}).items():
        for team in info.get("teams", []) or []:
            lookup[_text(team).lower()] = code
    return lookup


def normalise_suspension_rows(rows: Iterable[dict], leagues: dict | None = None) -> list[dict]:
    league_by_team = _league_lookup(leagues or {})
    clean = []
    seen = set()

    for row in rows or []:
        player = _text(row.get("player"))
        team = _text(row.get("team"))
        status = _text(row.get("status")).lower().replace(" ", "_").replace("-", "_")
        if status in {"warning", "apercibido", "apercibidos", "one_yellow_away", "one_card_away"}:
            status = "at_risk"
        if status in {"ban", "banned", "suspension", "sancionado", "sancion"}:
            status = "suspended"

        if not player or not team or status not in VALID_STATUSES:
            continue

        league = _text(row.get("league")) or league_by_team.get(team.lower()) or None
        league_name = (leagues or {}).get(league, {}).get("name", league) if league else None
        source_name = _text(row.get("source_name") or row.get("source") or "Fuente verificada")
        source_url = _text(row.get("source_url") or row.get("url"))
        official = _bool(row.get("official"))
        verified = official or _bool(row.get("verified"))

        item = {
            "player": player,
            "team": team,
            "league": league,
            "league_name": league_name,
            "status": status,
            "status_label": STATUS_LABELS[status],
            "cards": _number(row.get("cards")),
            "threshold": _number(row.get("threshold")),
            "matchday": _text(row.get("matchday") or row.get("round")) or None,
            "source_name": source_name,
            "source_url": source_url or None,
            "official": official,
            "verified": verified,
            "updated_at": _text(row.get("updated_at")) or utc_now_iso(),
            "notes": _text(row.get("notes")) or None,
        }
        key = (
            item["league"],
            item["team"].lower(),
            item["player"].lower(),
            item["status"],
            item["source_url"] or item["source_name"].lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        clean.append(item)

    clean.sort(key=lambda item: (
        item["league_name"] or "",
        item["team"],
        0 if item["status"] == "suspended" else 1,
        item["player"],
    ))
    return clean


def build_suspensions_payload(rows: Iterable[dict], leagues: dict | None = None, source_catalog: Iterable[dict] | None = None) -> dict:
    items = normalise_suspension_rows(rows, leagues)
    by_team: dict[str, dict[str, list[dict]]] = {}
    by_league: dict[str, dict] = {}
    sources = {}

    for source in source_catalog or []:
        source_key = source.get("url") or source.get("name")
        if not source_key:
            continue
        sources[source_key] = {
            "name": source.get("name"),
            "url": source.get("url"),
            "official": bool(source.get("official", False)),
            "verified": bool(source.get("verified", source.get("official", False))),
            "league": source.get("league"),
            "status": "configured",
        }

    for item in items:
        team_block = by_team.setdefault(item["team"], {"at_risk": [], "suspended": []})
        team_block[item["status"]].append(item)

        league = item.get("league") or "unknown"
        league_block = by_league.setdefault(league, {
            "name": item.get("league_name") or league,
            "at_risk": [],
            "suspended": [],
            "items": [],
        })
        league_block[item["status"]].append(item)
        league_block["items"].append(item)

        source_key = item.get("source_url") or item.get("source_name")
        if source_key:
            sources[source_key] = {
                "name": item.get("source_name"),
                "url": item.get("source_url"),
                "official": item.get("official", False),
                "verified": item.get("verified", False),
                "league": item.get("league"),
                "status": "has_rows",
            }

    official_count = sum(1 for item in items if item.get("official"))
    verified_count = sum(1 for item in items if item.get("verified"))
    return {
        "updated_at": utc_now_iso(),
        "status": "ok" if items else "empty",
        "source": "official_or_verified_suspension_feed",
        "disclaimer": (
            "Solo se muestran sanciones y apercibidos confirmados por una fuente oficial "
            "o cargados como verificados. KICKDEX no rellena esta lista con modelos de riesgo."
        ),
        "totals": {
            "items": len(items),
            "at_risk": sum(1 for item in items if item["status"] == "at_risk"),
            "suspended": sum(1 for item in items if item["status"] == "suspended"),
            "official": official_count,
            "verified": verified_count,
        },
        "sources": sorted(sources.values(), key=lambda source: (not source["official"], source["name"] or "")),
        "items": items,
        "by_team": by_team,
        "by_league": by_league,
    }
