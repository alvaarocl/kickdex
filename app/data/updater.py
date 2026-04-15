"""
Descargador de datos históricos de football-data.co.uk.
Descarga SP1 y SP2 para todas las temporadas desde 04/05 hasta la actual.
Lógica inteligente: temporadas antiguas solo si no existen; actual, siempre.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

from app.config import (
    CURRENT_SEASON_CODE,
    DATA_DIR,
    FOOTBALL_DATA_BASE_URL,
    LEAGUES,
    SEASONS_RANGE,
)

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (KICKDEX / educational use)"}
_LAST_UPDATE_FILE = ".last_update.json"


def _season_codes() -> list[str]:
    codes = []
    for y in SEASONS_RANGE:
        codes.append(f"{y:02d}{(y+1):02d}")
    return codes


def _load_last_update(data_dir: Path) -> dict:
    p = data_dir / _LAST_UPDATE_FILE
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def _save_last_update(data_dir: Path, info: dict) -> None:
    p = data_dir / _LAST_UPDATE_FILE
    p.write_text(json.dumps(info, indent=2))


def update_data(force_current: bool = True) -> dict:
    """
    Descarga/actualiza los CSVs de partidos.

    Args:
        force_current: Si True, siempre re-descarga la temporada actual.

    Returns:
        Resumen con claves 'downloaded', 'skipped', 'failed'.
    """
    data_dir = Path(DATA_DIR)
    data_dir.mkdir(exist_ok=True)

    last_update = _load_last_update(data_dir)
    seasons = _season_codes()
    summary = {"downloaded": [], "skipped": [], "failed": []}

    logger.info("Verificando base de datos histórica (%d temporadas × %d ligas)…",
                len(seasons), len(LEAGUES))

    for season in seasons:
        for league_code in LEAGUES:
            filename = f"{league_code}_{season}.csv"
            filepath = data_dir / filename
            url = f"{FOOTBALL_DATA_BASE_URL}/{season}/{league_code}.csv"

            is_current = season == CURRENT_SEASON_CODE

            # Lógica: temporada antigua con archivo → saltar
            if not is_current and filepath.exists():
                summary["skipped"].append(filename)
                continue

            # Temporada actual: saltar si se descargó hoy (a menos que force)
            if is_current and filepath.exists() and not force_current:
                today = datetime.now().strftime("%Y-%m-%d")
                if last_update.get(filename) == today:
                    summary["skipped"].append(filename)
                    continue

            try:
                r = requests.get(url, headers=_HEADERS, timeout=15)
                if r.status_code == 200 and len(r.content) > 100:
                    filepath.write_bytes(r.content)
                    last_update[filename] = datetime.now().strftime("%Y-%m-%d")
                    summary["downloaded"].append(filename)
                    logger.info("  ✓ %s", filename)
                else:
                    summary["failed"].append(filename)
                    logger.debug("  – %s (HTTP %d, posiblemente aún no existe)", filename, r.status_code)
                time.sleep(0.4)
            except Exception as e:
                summary["failed"].append(filename)
                logger.warning("  ✗ %s: %s", filename, e)

    _save_last_update(data_dir, last_update)
    logger.info(
        "Actualización completada: %d descargados, %d saltados, %d fallidos",
        len(summary["downloaded"]),
        len(summary["skipped"]),
        len(summary["failed"]),
    )
    return summary
