"""
UI — Tab de Árbitros.
Muestra el ranking disciplinario de los colegiados para identificar tendencias en tarjetas y faltas.
"""

import streamlit as st
import pandas as pd
from app.engine.referees import get_referee_stats
from app.config import DISCLAIMER, COLOR_VALUE_RED, COLOR_VALUE_GREEN

def render(df: pd.DataFrame) -> None:
    st.markdown("### ⚖️ Panel de Arbitraje")
    st.caption(
        "Analiza el perfil de cada árbitro basándose en su historial acumulado. "
        "Fundamental para mercados de tarjetas (Over/Under) y pronósticos de faltas."
    )
    
    with st.spinner("Analizando datos de arbitraje..."):
        # Obtenemos las estadísticas base
        stats = get_referee_stats(df)
        
    if stats.empty:
        st.warning(
            "No se han encontrado datos de árbitros en la base de datos actual. "
            "Nota: Algunas ligas (como La Liga en ciertos CSVs históricos) no proporcionan el nombre del árbitro. "
            "Ligas como la Premier League (E0) suelen incluir esta información."
        )
        return

    # Controles de búsqueda y ordenación
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("🔍 Buscar Árbitro", placeholder="Introduce nombre...", key="ref_search")
    with col2:
        min_matches = st.slider("Mín. Partidos", 3, 20, 5)

    # Filtrado dinámico
    filtered = stats[stats["Partidos"] >= min_matches].copy()
    if search:
        filtered = filtered[filtered["Referee"].str.contains(search, case=False)]
    
    # Rankings rápidos
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    
    top_yellows = stats.sort_values("Amarillas/Part.", ascending=False).iloc[0]
    r1.metric("Más Tarjetero (🟨)", top_yellows["Referee"], f"{top_yellows['Amarillas/Part.']:.2f}")
    
    top_fouls = stats.sort_values("Faltas/Part.", ascending=False).iloc[0]
    r2.metric("Más Riguroso (Faltas)", top_fouls["Referee"], f"{top_fouls['Faltas/Part.']:.2f}")
    
    top_reds = stats.sort_values("Rojas/Part.", ascending=False).iloc[0]
    r3.metric("Más Expulsiones (🟥)", top_reds["Referee"], f"{top_reds['Rojas/Part.']:.2f}")

    # Tabla Maestra
    st.markdown("##### Ranking Disciplinario Completo")
    
    # Configuración de columnas para que se vea Pro
    st.dataframe(
        filtered.sort_values("Amarillas/Part.", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Referee": st.column_config.TextColumn("Árbitro", width="medium"),
            "Partidos": st.column_config.NumberColumn("Partidos", format="%d"),
            "Amarillas/Part.": st.column_config.ProgressColumn(
                "🟨 Amarillas/Part.",
                help="Media de tarjetas amarillas por partido",
                format="%.2f",
                min_value=0,
                max_value=7.0
            ),
            "Rojas/Part.": st.column_config.NumberColumn("🟥 Rojas/Part.", format="%.2f"),
            "Faltas/Part.": st.column_config.NumberColumn("⏱️ Faltas/Part.", format="%.2f"),
        }
    )

    # Insights Pro
    st.info(
        "💡 **Análisis de Valor:**\n"
        "- **Árbitros 'Over':** Aquellos con > 4.5 amarillas/partido. Ideales para partidos de alta rivalidad.\n"
        "- **Árbitros 'Under':** Aquellos con < 3.0 amarillas/partido. Buscan dejar jugar y evitan amonestar temprano."
    )

    st.markdown(
        f'<div class="disclaimer">{DISCLAIMER}</div>',
        unsafe_allow_html=True
    )
