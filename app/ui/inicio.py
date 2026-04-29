"""
Tab Inicio — calendario y resultados.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
from app.data.fixtures import Fixture, get_upcoming_fixtures, get_recent_results, get_todays_fixtures
from app.config import LEAGUES

def _fixture_card_html(fx: Fixture, is_result: bool = False) -> str:
    league_cls = fx.league_code.lower()
    league_label = LEAGUES.get(fx.league_code, fx.league_code)
    
    # Formatear fecha estilo JS
    date_label = fx.date.strftime("%a %d %b")
    if fx.time: date_label += f" · {fx.time}"

    main_content = ""
    if is_result:
        home_win = fx.home_score > fx.away_score
        away_win = fx.away_score > fx.home_score
        main_content = f"""
        <div class="fx-score">
            <span class="{'fx-score-win' if home_win else ''}">{fx.home_score}</span>
            <span class="fx-score-sep">–</span>
            <span class="{'fx-score-win' if away_win else ''}">{fx.away_score}</span>
        </div>"""
    else:
        main_content = '<div class="fx-meta">Datos disponibles en el comparador</div>'

    return f"""
    <div class="fx-card">
        <div class="fx-row">
            <span class="fx-league-badge {league_cls}">{league_label}</span>
            <span class="fx-date">{date_label}</span>
        </div>
        <div class="fx-row fx-main">
            <div class="fx-teams">
                <span class="fx-team">{fx.home}</span>
                <span class="fx-vs">vs</span>
                <span class="fx-team">{fx.away}</span>
            </div>
            {main_content}
        </div>
    </div>"""

def render() -> None:
    st.markdown('<h2 class="section-h2">Calendario y Partidos</h2>', unsafe_allow_html=True)
    st.markdown('<p class="section-desc">Próximos partidos, resultados recientes y acceso rápido al comparador.</p>', unsafe_allow_html=True)

    # ── Filtros ──
    options = ["all"] + list(LEAGUES.keys())
    
    def _format_league(code):
        if code == "all": return "Todas"
        return LEAGUES.get(code, code)

    league_choice = st.radio(
        "Filtro", options=options, 
        format_func=_format_league,
        horizontal=True, label_visibility="collapsed"
    )

    # ── Datos ──
    today_fx = get_todays_fixtures()
    upcoming_fx = get_upcoming_fixtures()
    recent_fx = get_recent_results()

    def _filter(l):
        return [f for f in l if league_choice == "all" or f.league_code == league_choice]

    # Renderizar secciones
    t_fx = _filter(today_fx)
    if t_fx:
        st.markdown('<div class="fx-section-title">Partidos de hoy</div>', unsafe_allow_html=True)
        for fx in t_fx:
            col_c, col_b = st.columns([5, 1])
            col_c.markdown(_fixture_card_html(fx), unsafe_allow_html=True)
            if col_b.button("Analizar", key=f"btn_t_{fx.home}"):
                st.session_state.cmp_preload_home = fx.home
                st.session_state.cmp_preload_away = fx.away
                # st.session_state.active_tab = "comparador" # No funciona con st.tabs
                st.info("Equipos cargados. Ve a la pestaña Comparador.")

    u_fx = _filter(upcoming_fx)
    if u_fx:
        st.markdown('<div class="fx-section-title">Próxima jornada</div>', unsafe_allow_html=True)
        for fx in u_fx[:10]:
            col_c, col_b = st.columns([5, 1])
            col_c.markdown(_fixture_card_html(fx), unsafe_allow_html=True)
            if col_b.button("Analizar", key=f"btn_u_{fx.home}"):
                st.session_state.cmp_preload_home = fx.home
                st.session_state.cmp_preload_away = fx.away
                st.info("Equipos cargados. Ve a la pestaña Comparador.")

    r_fx = _filter(recent_fx)
    if r_fx:
        st.markdown('<div class="fx-section-title">Resultados recientes</div>', unsafe_allow_html=True)
        for fx in r_fx[:5]:
            st.markdown(_fixture_card_html(fx, is_result=True), unsafe_allow_html=True)
