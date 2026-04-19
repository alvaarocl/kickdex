"""
Player Scraper — Integración con FBref vía soccerdata.
Descarga estadísticas avanzadas de jugadores para La Liga y Segunda División.
"""

import logging
from pathlib import Path
import pandas as pd
from app.config import DATA_DIR, CURRENT_SEASON_LABEL

logger = logging.getLogger(__name__)

def update_players() -> bool:
    """
    Descarga estadísticas de jugadores de la temporada actual desde FBref.
    Guarda en datos/jugadores_raw.csv.
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

        logger.info("Iniciando scraping de jugadores desde FBref (La Liga)...")

        season = CURRENT_SEASON_LABEL.replace("/", "-")  # e.g. "2025-2026"

        fbref = sd.FBref(leagues=['ESP-La Liga', 'ESP-Segunda Division'], seasons=season)
        
        # Obtener stats de disparos (shooting) como base para scouting
        df_shooting = fbref.read_player_match_stats(stat_type='shooting')
        
        if df_shooting.empty:
            logger.warning("No se obtuvieron datos de jugadores de FBref.")
            return False

        # Resetear índice para tener 'player', 'team', 'date' como columnas
        df = df_shooting.reset_index()
        
        # Renombrar columnas a minúsculas consistentes con loader.py
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Guardar CSV
        df.to_csv(output_file, index=False, encoding="utf-8")
        logger.info("✓ %d registros de jugadores guardados en %s", len(df), output_file)
        return True

    except Exception as e:
        logger.error("Error en player_scraper: %s", e)
        return False

if __name__ == "__main__":
    # Test rápido
    logging.basicConfig(level=logging.INFO)
    update_players()
