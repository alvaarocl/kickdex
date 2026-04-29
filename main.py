"""
KICKDEX — Punto de entrada único.
Ejecutar con: streamlit run main.py
"""

import logging
import streamlit as st
import pandas as pd

# ── Configuración de página (DEBE ser la primera llamada Streamlit) ──────────
st.set_page_config(
    page_title="KICKDEX — The Football Data Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Importaciones del proyecto ───────────────────────────────────────────────
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
from app.ui.styles import get_custom_css, header_html
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ── Estado inicial de sesión ─────────────────────────────────────────────────
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True
if "lang" not in st.session_state:
    st.session_state.lang = "es"


# ── Inicialización de datos ──────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _init_data():
    """Descarga datos actualizados y los carga. Solo se ejecuta una vez por despliegue."""
    try:
        update_data(force_current=True)
    except Exception as e:
        logger.warning("No se pudieron actualizar los datos: %s", e)
    return True


@st.cache_data(show_spinner=False, ttl=3600)
def _load_data():
    df = load_matches()
    df_players = load_players()
    return df, df_players


# ── App principal ─────────────────────────────────────────────────────────────
def main():
    # Landing page primero (si procede)
    if st.session_state.show_landing:
        from app.ui import landing
        landing.render()
        return

    # Inicializar datos
    _init_data()
    with st.spinner("..."):
        df, df_players = _load_data()

    if df.empty:
        st.error("No se pudieron cargar datos.")
        return

    teams = get_team_list(df, recent_only=True)

    # ── Cabecera Premium ──
    n_partidos = len(df)
    last_date = df["Date"].max()
    upd = last_date.strftime("%d/%m/%Y") if not pd.isna(last_date) else "—"
    meta_txt = f"{n_partidos:,} partidos · actualizado {upd}"
    st.markdown(header_html(CURRENT_SEASON_LABEL, meta_txt), unsafe_allow_html=True)

    # ── Scroll suave al cambiar de tab ────────────────────────────────────────
    import streamlit.components.v1 as _components
    _components.html("""
    <script>
    (function() {
      function watchTabs() {
        var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
        tabs.forEach(function(t) {
          if (t._kx) return; t._kx = true;
          t.addEventListener('click', function() {
            setTimeout(function() { window.parent.scrollTo({top:0,behavior:'smooth'}); }, 80);
          });
        });
      }
      [200, 600, 1200].forEach(function(d) { setTimeout(watchTabs, d); });
    })();
    </script>
    """, height=0)

    # ── Tabs principales ──────────────────────────────────────────────────────
    tab_labels = [
        t("tab_inicio"),
        t("tab_comparador"),
        t("tab_h2h"),
        t("tab_jugadores"),
        t("tab_arbitros"),
    ]
    
    # Usamos st.tabs nativo pero estilizado via CSS para que se vea igual que la web
    st_tabs = st.tabs(tab_labels)
    
    from app.ui import inicio, comparador, h2h, jugadores, arbitros

    with st_tabs[0]:
        inicio.render()
    with st_tabs[1]:
        comparador.render(df, teams, df_players)
    with st_tabs[2]:
        h2h.render(df, teams)
    with st_tabs[3]:
        jugadores.render(df_players)
    with st_tabs[4]:
        arbitros.render(df)


if __name__ == "__main__":
    main()
