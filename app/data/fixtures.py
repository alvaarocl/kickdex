"""
Fetcher de partidos próximos y resultados recientes.

Estrategia: football-data.co.uk actualiza los CSVs por temporada (SP1_2526.csv,
SP2_2526.csv) añadiendo los fixtures de la próxima jornada sin
resultado (FTHG/FTAG NaN) 2-3 días antes del partido. Este módulo:

1. Re-descarga los CSVs actuales con TTL corto (1h).
2. Filtra filas sin FTHG → upcoming fixtures.
3. Devuelve también los resultados recientes (últimos N días).

No requiere API key ni scraping frágil.
"""

from __future__ import annotations

import io
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

from app.config import (
    CURRENT_SEASON_CODE,
    DATA_DIR,
    FOOTBALL_DATA_BASE_URL,
    LEAGUES,
)
from app.data.loader import normalize_team_name

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (KICKDEX / educational use)"}


@dataclass
class Fixture:
    """Un partido (jugado o por jugar)."""
    league_code: str          # "SP1" / "SP2"
    league_name: str          # "La Liga" / "Segunda División"
    date: pd.Timestamp
    time: str                 # "21:00" o ""
    home: str                 # normalizado
    away: str                 # normalizado
    home_score: int | None    # None si no jugado
    away_score: int | None

    @property
    def is_played(self) -> bool:
        return self.home_score is not None and self.away_score is not None

    @property
    def result_str(self) -> str:
        if self.is_played:
            return f"{self.home_score}-{self.away_score}"
        return "vs"


def _download_current_csv(league_code: str) -> pd.DataFrame | None:
    """Descarga el CSV de la temporada actual con latencia baja."""
    url = f"{FOOTBALL_DATA_BASE_URL}/{CURRENT_SEASON_CODE}/{league_code}.csv"
    try:
        r = requests.get(url, headers=_HEADERS, timeout=10)
        if r.status_code != 200 or len(r.content) < 100:
            logger.warning("Fixtures: no pude descargar %s (HTTP %d)", url, r.status_code)
            return None
        for enc in ("utf-8-sig", "utf-8", "latin1"):
            try:
                df = pd.read_csv(io.StringIO(r.content.decode(enc)), low_memory=False)
                df.columns = [c.lstrip("\ufeff").strip() for c in df.columns]
                return df
            except Exception:
                continue
    except Exception as e:
        logger.warning("Fixtures: error descargando %s: %s", url, e)
    return None


def _load_local_csv(league_code: str) -> pd.DataFrame | None:
    """Fallback: lee el CSV local si la descarga falla."""
    path = Path(DATA_DIR) / f"{league_code}_{CURRENT_SEASON_CODE}.csv"
    if not path.exists():
        return None
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False)
            df.columns = [c.lstrip("\ufeff").strip() for c in df.columns]
            return df
        except Exception:
            continue
    return None


def _row_to_fixture(row: pd.Series, league_code: str) -> Fixture | None:
    try:
        date = pd.to_datetime(row.get("Date"), dayfirst=True, errors="coerce")
        if pd.isna(date):
            return None
        home = normalize_team_name(row.get("HomeTeam"))
        away = normalize_team_name(row.get("AwayTeam"))
        if not isinstance(home, str) or not isinstance(away, str):
            return None

        def _i(col):
            v = row.get(col)
            return int(v) if pd.notna(v) else None

        return Fixture(
            league_code=league_code,
            league_name=LEAGUES.get(league_code, league_code),
            date=date,
            time=str(row.get("Time", "") or "").strip(),
            home=home,
            away=away,
            home_score=_i("FTHG"),
            away_score=_i("FTAG"),
        )
    except Exception:
        return None


def _persist_download(league_code: str, df: pd.DataFrame) -> None:
    """Guarda el CSV descargado para que el loader principal lo vea fresco."""
    try:
        path = Path(DATA_DIR) / f"{league_code}_{CURRENT_SEASON_CODE}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
    except Exception as e:
        logger.debug("No se pudo persistir %s: %s", league_code, e)


def fetch_all_fixtures(force: bool = False) -> list[Fixture]:
    """
    Descarga todos los fixtures (jugados y por jugar) de SP1 y SP2 temporada actual.
    Retorna lista combinada ordenada por fecha.
    """
    out: list[Fixture] = []
    for league_code in LEAGUES:
        df = _download_current_csv(league_code)
        if df is None:
            df = _load_local_csv(league_code)
        if df is None:
            continue
        if force or True:
            _persist_download(league_code, df)
        for _, row in df.iterrows():
            fx = _row_to_fixture(row, league_code)
            if fx is not None:
                out.append(fx)
        time.sleep(0.3)
    out.sort(key=lambda f: f.date)
    return out


def get_upcoming_fixtures(
    force: bool = False,
    max_days_ahead: int = 14,
) -> list[Fixture]:
    """Fixtures sin resultado dentro de los próximos `max_days_ahead` días."""
    all_fx = fetch_all_fixtures(force=force)
    horizon = pd.Timestamp(datetime.now()) + pd.Timedelta(days=max_days_ahead)
    return [f for f in all_fx if not f.is_played and f.date <= horizon]


def get_recent_results(
    force: bool = False,
    days_back: int = 7,
) -> list[Fixture]:
    """Últimos N días de resultados jugados."""
    all_fx = fetch_all_fixtures(force=force)
    cutoff = pd.Timestamp(datetime.now()) - pd.Timedelta(days=days_back)
    recent = [f for f in all_fx if f.is_played and f.date >= cutoff]
    recent.sort(key=lambda f: f.date, reverse=True)
    return recent


def get_todays_fixtures(force: bool = False) -> list[Fixture]:
    """Partidos de hoy (jugados o por jugar)."""
    all_fx = fetch_all_fixtures(force=force)
    today = pd.Timestamp(datetime.now().date())
    tomorrow = today + pd.Timedelta(days=1)
    return [f for f in all_fx if today <= f.date < tomorrow]
