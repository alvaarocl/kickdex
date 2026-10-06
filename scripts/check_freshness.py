"""
Vigilante de frescura de datos (último paso del workflow diario).

La mayoría de pasos del workflow son `continue-on-error` para no tumbar la web
si una fuente falla — pero eso hacía que los fallos fueran silenciosos (p. ej.
players.json congelado semanas, árbitros de World Soccer Data sin actualizar
desde agosto). Este script falla (exit 1) si algún dominio lleva demasiado sin
actualizarse; GitHub avisa por email de los workflows programados que fallan.
Se ejecuta DESPUÉS del commit, así nunca bloquea la publicación de datos.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"

# dominio -> (cómo leer la fecha, máximo de horas permitido)
LIMITS_HOURS = {
    "meta.json": 36,
    "fixtures.json": 36,
    "standings.json": 48,
    "live_scores.json": 24,  # solo respaldo: el directo real va por ESPN desde el navegador
    "player_coverage.json (scrape)": 24 * 5,
    "referees_matches.csv (ESPN)": 24 * 4,
}


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def _json_ts(name: str, *path: str) -> datetime | None:
    try:
        node = json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return None
    for key in path:
        node = (node or {}).get(key) if isinstance(node, dict) else None
    return _parse(node)


def collect() -> dict[str, datetime | None]:
    referees = None
    path = ROOT / "DATOS" / "referees_matches.csv"
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            stamps = [_parse(r.get("updated_at")) for r in csv.DictReader(fh)]
        referees = max((s for s in stamps if s), default=None)
    return {
        "meta.json": _json_ts("meta.json", "updated_at"),
        "fixtures.json": _json_ts("fixtures.json", "meta", "updated_at"),
        "standings.json": _json_ts("standings.json", "updated_at"),
        "live_scores.json": _json_ts("live_scores.json", "updated_at"),
        "player_coverage.json (scrape)": _json_ts("player_coverage.json", "scraped_at"),
        "referees_matches.csv (ESPN)": referees,
    }


def check(now: datetime | None = None) -> list[str]:
    now = now or datetime.now(timezone.utc)
    problems = []
    for name, stamp in collect().items():
        limit = LIMITS_HOURS[name]
        if stamp is None:
            problems.append(f"{name}: sin fecha de actualización")
            continue
        age = (now - stamp).total_seconds() / 3600
        status = "OK " if age <= limit else "OLD"
        print(f"  {status} {name}: hace {age:.1f} h (máx {limit} h)")
        if age > limit:
            problems.append(f"{name}: {age:.0f} h sin actualizar (máx {limit} h)")
    return problems


def main() -> int:
    problems = check()
    if problems:
        print("\nDATOS DESACTUALIZADOS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nFRESHNESS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
