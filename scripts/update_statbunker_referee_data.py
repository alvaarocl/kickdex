"""
Best-effort StatBunker referee season updater.

StatBunker exposes public 25/26 referee-card aggregate pages for several major
leagues. They do not provide match-by-match referee rows, so this file only
feeds the "season" window. It exits successfully on network/parser failures so
the data workflow remains reliable.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import DATA_DIR, LEAGUES, STATBUNKER_REFEREE_COMP_IDS

OUT_PATH = Path(DATA_DIR) / "referees_season.csv"
URL = "https://www.statbunker.com/competitions/RefereeYellowCards"
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


def _num(value: Any) -> float:
    text = str(value or "").strip()
    if text in {"", "-", "--", "nan", "None"}:
        return 0.0
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else 0.0


def _find_referee_table(html: str) -> pd.DataFrame:
    tables = pd.read_html(StringIO(html))
    for table in tables:
        columns = [str(c).strip() for c in table.columns]
        if "Referee" in columns and "P" in columns:
            table.columns = columns
            return table
    return pd.DataFrame()


def _download_html(comp_id: int, timeout: int) -> str:
    response = requests.get(
        URL,
        params={"comp_id": comp_id},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def fetch_league(code: str, comp_id: int, timeout: int) -> list[dict[str, Any]]:
    html = _download_html(comp_id, timeout)
    table = _find_referee_table(html)
    if table.empty:
        return []

    rows: list[dict[str, Any]] = []
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for _, row in table.iterrows():
        referee = str(row.get("Referee", "") or "").strip()
        matches = int(_num(row.get("P")))
        if not referee or matches <= 0 or referee.lower() in {"nan", "referee"}:
            continue
        rows.append(
            {
                "league": code,
                "league_name": LEAGUES.get(code, code),
                "referee": referee,
                "matches": matches,
                "yellow_cards": int(_num(row.get("Yellow Card", row.get("YC")))),
                "second_yellow_cards": int(_num(row.get("Red and Yellow Card", row.get("2YC")))),
                "red_cards": int(_num(row.get("Red Card", row.get("RC")))),
                "source": "statbunker",
                "updated_at": updated_at,
            }
        )
    return rows


def write_rows(rows: list[dict[str, Any]], path: Path = OUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def update_statbunker_referees(leagues: list[str], timeout: int = 45) -> int:
    rows: list[dict[str, Any]] = []
    for code in leagues:
        comp_id = STATBUNKER_REFEREE_COMP_IDS.get(code)
        if not comp_id:
            print(f"SKIP StatBunker {code}: sin comp_id")
            continue
        try:
            league_rows = fetch_league(code, comp_id, timeout)
        except Exception as exc:
            print(f"SKIP StatBunker {code}: {exc}")
            continue
        print(f"OK StatBunker {code}: {len(league_rows)} referees")
        rows.extend(league_rows)

    if rows:
        write_rows(rows)
    print(f"OK StatBunker referees={len(rows)} path={OUT_PATH}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leagues", nargs="*", default=list(STATBUNKER_REFEREE_COMP_IDS.keys()))
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()
    update_statbunker_referees(args.leagues, timeout=args.timeout)


if __name__ == "__main__":
    main()
