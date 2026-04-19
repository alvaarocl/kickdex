"""
Player Scraper — Integración con FBref vía soccerdata.
Descarga estadísticas avanzadas de jugadores para todas las ligas configuradas.
"""

import logging
import time
from pathlib import Path
import pandas as pd
from app.config import DATA_DIR, CURRENT_SEASON_LABEL

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

def update_players() -> bool:
    """
    Descarga estadísticas de jugadores de la temporada actual desde FBref
    para todas las ligas configuradas. Guarda en datos/jugadores_raw.csv.
    """
    try:
        try:
            import soccerdata as sd
        except ImportError:
            logger.warning("soccerdata no instalado — saltando scraping de jugadores FBref")
            return False

        data_path = Path(DATA_DIR)
        data_path.mkdir(exist_ok=True)
        output_file = data_path / "jugadores_raw.csv"

        season = CURRENT_SEASON_LABEL.replace("/", "-")  # e.g. "2025-2026"
        all_frames = []

        for code, fbref_name in FBREF_LEAGUES.items():
            try:
                logger.info("  Descargando jugadores %s (%s)...", code, fbref_name)
                fbref = sd.FBref(leagues=[fbref_name], seasons=season)
                df_shooting = fbref.read_player_match_stats(stat_type='shooting')
                if df_shooting.empty:
                    logger.warning("  Sin datos para %s", fbref_name)
                    continue
                df = df_shooting.reset_index()
                df.columns = [str(c).lower().strip() for c in df.columns]
                df["league"] = code
                all_frames.append(df)
                logger.info("  ✓ %s — %d registros", code, len(df))
                time.sleep(2)  # respetar rate limit de FBref
            except Exception as e:
                logger.warning("  Error %s: %s", code, e)
                continue

        if not all_frames:
            logger.warning("No se obtuvieron datos de jugadores de ninguna liga.")
            return False

        combined = pd.concat(all_frames, ignore_index=True)
        combined.to_csv(output_file, index=False, encoding="utf-8")
        logger.info("✓ %d registros totales de jugadores en %s", len(combined), output_file)
        return True

    except Exception as e:
        logger.error("Error en player_scraper: %s", e)
        return False

if __name__ == "__main__":
    # Test rápido
    logging.basicConfig(level=logging.INFO)
    update_players()
