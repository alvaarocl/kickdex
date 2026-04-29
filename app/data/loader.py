"""
Data Loader — carga, normaliza y cachea todos los CSVs históricos.
Garantías:
- Encoding: intenta utf-8, fallback a latin1
- Fechas: parser robusto sin hardcodear formato
- Nombres de equipos normalizados a nombres canónicos
- Sin duplicados exactos
- Columnas estándar siempre presentes (NaN si no existen en el CSV)
"""

import pandas as pd
import numpy as np
import unicodedata
import logging
from pathlib import Path
from functools import lru_cache

from app.config import (
    DATA_DIR, CURRENT_SEASON_START, CURRENT_SEASON_CODE,
    LEAGUES, TEAM_ALIASES, MIN_MATCHES_FOR_STATS,
)

logger = logging.getLogger(__name__)

# Columnas estándar que siempre deben existir (con fallback a NaN)
REQUIRED_COLS = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Div"]
OPTIONAL_COLS = [
    "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR",
    "HTHG", "HTAG",
]


def _normalize_str(s: str) -> str:
    """Minúsculas + quita tildes."""
    if not isinstance(s, str):
        return str(s)
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower().strip())
        if unicodedata.category(c) != "Mn"
    )


def normalize_team_name(name: str) -> str:
    """Devuelve el nombre canónico del equipo o el original si no hay alias."""
    if not isinstance(name, str):
        return name
    return TEAM_ALIASES.get(_normalize_str(name), name)


def _load_single_csv(path: Path) -> pd.DataFrame | None:
    """Carga un CSV con fallback de encoding y normaliza columnas básicas."""
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False, on_bad_lines="skip")
            # Marcar de qué liga/temporada viene
            stem = path.stem  # e.g. "SP1_2526"
            parts = stem.split("_")
            if len(parts) == 2:
                df["_league_code"] = parts[0]
                df["_season_code"] = parts[1]
            else:
                # Archivos como "SP1.csv" sin código de temporada
                df["_league_code"] = stem
                df["_season_code"] = ""
            return df
        except Exception:
            continue
    logger.warning("No se pudo cargar %s", path.name)
    return None


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parsea la columna Date manejando múltiples formatos sin hardcodear año."""
    if "Date" not in df.columns:
        return df
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    # Eliminar filas sin fecha válida
    bad = df["Date"].isna().sum()
    if bad > 0:
        logger.debug("Eliminadas %d filas con fecha inválida", bad)
        df = df.dropna(subset=["Date"])
    return df


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza que todas las columnas opcionales existan (NaN si falta)."""
    for col in OPTIONAL_COLS:
        if col not in df.columns:
            df[col] = np.nan
    return df


def _normalize_teams(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica normalización de nombres a HomeTeam y AwayTeam."""
    df = df.copy()
    df["HomeTeam"] = df["HomeTeam"].apply(normalize_team_name)
    df["AwayTeam"] = df["AwayTeam"].apply(normalize_team_name)
    return df


def _add_league_label(df: pd.DataFrame) -> pd.DataFrame:
    """Añade columna Liga con nombre legible."""
    df = df.copy()
    if "_league_code" in df.columns:
        df["Liga"] = df["_league_code"].map(LEAGUES).fillna(df["_league_code"])
    return df


@lru_cache(maxsize=1)
def load_matches() -> pd.DataFrame:
    """
    Carga y normaliza TODOS los CSVs históricos de la carpeta datos/.
    Usa lru_cache: solo se ejecuta una vez por sesión de Python.

    Returns:
        DataFrame ordenado por fecha con columnas estándar garantizadas.
    """
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        logger.error("Carpeta de datos no encontrada: %s", DATA_DIR)
        return pd.DataFrame()

    # Solo archivos con código de temporada (SP1_2526.csv), excluir SP1.csv y jugadores
    csv_files = sorted([
        f for f in data_path.glob("*.csv")
        if "_" in f.stem and "jugadores" not in f.name
    ])

    if not csv_files:
        logger.error("No se encontraron CSVs en %s", DATA_DIR)
        return pd.DataFrame()

    dfs = []
    for f in csv_files:
        df = _load_single_csv(f)
        if df is None or df.empty:
            continue
        # Solo necesitamos las columnas clave + opcionales
        missing_req = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing_req:
            logger.debug("CSV %s sin columnas: %s — omitido", f.name, missing_req)
            continue
        dfs.append(df)

    if not dfs:
        logger.error("Ningún CSV válido encontrado")
        return pd.DataFrame()

    full = pd.concat(dfs, ignore_index=True)

    # Pipeline de limpieza
    full = _parse_dates(full)
    full = _ensure_columns(full)
    full = _normalize_teams(full)
    full = _add_league_label(full)

    # Eliminar duplicados exactos (misma fecha + equipos)
    before = len(full)
    full = full.drop_duplicates(subset=["Date", "HomeTeam", "AwayTeam"])
    after = len(full)
    if before != after:
        logger.info("Eliminados %d registros duplicados", before - after)

    full = full.sort_values("Date", ascending=True).reset_index(drop=True)

    logger.info(
        "Datos cargados: %d partidos (%d–%d)",
        len(full),
        full["Date"].dt.year.min(),
        full["Date"].dt.year.max(),
    )
    return full


def get_current_season(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra solo partidos de la temporada actual."""
    if df is None or df.empty or "Date" not in df.columns:
        return pd.DataFrame()
    return df[df["Date"] >= CURRENT_SEASON_START].copy()


def get_team_list(df: pd.DataFrame, recent_only: bool = True) -> list[str]:
    """
    Lista de equipos disponibles.
    Si recent_only=True, solo equipos que han jugado en la temporada actual.
    """
    if df is None or df.empty or "HomeTeam" not in df.columns or "AwayTeam" not in df.columns:
        return []

    if recent_only:
        current = get_current_season(df)
        if current.empty:
            pass  # fallback a todos
        else:
            teams = set(current["HomeTeam"].dropna()) | set(current["AwayTeam"].dropna())
            return sorted(teams)

    teams = set(df["HomeTeam"].dropna()) | set(df["AwayTeam"].dropna())
    return sorted(teams)


def _load_players_legacy() -> pd.DataFrame:
    """
    Carga el CSV de estadísticas de jugadores.
    Devuelve DataFrame vacío si no existe.
    """
    path = Path(DATA_DIR) / "jugadores_raw.csv"
    if not path.exists():
        logger.warning("jugadores_raw.csv no encontrado en %s", DATA_DIR)
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, low_memory=False)
        df.columns = [str(c).lower().strip() for c in df.columns]
        if "squad" in df.columns:
            df = df.rename(columns={"squad": "team"})
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            # Solo temporada actual
            df = df[df["date"] >= CURRENT_SEASON_START]
        # Normalizar nombres de equipo
        if "team" in df.columns:
            df["team"] = df["team"].apply(normalize_team_name)
        # Asegurar columnas numéricas
        for col in ["sh", "sot", "fls", "crdy", "gls", "ast", "min"]:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return df
    except Exception as e:
        logger.error("Error al cargar jugadores: %s", e)
        return pd.DataFrame()

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex/object columns from soccerdata/FBref into simple names."""
    df = df.copy()
    cols = []
    for col in df.columns:
        if isinstance(col, tuple):
            parts = [str(p).strip() for p in col if str(p).strip() and not str(p).startswith("Unnamed")]
            cols.append("_".join(parts).lower())
        else:
            cols.append(str(col).strip().lower())
    df.columns = cols
    return df


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _normalise_player_frame(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Normalize player CSVs into the schema used by the static frontend."""
    if df is None or df.empty:
        return pd.DataFrame()

    df = _flatten_columns(df)
    rename = {
        "squad": "team",
        "club": "team",
        "team_name": "team",
        "player_name": "player",
        "match": "game",
        "performance_gls": "gls",
        "performance_ast": "ast",
        "performance_sh": "sh",
        "performance_sot": "sot",
        "performance_crdy": "crdy",
        "performance_crdr": "crdr",
        "performance_fls": "fls",
        "playing_time_min": "min",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "date" not in df.columns and "game" in df.columns:
        df["date"] = df["game"].astype(str).str.extract(r"(\d{4}-\d{2}-\d{2})", expand=False)

    required = {"team", "player"}
    if not required.issubset(df.columns):
        logger.warning("CSV de jugadores omitido (%s): faltan columnas %s", source, sorted(required - set(df.columns)))
        return pd.DataFrame()

    out = pd.DataFrame()
    out["team"] = df["team"].apply(normalize_team_name)
    out["player"] = df["player"].astype(str).str.strip()
    out["date"] = pd.to_datetime(df["date"], errors="coerce") if "date" in df.columns else pd.NaT
    source_league = Path(source).stem.upper()
    if "league" in df.columns:
        league = df["league"].fillna("").astype(str).replace({"nan": "", "None": ""})
        out["league"] = league.where(league.astype(bool), source_league)
    else:
        out["league"] = source_league

    for col in ["sh", "sot", "fls", "crdy", "crdr", "gls", "ast", "min"]:
        src = _first_existing(df, [col, col.upper(), col.capitalize()])
        out[col] = pd.to_numeric(df[src], errors="coerce").fillna(0.0) if src else 0.0

    out = out[(out["team"].astype(bool)) & (out["player"].astype(bool))]
    if out["date"].notna().any():
        out = out[(out["date"].isna()) | (out["date"] >= CURRENT_SEASON_START)]
    return out


def _read_player_csv(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            continue
    logger.warning("No se pudo cargar CSV de jugadores: %s", path)
    return pd.DataFrame()


def load_players() -> pd.DataFrame:
    """
    Carga CSVs de estadisticas de jugadores.
    Soporta datos/jugadores_raw.csv y CSVs por liga en datos/players/ o datos/jugadores/.
    """
    data_path = Path(DATA_DIR)
    candidates = []
    for folder_name in ("players", "jugadores"):
        folder = data_path / folder_name
        if folder.exists():
            candidates.extend(sorted(folder.glob("*.csv")))
    main_file = data_path / "jugadores_raw.csv"
    if not candidates and main_file.exists():
        candidates.append(main_file)

    if not candidates:
        logger.warning("No se encontraron CSVs de jugadores en %s", DATA_DIR)
        return pd.DataFrame()

    frames = []
    for path in candidates:
        frame = _normalise_player_frame(_read_player_csv(path), path.name)
        if not frame.empty:
            frames.append(frame)

    if not frames:
        logger.warning("Ningun CSV de jugadores valido encontrado")
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["date", "team", "player"], keep="last"
    )


def invalidate_cache() -> None:
    """Invalida el caché de load_matches para forzar recarga."""
    load_matches.cache_clear()
