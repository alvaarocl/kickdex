"""
Motor de árbitros — analiza el perfil disciplinario de cada colegiado.
Ayuda a identificar árbitros "tarjeteros" o permisivos para mercados disciplinarios.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)

def get_referee_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadísticas agrupadas por árbitro basándose en el historial.
    
    Métricas:
    - Partidos pitados
    - Promedio de Amarillas por partido
    - Promedio de Rojas por partido
    - Promedio de Faltas por partido
    """
    if "Referee" not in df.columns:
        logger.warning("La columna 'Referee' no está presente en el DataFrame.")
        return pd.DataFrame()
        
    # Limpiar nombres y filtrar nulos
    rdf = df.dropna(subset=["Referee"]).copy()
    rdf["Referee"] = rdf["Referee"].str.strip()
    
    if rdf.empty:
        return pd.DataFrame()
        
    # Columnas disciplinarias necesarias
    cols_num = ["HY", "AY", "HR", "AR", "HF", "AF"]
    available_cols = [c for c in cols_num if c in rdf.columns]
    
    for col in available_cols:
        rdf[col] = pd.to_numeric(rdf[col], errors="coerce").fillna(0)
            
    # Calcular totales por partido (si las columnas existen)
    rdf["Total_Yellows"] = rdf.get("HY", 0) + rdf.get("AY", 0)
    rdf["Total_Reds"] = rdf.get("HR", 0) + rdf.get("AR", 0)
    rdf["Total_Fouls"] = rdf.get("HF", 0) + rdf.get("AF", 0)
    
    # Agrupación por árbitro
    # Usamos 'Div' o cualquier columna existente para contar partidos
    count_col = "Div" if "Div" in rdf.columns else rdf.columns[0]
    
    stats = rdf.groupby("Referee").agg({
        count_col: "count",
        "Total_Yellows": "sum",
        "Total_Reds": "sum",
        "Total_Fouls": "sum"
    }).rename(columns={count_col: "Partidos"})
    
    # Solo incluir árbitros con una muestra mínima para que los promedios sean fiables
    stats = stats[stats["Partidos"] >= 3].copy()
    
    if stats.empty:
        return pd.DataFrame()
    
    # Cálculo de promedios
    stats["Amarillas/Part."] = (stats["Total_Yellows"] / stats["Partidos"]).round(2)
    stats["Rojas/Part."] = (stats["Total_Reds"] / stats["Partidos"]).round(2)
    stats["Faltas/Part."] = (stats["Total_Fouls"] / stats["Partidos"]).round(2)
    
    # Limpieza final para la UI
    final_stats = stats.drop(columns=["Total_Yellows", "Total_Reds", "Total_Fouls"])
    
    # Ordenar por amarillas (desc) por defecto, ya que es el mercado más común
    return final_stats.sort_values("Amarillas/Part.", ascending=False).reset_index()
