"""
Tab 🏠 Inicio — Calendario de partidos (hoy + próxima jornada) y resultados recientes.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.data.fixtures import (
    Fixture,
    get_upcoming_fixtures,
    get_recent_results,
    get_todays_fixtures,
)
from app.i18n import t


INICIO_CSS = """
<style>
.fx-card {
    background: linear-gradient(135deg, #1a1f2e 0%, #151925 100%);
    border: 1px solid #2a3040;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: border-color 0.15s;
}
.fx-card:hover { border-color: #00d4aa55; }
.fx-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}
.fx-teams {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1 1 320px;
    min-width: 260px;
}
.fx-team {
    color: #e8eaf6;
    font-weight: 700;
    font-size: 1.02rem;
}
.fx-vs {
    color: #8b9ab0;
    font-weight: 700;
    font-size: 0.95rem;
    padding: 0 6px;
}
.fx-score {
    background: #00d4aa22;
    color: #00d4aa;
    font-weight: 800;
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 1rem;
}
.fx-meta { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.fx-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
.fx-badge.sp1 { background: #00d4aa22; color: #00d4aa; }
.fx-badge.sp2 { background: #7c4dff22; color: #7c4dff; }
.fx-date {
    color: #8b9ab0;
    font-size: 0.82rem;
    font-weight: 600;
}
.fx-odds {
    display: flex;
    gap: 8px;
    color: #b0bec5;
    font-size: 0.82rem;
    font-family: "JetBrains Mono", monospace;
}
.fx-odd { background: #0e1117; padding: 3px 9px; border-radius: 5px; border: 1px solid #2a3040; }
.fx-odd b { color: #e8eaf6; }
.fx-empty {
    text-align: center;
    color: #8b9ab0;
    padding: 36px 20px;
    background: #1a1f2e;
    border: 1px dashed #2a3040;
    border-radius: 12px;
    font-size: 0.92rem;
    line-height: 1.5;
}
.fx-section-title {
    color: #e8eaf6 !important;
    font-size: 1.15rem !important;
    margin-top: 22px !important;
    margin-bottom: 12px !important;
    font-weight: 700 !important;
}
</style>
"""


def _badge(league_code: str) -> str:
    cls = "sp1" if league_code == "SP1" else "sp2"
    label = t("league_sp1") if league_code == "SP1" else t("league_sp2")
    return f'<span class="fx-badge {cls}">{label}</span>'


def _odds_html(fx: Fixture) -> str:
    if fx.odds_home is None:
        return ""
    return (
        '<div class="fx-odds">'
        f'<span class="fx-odd">{t("home")} <b>{fx.odds_home:.2f}</b></span>'
        f'<span class="fx-odd">{t("draw")} <b>{fx.odds_draw:.2f}</b></span>'
        f'<span class="fx-odd">{t("away")} <b>{fx.odds_away:.2f}</b></span>'
        '</div>'
    )


def _fixture_card(fx: Fixture, idx: int, key_prefix: str) -> None:
    """Renderiza una tarjeta de partido con botón de acción."""
    date_str = fx.date.strftime("%d/%m/%Y")
    time_str = f" · {fx.time}" if fx.time else ""
    score_or_vs = (
        f'<span class="fx-score">{fx.home_score}-{fx.away_score}</span>'
        if fx.is_played
        else '<span class="fx-vs">vs</span>'
    )

    col_card, col_btn = st.columns([5, 1])

    with col_card:
        st.markdown(
            f"""
            <div class="fx-card">
                <div class="fx-row">
                    <div class="fx-teams">
                        <span class="fx-team">{fx.home}</span>
                        {score_or_vs}
                        <span class="fx-team">{fx.away}</span>
                    </div>
                    <div class="fx-meta">
                        {_badge(fx.league_code)}
                        <span class="fx-date">📅 {date_str}{time_str}</span>
                    </div>
                </div>
                {_odds_html(fx)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_btn:
        if st.button(
            t("inicio_analyze"),
            key=f"{key_prefix}_{idx}",
            use_container_width=True,
        ):
            # Pre-carga equipos en el Comparador via session_state
            st.session_state.cmp_preload_home = fx.home
            st.session_state.cmp_preload_away = fx.away
            st.session_state.cmp_preload_league = fx.league_code
            st.session_state.active_tab = "comparador"
            st.rerun()


def _filter_by_league(fixtures: list[Fixture], league: str) -> list[Fixture]:
    if league == "all":
        return fixtures
    return [f for f in fixtures if f.league_code == league]


def render() -> None:
    """Renderiza la tab de inicio con calendario."""
    st.markdown(INICIO_CSS, unsafe_allow_html=True)

    st.markdown(f"### {t('inicio_title')}")
    st.caption(t("inicio_subtitle"))

    # ── Controles ────────────────────────────────────────────────────────────
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        league_choice = st.radio(
            t("inicio_filter_league"),
            options=["all", "SP1", "SP2"],
            format_func=lambda x: (
                t("league_all") if x == "all"
                else t("league_sp1") if x == "SP1"
                else t("league_sp2")
            ),
            horizontal=True,
            key="inicio_league",
        )
    with col_refresh:
        force = st.button(t("inicio_refresh"), use_container_width=True, key="inicio_refresh_btn")
        if force:
            # Limpiar caché de la función cacheada
            _cached_fixtures.clear()

    # ── Obtener fixtures (cacheado 1h) ───────────────────────────────────────
    with st.spinner("..."):
        today_fx, upcoming_fx, recent_fx = _cached_fixtures()

    today_fx = _filter_by_league(today_fx, league_choice)
    upcoming_fx = _filter_by_league(upcoming_fx, league_choice)
    recent_fx = _filter_by_league(recent_fx, league_choice)

    # ── Hoy ──────────────────────────────────────────────────────────────────
    if today_fx:
        st.markdown(f'<h4 class="fx-section-title">{t("inicio_today")}</h4>', unsafe_allow_html=True)
        for i, fx in enumerate(today_fx):
            _fixture_card(fx, i, "today")

    # ── Próxima jornada ──────────────────────────────────────────────────────
    st.markdown(f'<h4 class="fx-section-title">{t("inicio_upcoming")}</h4>', unsafe_allow_html=True)
    today_keys = {(f.league_code, f.home, f.away, f.date) for f in today_fx}
    upcoming_not_today = [
        f for f in upcoming_fx
        if (f.league_code, f.home, f.away, f.date) not in today_keys
    ]

    if upcoming_not_today:
        for i, fx in enumerate(upcoming_not_today[:20]):
            _fixture_card(fx, i, "upcoming")
    else:
        st.markdown(
            f'<div class="fx-empty">{t("inicio_no_upcoming")}</div>',
            unsafe_allow_html=True,
        )

    # ── Recientes ────────────────────────────────────────────────────────────
    if recent_fx:
        st.markdown(f'<h4 class="fx-section-title">{t("inicio_recent")}</h4>', unsafe_allow_html=True)
        for i, fx in enumerate(recent_fx[:10]):
            _fixture_card(fx, i, "recent")


@st.cache_data(show_spinner=False, ttl=3600)
def _cached_fixtures():
    """Cachea 1 hora las 3 listas para no re-descargar en cada render."""
    today = get_todays_fixtures()
    upcoming = get_upcoming_fixtures(max_days_ahead=14)
    recent = get_recent_results(days_back=5)
    return today, upcoming, recent
