"""Update docs/data/suspensions.json from official or verified sources.

Default behaviour is intentionally conservative: it reads DATOS/suspensions_manual.csv
and configured source feeds, then writes only rows that can be attributed. It never
promotes the statistical card-risk model to official apercibidos.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.engine.suspensions import build_suspensions_payload

DATA_DIR = ROOT / "DATOS"
OUTPUT_DIR = ROOT / "docs" / "data"
MANUAL_CSV = DATA_DIR / "suspensions_manual.csv"
SOURCES_JSON = DATA_DIR / "suspensions_sources.json"

PL_CLUBS = {
    "ARS": "Arsenal",
    "AVL": "Aston Villa",
    "BOU": "Bournemouth",
    "BRE": "Brentford",
    "BHA": "Brighton",
    "BUR": "Burnley",
    "CHE": "Chelsea",
    "CRY": "Crystal Palace",
    "EVE": "Everton",
    "FUL": "Fulham",
    "LEE": "Leeds",
    "LIV": "Liverpool",
    "MCI": "Man City",
    "MUN": "Man United",
    "NEW": "Newcastle",
    "NFO": "Nott'm Forest",
    "SUN": "Sunderland",
    "TOT": "Tottenham",
    "WHU": "West Ham",
    "WOL": "Wolves",
}

BUNDESLIGA_TEAMS = {
    "Bayer Leverkusen": "Leverkusen",
    "Bayern Munich": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "Borussia Mönchengladbach": "M'gladbach",
    "Cologne": "FC Koln",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "FC St. Pauli": "St Pauli",
    "St. Pauli": "St Pauli",
    "Hamburg": "Hamburg",
    "Mainz": "Mainz",
    "RB Leipzig": "RB Leipzig",
    "VfB Stuttgart": "Stuttgart",
    "Werder Bremen": "Werder Bremen",
}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        text = " ".join(str(data or "").split())
        if text:
            self.parts.append(text)


def html_lines(html: str) -> list[str]:
    parser = TextExtractor()
    parser.feed(html)
    return [part.strip() for part in parser.parts if part.strip()]


def article_body_lines(html: str) -> list[str]:
    for line in html_lines(html):
        if '"articleBody"' not in line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        body = payload.get("articleBody")
        if body:
            return [" ".join(part.split()) for part in body.splitlines() if part.strip()]
    return html_lines(html)


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def read_manual_rows(path: Path = MANUAL_CSV) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh) if any((value or "").strip() for value in row.values())]


def write_json(data, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")
    print(f"OK {filename} ({path.stat().st_size / 1024:.1f} KB)")


def _resolve_column(row: dict, options, default=None):
    if isinstance(options, str):
        return row.get(options, default)
    if isinstance(options, list):
        for name in options:
            if name in row and str(row.get(name) or "").strip():
                return row.get(name)
    return default


def _map_rows(rows: Iterable[dict], source: dict) -> list[dict]:
    columns = source.get("columns") or {}
    mapped = []
    for row in rows:
        item = {
            "league": _resolve_column(row, columns.get("league"), source.get("league")),
            "team": _resolve_column(row, columns.get("team")),
            "player": _resolve_column(row, columns.get("player")),
            "status": _resolve_column(row, columns.get("status"), source.get("status")),
            "cards": _resolve_column(row, columns.get("cards")),
            "threshold": _resolve_column(row, columns.get("threshold"), source.get("threshold")),
            "matchday": _resolve_column(row, columns.get("matchday")),
            "source_name": source.get("name"),
            "source_url": source.get("url"),
            "official": source.get("official", True),
            "verified": source.get("verified", source.get("official", True)),
            "notes": _resolve_column(row, columns.get("notes"), source.get("notes")),
        }
        mapped.append(item)
    return mapped


def _source_row(source: dict, **values) -> dict:
    row = {
        "league": source.get("league"),
        "source_name": source.get("name"),
        "source_url": source.get("url"),
        "official": source.get("official", True),
        "verified": source.get("verified", source.get("official", True)),
    }
    row.update(values)
    return row


def parse_premierleague_article(html: str, source: dict) -> list[dict]:
    lines = html_lines(html)
    rows = []
    positions = {"GK", "DEF", "MID", "FWD"}

    try:
        start = lines.index("Players suspended") + 1
    except ValueError:
        return rows
    end = next(
        (idx for idx in range(start, len(lines)) if lines[idx] == "Ineligible players" or lines[idx].startswith("Last updated")),
        len(lines),
    )
    table = [line for line in lines[start:end] if line not in {"Player", "Club", "Position", "Suspended for"}]

    i = 0
    while i < len(table):
        token = table[i]
        if i + 2 < len(table) and table[i + 1] in PL_CLUBS:
            player = token
            club = table[i + 1]
            cursor = i + 2
            if cursor < len(table) and table[cursor] in positions:
                cursor += 1
            matchday = table[cursor] if cursor < len(table) else None
            i = cursor + 1
        else:
            parts = token.split()
            club_index = next((idx for idx, part in enumerate(parts) if part in PL_CLUBS), None)
            if club_index is None or club_index == 0:
                i += 1
                continue
            player = " ".join(parts[:club_index]).strip()
            club = parts[club_index]
            rest = [part for part in parts[club_index + 1:] if part not in positions]
            matchday = " ".join(rest) if rest else None
            i += 1
        rows.append(_source_row(
            source,
            player=player,
            team=PL_CLUBS[club],
            status="suspended",
            matchday=matchday,
        ))
    return rows


def _parse_bundesliga_player_team(line: str):
    match = re.match(r"^(?P<player>.+?)\s+\((?P<team>[^)]+)\)", line)
    if not match:
        return None, None
    player = match.group("player").strip()
    team = BUNDESLIGA_TEAMS.get(match.group("team").strip(), match.group("team").strip())
    return player, team


def parse_bundesliga_article(html: str, source: dict) -> list[dict]:
    lines = article_body_lines(html)
    rows = []
    mode = None

    for raw in lines:
        line = raw.replace("–", "-")
        if line.startswith("Players suspended for Bundesliga"):
            mode = "suspended"
            continue
        if line.startswith("Players on nine yellow cards"):
            mode = "at_risk_9"
            continue
        if line.startswith("Players on four yellow cards"):
            mode = "at_risk_4"
            continue
        if line.startswith("Watch:") or line.startswith("Get the latest probable line-ups"):
            if mode == "suspended":
                mode = None
            if line.startswith("Get the latest probable line-ups"):
                break
            continue
        if mode is None:
            continue

        player, team = _parse_bundesliga_player_team(line)
        if not player or not team:
            continue

        if mode == "suspended":
            rows.append(_source_row(source, player=player, team=team, status="suspended", notes=line))
        elif mode == "at_risk_9":
            rows.append(_source_row(source, player=player, team=team, status="at_risk", cards=9, threshold=10))
        elif mode == "at_risk_4":
            rows.append(_source_row(source, player=player, team=team, status="at_risk", cards=4, threshold=5))
    return rows


def fetch_source_rows(source: dict, timeout: int = 45) -> list[dict]:
    """Fetch a configured official/verified source.

    Supported source types:
    - json: URL returns either a list of rows or {"items": [...]}.
    - csv: URL returns CSV with mappable columns.
    - html_table: pandas.read_html extracts tables; columns config maps table headers.
    - premierleague_article: official PL article parser.
    - bundesliga_article: official Bundesliga article parser.
    - manual_review: records the source but does not parse it.
    """
    kind = source.get("type")
    url = source.get("url")
    if kind in {"manual_review", None}:
        return []
    if not url:
        return []

    import requests

    print(f"Fetching {source.get('name') or url}")
    res = requests.get(url, timeout=timeout, headers={"User-Agent": "KICKDEX data updater/1.0"})
    res.raise_for_status()

    if kind == "premierleague_article":
        return parse_premierleague_article(res.text, source)

    if kind == "bundesliga_article":
        return parse_bundesliga_article(res.text, source)

    if kind == "json":
        payload = res.json()
        rows = payload.get("items", payload) if isinstance(payload, dict) else payload
        return _map_rows(rows or [], source)

    if kind == "csv":
        text = res.content.decode(source.get("encoding") or "utf-8-sig", errors="replace")
        rows = csv.DictReader(text.splitlines())
        return _map_rows(rows, source)

    if kind == "html_table":
        import pandas as pd

        tables = pd.read_html(res.text)
        table_index = int(source.get("table_index", 0))
        if table_index >= len(tables):
            return []
        rows = tables[table_index].fillna("").to_dict(orient="records")
        return _map_rows(rows, source)

    raise ValueError(f"Unsupported suspension source type: {kind}")


def fetch_configured_sources(path: Path = SOURCES_JSON, timeout: int = 45) -> list[dict]:
    config = read_json(path, {"sources": []})
    rows = []
    for source in config.get("sources", []) or []:
        try:
            rows.extend(fetch_source_rows(source, timeout=timeout))
        except Exception as exc:
            print(f"WARNING source failed: {source.get('name') or source.get('url')} - {exc}")
    return rows


def build_payload(fetch: bool = False, timeout: int = 45) -> dict:
    leagues = read_json(OUTPUT_DIR / "leagues.json", {})
    config = read_json(SOURCES_JSON, {"sources": []})
    rows = read_manual_rows()
    if fetch:
        rows.extend(fetch_configured_sources(timeout=timeout))
    return build_suspensions_payload(rows, leagues, source_catalog=config.get("sources", []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update official/verified suspension feed")
    parser.add_argument("--fetch", action="store_true", help="Fetch configured remote official/verified sources")
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args(argv)

    payload = build_payload(fetch=args.fetch, timeout=args.timeout)
    write_json(payload, "suspensions.json")
    print(
        "Suspensions feed: "
        f"{payload['totals']['items']} rows, "
        f"{payload['totals']['official']} official, "
        f"{payload['totals']['verified']} verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
