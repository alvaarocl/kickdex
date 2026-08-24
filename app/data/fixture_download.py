"""FixtureDownload calendar feed helpers.

The feed is public JSON and normally updated daily. We use it as the complete
season-calendar source; match analytics continue to use football-data CSVs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from difflib import get_close_matches
import re
import unicodedata
from zoneinfo import ZoneInfo

import requests

from app.config import CURRENT_SEASON_YEAR, TEAM_ALIASES


FEED_BASE_URL = "https://fixturedownload.com/feed/json"

FIXTURE_DOWNLOAD_COMPETITIONS = {
    "SP1": "la-liga",
    "E0": "epl",
    "E1": "championship",
    "I1": "serie-a",
    "D1": "bundesliga",
    "F1": "ligue-1",
    "N1": "eredivisie",
}


def fixture_download_slugs(season_year: int = CURRENT_SEASON_YEAR) -> dict[str, str]:
    """Return feed slugs for the configured season; never hardcode last season."""
    return {code: f"{competition}-{season_year}" for code, competition in FIXTURE_DOWNLOAD_COMPETITIONS.items()}

TEAM_NAME_ALIASES = {
    "man utd": "Man United",
    "spurs": "Tottenham",
    "wolverhampton wanderers": "Wolves",
    "fc bayern munchen": "Bayern Munich",
    "fc bayern münchen": "Bayern Munich",
    "borussia monchengladbach": "M'gladbach",
    "borussia mönchengladbach": "M'gladbach",
    "1 fc koln": "FC Koln",
    "1 fc köln": "FC Koln",
    "1 fsv mainz 05": "Mainz",
    "sv werder bremen": "Werder Bremen",
    "sport club freiburg": "Freiburg",
    "fc st pauli": "St Pauli",
    "vfl wolfsburg": "Wolfsburg",
    "tsg hoffenheim": "Hoffenheim",
    "fc augsburg": "Augsburg",
    "fc union berlin": "Union Berlin",
    "1 fc union berlin": "Union Berlin",
    "fc heidenheim": "Heidenheim",
    "1 fc heidenheim 1846": "Heidenheim",
    "hamburger sv": "Hamburg",
    "olympique de marseille": "Marseille",
    "olympique marseille": "Marseille",
    "olympique lyonnais": "Lyon",
    "paris saint germain": "PSG",
    "losc lille": "Lille",
    "havre athletic club": "Le Havre",
    "rc lens": "Lens",
    "rc strasbourg alsace": "Strasbourg",
    "stade rennais fc": "Rennes",
    "stade brestois 29": "Brest",
    "angers sco": "Angers",
    "as monaco": "Monaco",
    "ogc nice": "Nice",
    "fc lorient": "Lorient",
    "fc metz": "Metz",
    "fc nantes": "Nantes",
    "toulouse fc": "Toulouse",
    "aj auxerre": "Auxerre",
    "fc barcelona": "Barcelona",
    "atletico de madrid": "Ath Madrid",
    "atlético de madrid": "Ath Madrid",
    "atl madrid": "Ath Madrid",
    "athletic club": "Athletic Club",
    "ca osasuna": "Osasuna",
    "c a osasuna": "Osasuna",
    "cd alaves": "Alaves",
    "d alaves": "Alaves",
    "elche cf": "Elche",
    "espanyol barcelona": "Espanol",
    "rcd espanyol": "Espanol",
    "rcd espanyol de barcelona": "Espanol",
    "getafe cf": "Getafe",
    "girona fc": "Girona",
    "levante ud": "Levante",
    "rc celta": "Celta",
    "rcd mallorca": "Mallorca",
    "real betis": "Betis",
    "real sociedad": "Sociedad",
    "rayo vallecano": "Vallecano",
    "r racing club": "Santander",
    "villarreal cf": "Villarreal",
    "queens park rangers": "QPR",
    "sheffield wednesday": "Sheffield Weds",
    "west bromwich albion": "West Brom",
    "internazionale": "Inter",
    "fortuna sittard": "For Sittard",
}


def _norm_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _canonical_team(name: str, league_teams: list[str]) -> str:
    if not name:
        return ""
    lookup = {_norm_name(team): team for team in league_teams}
    norm = _norm_name(name)
    for source in (TEAM_NAME_ALIASES, TEAM_ALIASES):
        mapped = source.get(norm)
        if mapped:
            return mapped
    if norm in lookup:
        return lookup[norm]
    for key, canonical in lookup.items():
        if norm.startswith(f"{key} ") or norm.endswith(f" {key}") or key.startswith(f"{norm} "):
            return canonical

    trimmed = re.sub(r"\b(fc|cf|sc|afc|ud|cd|rcd|rc|ac|sv|vfl|tsg|as|losc)\b", "", norm)
    trimmed = re.sub(r"\s+", " ", trimmed).strip()
    if trimmed in lookup:
        return lookup[trimmed]
    for key, canonical in lookup.items():
        if trimmed.startswith(f"{key} ") or trimmed.endswith(f" {key}") or key.startswith(f"{trimmed} "):
            return canonical

    match = get_close_matches(norm, list(lookup.keys()), n=1, cutoff=0.86)
    return lookup[match[0]] if match else str(name)


def _parse_feed_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_fixture_download_calendar(
    leagues: dict[str, str],
    league_teams: dict[str, list[str]],
    timeout: int = 20,
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """Fetch recent results, upcoming fixtures and the complete calendar."""

    session = requests.Session()
    session.headers.update({"User-Agent": "KICKDEX/1.0 (+https://kickdex.alvarocarpintero.com)"})
    madrid = ZoneInfo("Europe/Madrid")
    now_utc = datetime.now(timezone.utc)
    recent: list[dict] = []
    upcoming: list[dict] = []
    calendar: list[dict] = []
    status = {"source": "fixturedownload", "updated_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "leagues": {}}

    for code, slug in fixture_download_slugs().items():
        if code not in leagues:
            continue
        url = f"{FEED_BASE_URL}/{slug}"
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            matches = response.json()
        except Exception as exc:
            status["leagues"][code] = {"ok": False, "error": str(exc)}
            continue

        league_recent = 0
        league_upcoming = 0
        for match in matches:
            dt_utc = _parse_feed_datetime(match.get("DateUtc"))
            if not dt_utc:
                continue
            dt_local = dt_utc.astimezone(madrid)
            home_score = match.get("HomeTeamScore")
            away_score = match.get("AwayTeamScore")
            has_score = home_score is not None and away_score is not None
            item = {
                "league": code,
                "league_name": leagues.get(code, code),
                "date": dt_local.strftime("%Y-%m-%d"),
                "time": dt_local.strftime("%H:%M"),
                "home": _canonical_team(match.get("HomeTeam", ""), league_teams.get(code, [])),
                "away": _canonical_team(match.get("AwayTeam", ""), league_teams.get(code, [])),
                "round": match.get("RoundNumber"),
                "venue": match.get("Location") or "",
                "source": "FixtureDownload",
            }
            if has_score:
                item["home_score"] = int(home_score)
                item["away_score"] = int(away_score)
                item["status"] = "finished"
                if now_utc - timedelta(days=7) <= dt_utc <= now_utc:
                    recent.append(item)
                    league_recent += 1
            elif dt_utc >= now_utc:
                item["status"] = "scheduled"
                upcoming.append(item)
                league_upcoming += 1
            else:
                item["status"] = "postponed"
            calendar.append(item)

        status["leagues"][code] = {
            "ok": True,
            "recent": league_recent,
            "upcoming": league_upcoming,
            "total": len(matches),
        }

    return recent, upcoming, calendar, status
