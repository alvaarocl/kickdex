"""
Analista Pro — Punto de entrada único.
Ejecutar con: streamlit run main.py
"""

import logging
import streamlit as st

# ── Configuración de página (DEBE ser la primera llamada Streamlit) ──────────
st.set_page_config(
    page_title="Analista Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Importaciones del proyecto ───────────────────────────────────────────────
from app.ui.styles import CUSTOM_CSS
from app.data.loader import load_matches, load_players, get_team_list, invalidate_cache
from app.data.updater import update_data
from app.config import CURRENT_SEASON_LABEL, LEAGUES

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── CSS global ───────────────────────────────────────────────────────────────
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Inicialización de datos (con caché Streamlit para no re-ejecutar) ────────
@st.cache_resource(show_spinner=False)
def _init_data():
    """Descarga datos actualizados y los carga. Solo se ejecuta una vez por despliegue."""
    logger.info("Inicializando datos...")
    try:
        result = update_data(force_current=True)
        logger.info("Actualización: %s", result)
    except Exception as e:
        logger.warning("No se pudieron actualizar los datos: %s", e)
    return True


@st.cache_data(show_spinner=False, ttl=3600)
def _load_data():
    df = load_matches()
    df_players = load_players()
    return df, df_players


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _render_sidebar(df):
    with st.sidebar:
        st.markdown("## ⚽ Analista Pro")
        st.caption("Herramienta gratuita de Big Data futbolístico")
        st.divider()

        if not df.empty:
            n_partidos = len(df)
            min_year = df["Date"].dt.year.min()
            max_year = df["Date"].dt.year.max()
            ligas = ", ".join(LEAGUES.values())
            st.markdown(f"**📚 Base de Datos**")
            st.caption(f"{n_partidos:,} partidos · {min_year}–{max_year}")
            st.caption(f"Ligas: {ligas}")
            st.caption(f"Temporada actual: {CURRENT_SEASON_LABEL}")
        else:
            st.error("Sin datos. Revisa la carpeta `datos/`.")

        st.divider()

        if st.button("🔄 Actualizar datos", use_container_width=True):
            invalidate_cache()
            _load_data.clear()
            st.rerun()

        st.markdown(
            '<div style="color:#8b9ab0;font-size:0.7rem;margin-top:20px;">'
            'Analista Pro · Uso educativo<br>'
            'Datos: football-data.co.uk<br>'
            '<a href="https://alvarocarpintero.com" style="color:#00d4aa;">alvarocarpintero.com</a>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── App principal ─────────────────────────────────────────────────────────────
def main():
    # Inicializar (solo una vez por deploy, gracias a cache_resource)
    _init_data()

    # Cargar datos (cacheados 1 hora)
    with st.spinner("Cargando datos..."):
        df, df_players = _load_data()

    if df.empty:
        st.error(
            "No se pudieron cargar datos. "
            "Verifica que la carpeta `datos/` exista y contenga archivos CSV válidos."
        )
        return

    teams = get_team_list(df, recent_only=True)

    # Sidebar
    _render_sidebar(df)

    # ── Cabecera ──────────────────────────────────────────────────────────────
    col_title, col_season = st.columns([3, 1])
    with col_title:
        st.markdown(
            '<h1 style="margin-bottom:0;color:#e8eaf6;">⚽ Analista Pro</h1>'
            '<p style="color:#8b9ab0;margin-top:2px;font-size:0.9rem;">'
            'Big Data · Value Bets · Player Scouting · 100% Gratuito</p>',
            unsafe_allow_html=True,
        )
    with col_season:
        st.markdown(
            f'<div style="text-align:right;padding-top:12px;">'
            f'<span style="background:#00d4aa22;color:#00d4aa;padding:4px 12px;'
            f'border-radius:20px;font-size:0.8rem;font-weight:700;">🟢 {CURRENT_SEASON_LABEL}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Tabs principales ──────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Comparador",
        "📚 H2H Histórico",
        "⚽ Jugadores",
        "💎 Value Bets",
    ])

    # Importar UIs aquí para evitar imports circulares en arranque
    from app.ui import comparador, h2h, jugadores, valor

    with tab1:
        comparador.render(df, teams)

    with tab2:
        h2h.render(df, teams)

    with tab3:
        jugadores.render(df_players)

    with tab4:
        valor.render(df, teams)


if __name__ == "__main__":
    main()
