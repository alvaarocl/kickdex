"""Health contracts for the static data domains exposed by KICKDEX."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.config import CURRENT_SEASON_LABEL, LEAGUES


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_data_health(
    meta: dict[str, Any],
    fixtures: dict[str, Any],
    coverage: dict[str, Any],
    referees: list[dict[str, Any]],
    suspensions: dict[str, Any],
    leagues: dict[str, Any],
) -> dict[str, Any]:
    fixture_meta = fixtures.get("meta") or {}
    fixture_download = fixture_meta.get("fixture_download") or {}
    fixture_sources = fixture_download.get("leagues") or {}
    available_fixtures = len(fixtures.get("recent") or []) + len(fixtures.get("upcoming") or [])
    fixture_failures = sorted(
        code for code, info in fixture_sources.items() if isinstance(info, dict) and not info.get("ok")
    )

    player_rows = int(coverage.get("total_player_rows") or 0)
    player_rates = [
        info.get("coverage_rate")
        for info in (coverage.get("by_league") or {}).values()
        if info.get("coverage_rate") is not None
    ]
    player_status = "unavailable" if not player_rows else ("fresh" if player_rates and min(player_rates) >= 1 else "partial")

    expected_leagues = set(LEAGUES)
    present_leagues = {code for code, info in leagues.items() if info.get("teams")}
    incomplete_rosters = sorted(
        code
        for code in expected_leagues
        if (leagues.get(code) or {}).get("roster_status") != "complete"
    )
    calendar_is_partial = bool(fixture_failures) or bool(fixture_download.get("skipped")) or not fixtures.get("upcoming")
    calendar_status = "unavailable" if not available_fixtures else ("partial" if calendar_is_partial else "fresh")
    teams_status = "fresh" if expected_leagues <= present_leagues and not incomplete_rosters else "partial"
    suspension_items = suspensions.get("items") or []
    domains = {
        "calendar": {
            "status": calendar_status,
            "updated_at": fixture_meta.get("updated_at"),
            "records": available_fixtures,
            "failed_leagues": fixture_failures,
        },
        "teams": {
            "status": teams_status,
            "updated_at": meta.get("updated_at"),
            "records": sum(len(info.get("teams") or []) for info in leagues.values()),
            "missing_leagues": sorted(expected_leagues - present_leagues),
            "incomplete_rosters": incomplete_rosters,
        },
        "players": {
            "status": player_status,
            "updated_at": coverage.get("updated_at"),
            "records": player_rows,
            "coverage_by_league": {
                code: info.get("coverage_rate") for code, info in (coverage.get("by_league") or {}).items()
            },
        },
        "referees": {
            "status": "unavailable" if not referees else "partial",
            "updated_at": meta.get("updated_at"),
            "records": len(referees),
            "note": "La cobertura arbitral depende de fuentes agregadas, historicas y manuales.",
        },
        "suspensions": {
            "status": "fresh" if suspension_items else "unavailable",
            "updated_at": suspensions.get("updated_at"),
            "records": len(suspension_items),
        },
    }
    essential_statuses = [domains["calendar"]["status"], domains["teams"]["status"]]
    return {
        "updated_at": _now(),
        "season": CURRENT_SEASON_LABEL,
        "overall": "unavailable" if all(status == "unavailable" for status in essential_statuses) else (
            "partial" if any(v["status"] == "partial" for v in domains.values()) else "fresh"
        ),
        "domains": domains,
    }
