"""
Player Scraper — Integración con FBref vía soccerdata.
Descarga estadísticas avanzadas de jugadores para todas las ligas configuradas.
"""

import logging
import json
import os
import time
from pathlib import Path
import pandas as pd
from app.config import DATA_DIR, CURRENT_SEASON_LABEL, CURRENT_SEASON_YEAR
from app.data.loader import normalize_team_name

logger = logging.getLogger(__name__)

# Mapeo football-data code → nombre de liga en FBref/soccerdata
FBREF_LEAGUES = {
    "SP1": "ESP-La Liga",
    "SP2": "ESP-Segunda Division",
    "E0":  "ENG-Premier League",
    "E1":  "ENG-Championship",
    "I1":  "ITA-Serie A",
    "I2":  "ITA-Serie B",
    "D1":  "GER-Bundesliga",
    "D2":  "GER-2. Bundesliga",
    "F1":  "FRA-Ligue 1",
    "F2":  "FRA-Ligue 2",
    "N1":  "NED-Eredivisie",
}

# Ligas con lector soccerdata.Understat (HTTP puro, sin Selenium/Chrome).
# Se usan como relleno para equipos que faltan en la cache de FBref (p. ej.
# recién ascendidos) sin depender del navegador undetected-chromedriver que
# se cuelga en algunos entornos. Solo cubre las 5 grandes ligas: Understat no
# tiene segundas divisiones ni Eredivisie.
UNDERSTAT_LEAGUES = {
    "SP1": "ESP-La Liga",
    "E0": "ENG-Premier League",
    "I1": "ITA-Serie A",
    "D1": "GER-Bundesliga",
    "F1": "FRA-Ligue 1",
}

SOCCERDATA_CUSTOM_LEAGUES = {
    "ESP-Segunda Division": {"FBref": "Segunda División", "season_start": "Aug", "season_end": "Jun"},
    "ENG-Championship": {"FBref": "Championship", "season_start": "Aug", "season_end": "May"},
    "ITA-Serie B": {"FBref": "Serie B", "season_start": "Aug", "season_end": "May"},
    "GER-2. Bundesliga": {"FBref": "2. Bundesliga", "season_start": "Aug", "season_end": "May"},
    "FRA-Ligue 2": {"FBref": "Ligue 2", "season_start": "Aug", "season_end": "May"},
    "NED-Eredivisie": {"FBref": "Eredivisie", "season_start": "Aug", "season_end": "May"},
}


def _ensure_soccerdata_config(data_path: Path) -> None:
    config_dir = data_path / "soccerdata" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    league_dict_path = config_dir / "league_dict.json"
    existing = {}
    if league_dict_path.exists():
        try:
            existing = json.loads(league_dict_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    merged = {**existing, **SOCCERDATA_CUSTOM_LEAGUES}
    league_dict_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

def update_players(leagues: list[str] | None = None) -> bool:
    """
    Descarga estadísticas de jugadores de la temporada actual desde FBref
    para todas las ligas configuradas. Guarda en datos/jugadores_raw.csv.
    """
    try:
        data_path = Path(DATA_DIR)
        data_path.mkdir(exist_ok=True)
        os.environ.setdefault("SOCCERDATA_DIR", str(data_path / "soccerdata"))
        _ensure_soccerdata_config(data_path)

        try:
            import soccerdata as sd
        except ImportError:
            logger.warning("soccerdata no instalado — saltando scraping de jugadores FBref")
            return False

        per_league_path = data_path / "players"
        per_league_path.mkdir(exist_ok=True)
        output_file = data_path / "jugadores_raw.csv"

        season = CURRENT_SEASON_LABEL.replace("/", "-")  # e.g. "2025-2026"
        all_frames = []

        def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
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

        def _normalise_match_logs(df: pd.DataFrame, league_code: str) -> pd.DataFrame:
            df = _flatten_columns(df.reset_index())
            rename = {
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
            for required in ("team", "player"):
                if required not in df.columns:
                    raise ValueError(f"FBref no devolvio columna requerida: {required}")
            out = pd.DataFrame()
            out["league"] = league_code
            out["date"] = pd.to_datetime(df.get("date"), errors="coerce")
            out["team"] = df["team"].apply(normalize_team_name)
            out["player"] = df["player"].astype(str).str.strip()
            for col in ["min", "gls", "ast", "sh", "sot", "fls", "crdy", "crdr"]:
                out[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0) if col in df.columns else 0.0
            return out[(out["team"].astype(bool)) & (out["player"].astype(bool))]

        def _normalise_season_stats(fbref, league_code: str) -> pd.DataFrame:
            frames = {}
            for stat_type in ("standard", "shooting", "misc"):
                raw = fbref.read_player_season_stats(stat_type=stat_type)
                if raw is None or raw.empty:
                    continue
                frame = _flatten_columns(raw.reset_index())
                frames[stat_type] = frame

            if "standard" not in frames:
                return pd.DataFrame()

            keys = ["league", "season", "team", "player"]
            df = frames["standard"]
            for stat_type in ("shooting", "misc"):
                if stat_type in frames:
                    keep = [c for c in frames[stat_type].columns if c in keys or c not in df.columns]
                    df = df.merge(frames[stat_type][keep], on=keys, how="left")

            for required in ("team", "player"):
                if required not in df.columns:
                    raise ValueError(f"FBref no devolvio columna requerida: {required}")

            def _num(col):
                if col not in df.columns:
                    return pd.Series(0.0, index=df.index)
                return pd.to_numeric(df[col], errors="coerce").fillna(0.0)

            mp = _num("playing time_mp")
            mp = mp.mask(mp <= 0, 1)

            team = df["team"].apply(normalize_team_name)
            player = df["player"].astype(str).str.strip()
            out = pd.DataFrame({
                "league": league_code,
                "date": pd.Timestamp.utcnow().date().isoformat(),
                "team": team,
                "player": player,
                "min": (_num("playing time_min") / mp).round(2),
                "gls": (_num("performance_gls") / mp).round(3),
                "ast": (_num("performance_ast") / mp).round(3),
                "sh": (_num("standard_sh") / mp).round(3),
                "sot": (_num("standard_sot") / mp).round(3),
                "fls": (_num("performance_fls") / mp).round(3),
                "crdy": (_num("performance_crdy") / mp).round(3),
                "crdr": (_num("performance_crdr") / mp).round(3),
            })
            return out[(out["team"].astype(bool)) & (out["player"].astype(bool))]

        def _normalise_understat_season_stats(raw: pd.DataFrame, league_code: str) -> pd.DataFrame:
            if raw is None or raw.empty:
                return pd.DataFrame()
            df = raw.reset_index()
            for required in ("team", "player"):
                if required not in df.columns:
                    raise ValueError(f"Understat no devolvio columna requerida: {required}")

            def _num(col):
                if col not in df.columns:
                    return pd.Series(0.0, index=df.index)
                return pd.to_numeric(df[col], errors="coerce").fillna(0.0)

            mp = _num("matches")
            mp = mp.mask(mp <= 0, 1)

            team = df["team"].apply(normalize_team_name)
            player = df["player"].astype(str).str.strip()
            out = pd.DataFrame({
                "league": league_code,
                "date": pd.Timestamp.utcnow().date().isoformat(),
                "team": team,
                "player": player,
                "min": (_num("minutes") / mp).round(2),
                "gls": (_num("goals") / mp).round(3),
                "ast": (_num("assists") / mp).round(3),
                "sh": (_num("shots") / mp).round(3),
                # Understat no expone tiros a puerta ni faltas cometidas a nivel
                # de temporada; quedan en 0.0 (limitación conocida de la fuente).
                "sot": (_num("shots_on_target") / mp).round(3),
                "fls": (_num("fouls") / mp).round(3),
                "crdy": (_num("yellow_cards") / mp).round(3),
                "crdr": (_num("red_cards") / mp).round(3),
            })
            return out[(out["team"].astype(bool)) & (out["player"].astype(bool))]

        def _merge_missing_teams(fresh: pd.DataFrame, cached_path: Path) -> pd.DataFrame:
            """Combina datos nuevos con la cache local sin pisar equipos ya cubiertos.

            Se usa para Understat: solo aporta filas de equipos ausentes en la
            cache (p. ej. recién ascendidos), preservando las estadísticas más
            completas que ya existen (sot/fls reales) para el resto.
            """
            if not cached_path.exists():
                return fresh
            try:
                cached_df = pd.read_csv(cached_path, low_memory=False)
            except Exception:
                return fresh
            existing_teams = set(cached_df["team"].astype(str)) if "team" in cached_df.columns else set()
            new_rows = fresh[~fresh["team"].isin(existing_teams)]
            if new_rows.empty:
                return cached_df
            return pd.concat([cached_df, new_rows], ignore_index=True)

        selected_leagues = {code.upper() for code in leagues} if leagues else set(FBREF_LEAGUES)

        for code, fbref_name in FBREF_LEAGUES.items():
            if code not in selected_leagues:
                continue
            cached = per_league_path / f"{code}.csv"

            understat_name = UNDERSTAT_LEAGUES.get(code)
            if understat_name:
                try:
                    logger.info("  Descargando jugadores %s vía Understat (%s)...", code, understat_name)
                    understat = sd.Understat(leagues=[understat_name], seasons=CURRENT_SEASON_YEAR)
                    fresh = _normalise_understat_season_stats(understat.read_player_season_stats(), code)
                    if fresh.empty:
                        logger.warning("  Understat sin datos para %s", understat_name)
                    else:
                        merged = _merge_missing_teams(fresh, cached)
                        merged.to_csv(cached, index=False, encoding="utf-8")
                        all_frames.append(merged)
                        logger.info(
                            "  OK %s (Understat) - %d registros, %d equipos",
                            code, len(merged), merged["team"].nunique(),
                        )
                        time.sleep(1)  # respetar rate limit de Understat
                        continue
                except Exception as e:
                    logger.warning("  Error Understat %s: %s — probando FBref...", code, e)

            try:
                logger.info("  Descargando jugadores %s (%s)...", code, fbref_name)
                fbref = sd.FBref(leagues=[fbref_name], seasons=season)
                df = _normalise_season_stats(fbref, code)
                if df.empty:
                    logger.warning("  Sin datos para %s", fbref_name)
                    continue
                df["league"] = code
                df.to_csv(cached, index=False, encoding="utf-8")
                all_frames.append(df)
                logger.info("  OK %s - %d registros", code, len(df))
                time.sleep(2)  # respetar rate limit de FBref
            except Exception as e:
                logger.warning("  Error %s: %s", code, e)
                if cached.exists():
                    try:
                        all_frames.append(pd.read_csv(cached, low_memory=False))
                        logger.info("  Usando cache local de jugadores para %s", code)
                    except Exception as cache_error:
                        logger.warning("  Cache local invalida para %s: %s", code, cache_error)
                continue

        if not all_frames:
            logger.warning("No se obtuvieron datos de jugadores de ninguna liga.")
            return False

        combined = pd.concat(all_frames, ignore_index=True)
        combined.to_csv(output_file, index=False, encoding="utf-8")
        logger.info("OK %d registros totales de jugadores en %s", len(combined), output_file)
        return True

    except Exception as e:
        logger.error("Error en player_scraper: %s", e)
        return False

if __name__ == "__main__":
    # Test rápido
    logging.basicConfig(level=logging.INFO)
    update_players()
