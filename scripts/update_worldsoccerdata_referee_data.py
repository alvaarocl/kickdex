"""
Best-effort World Soccer Data referee season updater.

World Soccer Data exposes current-season referee pages for the major leagues we
track. League pages provide referee names and match counts; individual referee
pages provide yellow/red card totals. This feeds the "season" window only.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import CURRENT_SEASON_START, CURRENT_SEASON_YEAR, DATA_DIR, LEAGUES, WORLDSOCCERDATA_REFEREE_PATHS

BASE_URL = "https://www.worldsoccerdata.com"
READER_BASE_URL = "https://r.jina.ai/"
OUT_PATH = Path(DATA_DIR) / "referees_season.csv"
FIELDNAMES = [
    "league",
    "league_name",
    "referee",
    "matches",
    "yellow_cards",
    "second_yellow_cards",
    "red_cards",
    "source",
    "updated_at",
]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _request(url: str, timeout: int) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.RequestException:
        response = None
    # Desde 2026-08 el WAF (Mod_Security) responde 406 a los runners de
    # GitHub; antes solo se caía al lector con 403/429 y cada ejecución
    # saltaba todas las ligas en silencio. Cualquier bloqueo → lector.
    if response is not None and response.status_code < 400:
        return response.text

    reader_url = f"{READER_BASE_URL}{url}"
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            reader = requests.get(reader_url, headers=HEADERS, timeout=timeout)
            if reader.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            reader.raise_for_status()
            return reader.text
        except Exception as exc:
            last_error = exc
            time.sleep(5 * (attempt + 1))
    if last_error:
        raise last_error
    if response is not None:
        response.raise_for_status()
    raise RuntimeError(f"No se pudo leer {url}")


def _num(value: Any) -> int:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else 0


def _parse_referee_links(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    rows_by_href: dict[str, dict[str, Any]] = {}
    for link in soup.select("table.stat-time a.ref-link[href*='/referees/']"):
        row = link.find_parent("tr")
        cells = row.find_all("td") if row else []
        if len(cells) < 2:
            continue
        name = link.get_text(" ", strip=True)
        href = link.get("href")
        matches = _num(cells[1].get_text(" ", strip=True))
        if name and href and matches > 0:
            absolute_href = urljoin(BASE_URL, href)
            current = rows_by_href.get(absolute_href)
            if current is None or matches > int(current.get("matches") or 0):
                rows_by_href[absolute_href] = {"referee": name, "href": absolute_href, "matches": matches}

    for name, href, matches_raw in re.findall(
        r"\|\s*\[([^\]]+)\]\((https?://www\.worldsoccerdata\.com/stats/[^)]+/referees/[^)]+)\)\s*\|\s*(\d+)\s*\|",
        html,
    ):
        matches = int(matches_raw)
        href = "https://" + href.split("://", 1)[1]  # el lector devuelve http://
        current = rows_by_href.get(href)
        if current is None or matches > int(current.get("matches") or 0):
            rows_by_href[href] = {"referee": name.strip(), "href": href, "matches": matches}
    return sorted(rows_by_href.values(), key=lambda row: (-int(row["matches"]), str(row["referee"])))


def _parse_cards(html: str) -> tuple[int, int] | None:
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    match = re.search(
        r"Cards\s*\(avg\)\s+[\d.]+\s+YC\s+·?\s*[\d.]+\s+RC\s+Totals:\s*(\d+)Y\s*/\s*(\d+)R",
        text,
    )
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


MATCHES_PATH = Path(DATA_DIR) / "referees_wsd_matches.csv"
MATCH_FIELDNAMES = [
    "date",
    "league",
    "referee",
    "home",
    "away",
    "home_score",
    "away_score",
    "yellow_cards",
    "red_cards",
    "season",
    "source",
    "updated_at",
]
_SEASON_HEADING = re.compile(r"Matches\s+(\d{4})\s*[-–]\s*(\d{4})", re.I)


def _table_lines(text: str) -> list[str]:
    """Normaliza la página a líneas tipo markdown ("### ..." y "| a | b |").
    El lector r.jina.ai ya devuelve markdown; el HTML directo se convierte."""
    head = text[:2000].lower()
    if "<html" not in head and "<table" not in text.lower():
        return text.splitlines()
    soup = BeautifulSoup(text, "html.parser")
    lines = []
    for node in soup.find_all(["h1", "h2", "h3", "h4", "tr"]):
        if node.name == "tr":
            cells = [c.get_text(" ", strip=True) for c in node.find_all(["td", "th"])]
            lines.append("| " + " | ".join(cells) + " |")
        else:
            lines.append("### " + node.get_text(" ", strip=True))
    return lines


def _parse_match_log(text: str) -> list[dict[str, Any]]:
    """Partidos del perfil de un árbitro: tablas "Matches 2026-2027", etc.
    Fila: | 20 Sep 2026 | [Home vs Away](url) | 2-1 (0-0) | ... | 4 1 |
    (la última columna son amarillas y rojas)."""
    season = None
    out = []
    for line in _table_lines(text):
        stripped = line.strip()
        if not stripped.startswith("|"):
            heading = _SEASON_HEADING.search(stripped)
            if stripped.startswith("#"):
                season = int(heading.group(1)) if heading else None
            continue
        if season is None:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue
        try:
            date = datetime.strptime(cells[0], "%d %b %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        teams = re.sub(r"\]\([^)]*\)", "", cells[1]).lstrip("[")
        if " vs " not in teams:
            continue
        home, away = [t.strip() for t in teams.split(" vs ", 1)]
        score = re.match(r"(\d+)\s*-\s*(\d+)", cells[2])
        cards = re.match(r"(\d+)\s+(\d+)$", cells[-1])
        if not score or not cards:
            continue
        out.append({
            "date": date,
            "home": home,
            "away": away,
            "home_score": int(score.group(1)),
            "away_score": int(score.group(2)),
            "yellow_cards": int(cards.group(1)),
            "red_cards": int(cards.group(2)),
            "season": season,
        })
    return out


def fetch_league(
    code: str,
    path: str,
    season: int,
    timeout: int,
    sleep_seconds: float,
    concurrency: int = 6,
    existing_season: dict[str, dict[str, Any]] | None = None,
    existing_logged: dict[str, int] | None = None,
    deadline: float | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    """Devuelve (filas de temporada, partidos nuevos, árbitros re-descargados).

    Incremental: la tabla de la liga ya trae los PJ de cada árbitro; solo se
    descarga el perfil de quien tiene partidos nuevos desde la última vez.
    """
    league_url = f"{BASE_URL}/stats/{path}/referees/{season}"
    links = _parse_referee_links(_request(league_url, timeout))
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    existing_season = existing_season or {}
    existing_logged = existing_logged or {}
    rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []
    refreshed: set[str] = set()

    to_fetch = []
    for item in links:
        prev = existing_season.get(item["referee"])
        up_to_date = (
            prev is not None
            and int(float(prev.get("matches") or 0)) == item["matches"]
            and existing_logged.get(item["referee"], 0) >= item["matches"]
        )
        if up_to_date:
            rows.append(prev)
        else:
            to_fetch.append(item)

    def fetch_profile(item: dict[str, Any]):
        if deadline and time.monotonic() > deadline:
            return item, None, None
        try:
            page = _request(f"{item['href']}?season={season}", timeout)
        except Exception as exc:
            print(f"SKIP WorldSoccerData {code} {item['referee']}: {exc}")
            return item, None, None
        return item, _parse_cards(page), _parse_match_log(page)

    workers = max(1, min(concurrency, len(to_fetch) or 1))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_profile, item) for item in to_fetch]
        for future in as_completed(futures):
            item, cards, log = future.result()
            if sleep_seconds:
                time.sleep(sleep_seconds)
            if cards is None and not log:
                prev = existing_season.get(item["referee"])
                if prev is not None:
                    rows.append(prev)  # mejor el dato anterior que nada
                continue
            current = [m for m in (log or []) if m["season"] == season]
            if current and len(current) == item["matches"]:
                yellow_cards = sum(m["yellow_cards"] for m in current)
                red_cards = sum(m["red_cards"] for m in current)
            elif cards is not None:
                yellow_cards, red_cards = cards
            else:
                continue
            rows.append({
                "league": code,
                "league_name": LEAGUES.get(code, code),
                "referee": item["referee"],
                "matches": item["matches"],
                "yellow_cards": yellow_cards,
                "second_yellow_cards": 0,
                "red_cards": red_cards,
                "source": "worldsoccerdata",
                "updated_at": updated_at,
            })
            refreshed.add(item["referee"])
            for m in log or []:
                match_rows.append({**m, "league": code, "referee": item["referee"],
                                   "source": "worldsoccerdata", "updated_at": updated_at})
    rows.sort(key=lambda row: (-int(float(row.get("matches") or 0)), str(row.get("referee") or "")))
    print(f"   {code}: {len(links)} árbitros, {len(to_fetch)} perfiles a descargar, {len(refreshed)} actualizados")
    return rows, match_rows, refreshed


def write_rows(rows: list[dict[str, Any]], path: Path = OUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def _load_existing_rows(path: Path = OUT_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def _write_csv(rows: list[dict[str, Any]], path: Path, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def update_worldsoccerdata_referees(
    leagues: list[str],
    season: int,
    timeout: int = 30,
    sleep_seconds: float = 0.2,
    concurrency: int = 6,
    max_seconds: float | None = None,
    full: bool = False,
) -> int:
    deadline = time.monotonic() + max_seconds if max_seconds else None
    existing = _load_existing_rows()
    existing_matches = [] if full else _load_existing_rows(MATCHES_PATH)
    rows: list[dict[str, Any]] = []
    new_matches: list[dict[str, Any]] = []
    refreshed_by_league: dict[str, set[str]] = {}

    for code in leagues:
        path = WORLDSOCCERDATA_REFEREE_PATHS.get(code)
        if not path:
            print(f"SKIP WorldSoccerData {code}: sin path")
            continue
        if deadline and time.monotonic() > deadline:
            print(f"SKIP WorldSoccerData {code}: presupuesto de tiempo agotado (sigue en la próxima ejecución)")
            continue
        # Solo filas ya validadas como de esta temporada sirven para el modo incremental.
        prev_season = {} if full else {
            r["referee"]: r for r in existing
            if r.get("league") == code and str(r.get("updated_at", ""))[:10] >= CURRENT_SEASON_START
        }
        logged: dict[str, int] = {}
        for m in existing_matches:
            if m.get("league") == code and str(m.get("season")) == str(season):
                logged[m["referee"]] = logged.get(m["referee"], 0) + 1
        try:
            league_rows, league_matches, refreshed = fetch_league(
                code, path, season, timeout, sleep_seconds, concurrency,
                existing_season=prev_season, existing_logged=logged, deadline=deadline,
            )
        except Exception as exc:
            print(f"SKIP WorldSoccerData {code}: {exc}")
            continue
        print(f"OK WorldSoccerData {code}: {len(league_rows)} referees")
        rows.extend(league_rows)
        new_matches.extend(league_matches)
        refreshed_by_league[code] = refreshed

    if rows:
        refreshed_leagues = {row.get("league") for row in rows}
        preserve = [row for row in existing if row.get("league") not in refreshed_leagues]
        write_rows(preserve + rows)

    if new_matches or refreshed_by_league:
        # Los perfiles re-descargados sustituyen sus partidos; el resto se conserva.
        kept = [
            m for m in existing_matches
            if m.get("referee") not in refreshed_by_league.get(m.get("league"), set())
        ]
        merged: dict[tuple, dict[str, Any]] = {}
        for m in kept + new_matches:
            merged[(m.get("league"), m.get("date"), m.get("home"), m.get("away"))] = m
        out = sorted(merged.values(), key=lambda m: (str(m.get("league")), str(m.get("date"))), reverse=True)
        _write_csv(out, MATCHES_PATH, MATCH_FIELDNAMES)
        print(f"OK WorldSoccerData partidos={len(out)} path={MATCHES_PATH}")
    print(f"OK WorldSoccerData referees={len(rows)} path={OUT_PATH}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(WORLDSOCCERDATA_REFEREE_PATHS.keys()))
    parser.add_argument("--season", type=int, default=CURRENT_SEASON_YEAR)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--max-seconds", type=float, default=None,
                        help="Presupuesto de tiempo; lo pendiente se completa en la siguiente ejecución")
    parser.add_argument("--full", action="store_true", help="Ignora la caché incremental")
    args = parser.parse_args()
    update_worldsoccerdata_referees(args.leagues, args.season, args.timeout, args.sleep, args.concurrency,
                                    max_seconds=args.max_seconds, full=args.full)


if __name__ == "__main__":
    main()
