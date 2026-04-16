"""
KICKDEX — Punto de entrada único.
Ejecutar con: streamlit run main.py
"""

import logging
import streamlit as st

# ── Configuración de página (DEBE ser la primera llamada Streamlit) ──────────
st.set_page_config(
    page_title="KICKDEX — The Football Data Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Importaciones del proyecto ───────────────────────────────────────────────
from app.ui.styles import CUSTOM_CSS
from app.data.loader import load_matches, load_players, get_team_list, invalidate_cache
from app.data.updater import update_data
from app.config import CURRENT_SEASON_LABEL, LEAGUES
from app.i18n import t, get_lang, set_lang

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── CSS global ───────────────────────────────────────────────────────────────
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Estado inicial de sesión ─────────────────────────────────────────────────
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True
if "lang" not in st.session_state:
    st.session_state.lang = "es"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "inicio"


# ── Inicialización de datos ──────────────────────────────────────────────────
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


# ── Language toggle (top-right) ──────────────────────────────────────────────
def _render_lang_toggle():
    """Botón ES/EN en la esquina superior derecha."""
    _, col_lang = st.columns([6, 1])
    with col_lang:
        current = get_lang()
        new_lang = st.radio(
            "🌐",
            options=["es", "en"],
            format_func=lambda x: "🇪🇸 ES" if x == "es" else "🇬🇧 EN",
            index=0 if current == "es" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="lang_toggle",
        )
        if new_lang != current:
            set_lang(new_lang)
            st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _render_sidebar(df):
    with st.sidebar:
        st.markdown("## KICKDEX")
        st.caption(t("sidebar_tool"))
        st.divider()

        if not df.empty:
            n_partidos = len(df)
            min_year = df["Date"].dt.year.min()
            max_year = df["Date"].dt.year.max()
            ligas = ", ".join(LEAGUES.values())
            st.markdown(f"**{t('sidebar_db')}**")
            st.caption(f"{n_partidos:,} {t('sidebar_matches')} · {min_year}–{max_year}")
            st.caption(f"{t('sidebar_leagues')}: {ligas}")
            st.caption(f"{t('sidebar_season')}: {CURRENT_SEASON_LABEL}")
        else:
            st.error(t("sidebar_no_data"))

        st.divider()

        if st.button(t("sidebar_update"), use_container_width=True):
            invalidate_cache()
            _load_data.clear()
            st.rerun()

        st.markdown(
            '<div style="color:#8b9ab0;font-size:0.7rem;margin-top:20px;">'
            'KICKDEX · Uso educativo<br>'
            'Datos: football-data.co.uk<br>'
            '<a href="https://alvarocarpintero.com" style="color:#00d4aa;">alvarocarpintero.com</a>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── App principal ─────────────────────────────────────────────────────────────
def main():
    # Landing page primero (si procede)
    if st.session_state.show_landing:
        _render_lang_toggle()
        from app.ui import landing
        landing.render()
        return

    # Inicializar datos
    _init_data()
    with st.spinner("..."):
        df, df_players = _load_data()

    if df.empty:
        st.error(
            "No se pudieron cargar datos. "
            "Verifica que la carpeta `datos/` exista y contenga archivos CSV válidos."
        )
        return

    teams = get_team_list(df, recent_only=True)

    _render_sidebar(df)

    # ── Cabecera + lang toggle ────────────────────────────────────────────────
    col_title, col_season, col_lang = st.columns([4, 1, 1])
    with col_title:
        st.markdown(
            f'<h1 style="margin-bottom:0;color:#e8eaf6;">KICKDEX</h1>'
            f'<p style="color:#8b9ab0;margin-top:2px;font-size:0.9rem;">'
            f'{t("app_tagline")}</p>',
            unsafe_allow_html=True,
        )
    with col_season:
        st.markdown(
            f'<div style="text-align:right;padding-top:18px;">'
            f'<span style="background:#00d4aa22;color:#00d4aa;padding:4px 12px;'
            f'border-radius:20px;font-size:0.8rem;font-weight:700;">🟢 {CURRENT_SEASON_LABEL}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_lang:
        current = get_lang()
        new_lang = st.radio(
            "lang",
            options=["es", "en"],
            format_func=lambda x: "🇪🇸 ES" if x == "es" else "🇬🇧 EN",
            index=0 if current == "es" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="lang_toggle_main",
        )
        if new_lang != current:
            set_lang(new_lang)
            st.rerun()

    # ── Tabs principales ──────────────────────────────────────────────────────
    # Usamos un radio horizontal custom o un selector para manejar el estado de la pestaña
    # ya que st.tabs es estático y no permite saltar programáticamente con st.rerun de forma nativa.
    # No obstante, para mantener la estética de tabs, usaremos un truco de session_state.
    
    tabs = [
        t("tab_inicio"),
        t("tab_comparador"),
        t("tab_h2h"),
        t("tab_jugadores"),
        t("tab_value"),
    ]
    
    # Mapeo de nombres de tabs a índices
    tab_map = {
        "inicio": 0,
        "comparador": 1,
        "h2h": 2,
        "jugadores": 3,
        "valor": 4
    }
    
    # Determinar qué pestaña mostrar
    active_index = tab_map.get(st.session_state.active_tab, 0)
    
    # Crear los tabs (esto siempre crea todos, pero Streamlit solo activa el primero por defecto)
    # Para forzar el cambio, necesitamos que st.tabs se "re-renderice" con el índice correcto.
    # Como st.tabs no tiene parámetro 'index', usaremos un contenedor dinámico o 
    # simplemente renderizaremos la pestaña activa basada en session_state.
    
    # Opción profesional: Usar un selector de tabs custom con CSS
    st.markdown('<div class="tabs-anchor"></div>', unsafe_allow_html=True)
    
    selected_tab = st.session_state.active_tab
    
    # Renderizar contenido según la pestaña activa en session_state
    from app.ui import inicio, comparador, h2h, jugadores, valor

    if selected_tab == "inicio":
        inicio.render()
    elif selected_tab == "comparador":
        comparador.render(df, teams, df_players)
    elif selected_tab == "h2h":
        h2h.render(df, teams)
    elif selected_tab == "jugadores":
        jugadores.render(df_players)
    elif selected_tab == "valor":
        valor.render(df, teams)


if __name__ == "__main__":
    main()
