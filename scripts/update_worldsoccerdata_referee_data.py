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

from app.config import CURRENT_SEASON_YEAR, DATA_DIR, LEAGUES, WORLDSOCCERDATA_REFEREE_PATHS

BASE_URL = "https://www.worldsoccerdata.com"
READER_BASE_URL = "https://r.jina.ai/http://"
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
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    if response.status_code not in {403, 429}:
        response.raise_for_status()
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
    response.raise_for_status()
    return response.text


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
        r"\|\s*\[([^\]]+)\]\((https://www\.worldsoccerdata\.com/stats/[^)]+/referees/[^)]+)\)\s*\|\s*(\d+)\s*\|",
        html,
    ):
        matches = int(matches_raw)
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


def fetch_league(
    code: str,
    path: str,
    season: int,
    timeout: int,
    sleep_seconds: float,
    concurrency: int = 6,
) -> list[dict[str, Any]]:
    league_url = f"{BASE_URL}/stats/{path}/referees/{season}"
    links = _parse_referee_links(_request(league_url, timeout))
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows: list[dict[str, Any]] = []

    def fetch_profile(item: dict[str, Any]) -> dict[str, Any] | None:
        try:
            cards = _parse_cards(_request(f"{item['href']}?season={season}", timeout))
        except Exception as exc:
            print(f"SKIP WorldSoccerData {code} {item['referee']}: {exc}")
            return None
        if cards is None:
            print(f"SKIP WorldSoccerData {code} {item['referee']}: cards not found")
            return None
        yellow_cards, red_cards = cards
        return {
            "league": code,
            "league_name": LEAGUES.get(code, code),
            "referee": item["referee"],
            "matches": item["matches"],
            "yellow_cards": yellow_cards,
            "second_yellow_cards": 0,
            "red_cards": red_cards,
            "source": "worldsoccerdata",
            "updated_at": updated_at,
        }

    workers = max(1, min(concurrency, len(links) or 1))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_profile, item) for item in links]
        for future in as_completed(futures):
            row = future.result()
            if row:
                rows.append(row)
            if sleep_seconds:
                time.sleep(sleep_seconds)
    rows.sort(key=lambda row: (-int(row.get("matches") or 0), str(row.get("referee") or "")))
    return rows


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


def update_worldsoccerdata_referees(
    leagues: list[str],
    season: int,
    timeout: int = 30,
    sleep_seconds: float = 0.2,
    concurrency: int = 6,
) -> int:
    rows: list[dict[str, Any]] = []
    requested = set(leagues)
    existing = _load_existing_rows()
    for code in leagues:
        path = WORLDSOCCERDATA_REFEREE_PATHS.get(code)
        if not path:
            print(f"SKIP WorldSoccerData {code}: sin path")
            continue
        try:
            league_rows = fetch_league(code, path, season, timeout, sleep_seconds, concurrency)
        except Exception as exc:
            print(f"SKIP WorldSoccerData {code}: {exc}")
            continue
        print(f"OK WorldSoccerData {code}: {len(league_rows)} referees")
        rows.extend(league_rows)

    if rows:
        refreshed = {row.get("league") for row in rows}
        preserve = [row for row in existing if row.get("league") not in refreshed]
        rows = preserve + rows
        write_rows(rows)
    print(f"OK WorldSoccerData referees={len(rows)} path={OUT_PATH}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(WORLDSOCCERDATA_REFEREE_PATHS.keys()))
    parser.add_argument("--season", type=int, default=CURRENT_SEASON_YEAR)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--concurrency", type=int, default=6)
    args = parser.parse_args()
    update_worldsoccerdata_referees(args.leagues, args.season, args.timeout, args.sleep, args.concurrency)


if __name__ == "__main__":
    main()
