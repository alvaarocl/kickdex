"""
Check referee season coverage for the static frontend.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"


def _read_json(name: str, default):
    path = DATA_DIR / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-under", type=int, default=None, help="Fail if a required league has fewer season referees.")
    parser.add_argument("--required-leagues", nargs="*", default=None)
    args = parser.parse_args()

    referees = _read_json("referees.json", [])
    leagues = _read_json("leagues.json", {})
    required = set(args.required_leagues or leagues.keys())

    counts: dict[str, int] = {}
    for row in referees if isinstance(referees, list) else []:
        league = str(row.get("league") or "")
        season = row.get("season") or {}
        if league and int(season.get("matches") or 0) > 0:
            counts[league] = counts.get(league, 0) + 1

    print("REFEREE SEASON COVERAGE")
    failed = False
    for code in sorted(required):
        count = counts.get(code, 0)
        name = (leagues.get(code) or {}).get("name", code) if isinstance(leagues, dict) else code
        print(f"{code:>3} {name:<24} season_referees={count}")
        if args.fail_under is not None and count < args.fail_under:
            failed = True

    missing_required = sorted(required - set(counts))
    if missing_required:
        print(f"missing_required_leagues={','.join(missing_required)}")
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
