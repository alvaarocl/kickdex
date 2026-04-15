"""
Tab ⚡ Comparador de Partido.
Forma reciente + Smart Alerts + Probabilidades + Comparativa de jugadores.
Soporta filtro por división (SP1/SP2).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.engine.metrics import get_recent_form, get_h2h_summary
from app.engine.smart_alerts import generate_alerts, AlertStrength
from app.engine.probability import calculate_probabilities
from app.ui.styles import result_tag, prob_bar_html, alert_card_html
from app.config import (
    ROLLING_WINDOW_OPTIONS, ROLLING_WINDOW_DEFAULT,
    MIN_MATCHES_FOR_STATS, LEAGUES,
)
from app.i18n import t


def _form_log_html(match_log: list[dict]) -> str:
    rows = []
    for m in reversed(match_log):
        tag = result_tag(m["result"])
        venue = "🏠" if m["venue"] == "C" else "✈️"
        rows.append(
            f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
            f'{tag} {venue} <span style="color:#b0bec5;font-size:0.82rem;">'
            f'{m["score"]} vs <b>{m["opponent"]}</b> ({m["date"]})</span></div>'
        )
    return "\n".join(rows) if rows else "<span style='color:#8b9ab0'>—</span>"


def _radar_chart(home_stats: dict, away_stats: dict) -> go.Figure:
    categories = ["Goals", "Shots", "SoT", "Corners", "xG"]
    home_vals = [
        home_stats.get("avg_goals", 0),
        home_stats.get("avg_shots", 0) / 3,
        home_stats.get("avg_shots_on", 0),
        home_stats.get("avg_corners", 0) / 2,
        home_stats.get("avg_xg_proxy", 0),
    ]
    away_vals = [
        away_stats.get("avg_goals", 0),
        away_stats.get("avg_shots", 0) / 3,
        away_stats.get("avg_shots_on", 0),
        away_stats.get("avg_corners", 0) / 2,
        away_stats.get("avg_xg_proxy", 0),
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=home_vals + [home_vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=home_stats.get("team", "Home"),
        line_color="#00d4aa",
        fillcolor="rgba(0,212,170,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=away_vals + [away_vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=away_stats.get("team", "Away"),
        line_color="#7c4dff",
        fillcolor="rgba(124,77,255,0.15)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1f2e",
            radialaxis=dict(visible=True, range=[0, 5], gridcolor="#2a3040",
                            tickfont=dict(color="#8b9ab0")),
            angularaxis=dict(gridcolor="#2a3040", tickfont=dict(color="#b0bec5")),
        ),
        showlegend=True,
        paper_bgcolor="#0e1117",
        font=dict(color="#b0bec5"),
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(bgcolor="#1a1f2e", bordercolor="#2a3040", borderwidth=1),
    )
    return fig


def _get_teams_by_league(df: pd.DataFrame, league_code: str | None) -> list[str]:
    """Devuelve los equipos de una liga específica (o de todas si league_code is None)."""
    source = df if league_code is None else df[df["Div"] == league_code]
    if source.empty:
        return []
    teams = set(source["HomeTeam"].dropna()) | set(source["AwayTeam"].dropna())
    return sorted(teams)


def _player_comparison(df_players: pd.DataFrame, home_team: str, away_team: str) -> None:
    """Muestra tabla side-by-side con top jugadores de cada equipo."""
    st.divider()
    st.markdown(f"#### {t('cmp_players_title')}")

    if df_players is None or df_players.empty:
        st.info(t("cmp_players_none"))
        return

    def _top_players(team: str, n: int = 6) -> pd.DataFrame:
        grp = df_players[df_players["team"] == team]
        if grp.empty:
            return pd.DataFrame()
        agg = (
            grp.groupby("player")
            .agg(
                Tiros=("sh", "mean"),
                APuerta=("sot", "mean"),
                Goles=("gls", "sum"),
                Asis=("ast", "sum"),
                PJ=("player", "count"),
            )
            .sort_values("Tiros", ascending=False)
            .head(n)
            .reset_index()
        )
        agg["Tiros"] = agg["Tiros"].round(2)
        agg["APuerta"] = agg["APuerta"].round(2)
        agg.columns = [
            t("player"), t("shots"), t("shots_on"),
            t("goals"), t("assists"), t("matches"),
        ]
        return agg

    home_df = _top_players(home_team)
    away_df = _top_players(away_team)

    if home_df.empty and away_df.empty:
        st.info(t("cmp_players_none"))
        return

    st.caption(t("cmp_players_top"))
    cp_l, cp_r = st.columns(2)
    with cp_l:
        st.markdown(f"**🏠 {home_team}**")
        if home_df.empty:
            st.caption("—")
        else:
            st.dataframe(home_df, hide_index=True, use_container_width=True)
    with cp_r:
        st.markdown(f"**✈️ {away_team}**")
        if away_df.empty:
            st.caption("—")
        else:
            st.dataframe(away_df, hide_index=True, use_container_width=True)


def render(df: pd.DataFrame, teams: list[str], df_players: pd.DataFrame | None = None) -> None:
    """Renderiza la pestaña Comparador."""
    st.markdown(f"### {t('cmp_title')}")

    # ── Filtro de división ──────────────────────────────────────────────────
    league_options = ["ALL"] + list(LEAGUES.keys())

    def _league_label(code: str) -> str:
        if code == "ALL":
            return t("league_all")
        if code == "SP1":
            return t("league_sp1")
        if code == "SP2":
            return t("league_sp2")
        return code

    # Leer pre-carga desde session_state (viene del Inicio)
    preload_league = st.session_state.pop("cmp_preload_league", None)
    default_league_idx = league_options.index(preload_league) if preload_league in league_options else 0

    league_choice = st.radio(
        t("cmp_league"),
        options=league_options,
        format_func=_league_label,
        horizontal=True,
        index=default_league_idx,
        key="cmp_league_radio",
    )
    league_code = None if league_choice == "ALL" else league_choice
    filtered_teams = _get_teams_by_league(df, league_code) if league_code else teams

    if not filtered_teams:
        st.warning(t("cmp_no_data"))
        return

    # ── Selectores de equipos ───────────────────────────────────────────────
    preload_home = st.session_state.pop("cmp_preload_home", None)
    preload_away = st.session_state.pop("cmp_preload_away", None)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if preload_home and preload_home in filtered_teams:
            default_home = filtered_teams.index(preload_home)
        else:
            default_home = filtered_teams.index("Real Madrid") if "Real Madrid" in filtered_teams else 0
        local = st.selectbox(t("cmp_home"), filtered_teams, index=default_home, key="cmp_home_sel")
    with col2:
        away_teams_list = [t_ for t_ in filtered_teams if t_ != local]
        if not away_teams_list:
            st.warning(t("cmp_no_data"))
            return
        if preload_away and preload_away in away_teams_list:
            default_away = away_teams_list.index(preload_away)
        else:
            default_away = away_teams_list.index("Barcelona") if "Barcelona" in away_teams_list else 0
        visitante = st.selectbox(t("cmp_away"), away_teams_list, index=default_away, key="cmp_away_sel")
    with col3:
        n = st.selectbox(
            t("cmp_last"),
            ROLLING_WINDOW_OPTIONS,
            index=ROLLING_WINDOW_OPTIONS.index(ROLLING_WINDOW_DEFAULT),
            key="cmp_n",
        )

    # Auto-analizar si venimos de pre-carga, si no esperar al botón
    auto_analyze = bool(preload_home and preload_away)
    analizar = st.button(t("cmp_analyze"), type="primary", use_container_width=True)

    if not (analizar or auto_analyze):
        st.markdown(
            f'<div style="text-align:center;color:#8b9ab0;margin-top:60px;font-size:1.1rem;">'
            f'{t("cmp_select_prompt")}</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Calcular stats ──────────────────────────────────────────────────────
    # Si hay filtro de liga, restringir df a esa liga; si no, usar todo
    df_source = df[df["Div"] == league_code].copy() if league_code else df

    with st.spinner("..."):
        home_stats = get_recent_form(df_source, local, venue="Home", n=n)
        away_stats = get_recent_form(df_source, visitante, venue="Away", n=n)
        h2h_sum = get_h2h_summary(df_source, local, visitante)

    if not home_stats or not away_stats:
        st.warning(t("cmp_no_data"))
        return

    # ── Layout principal ────────────────────────────────────────────────────
    st.divider()

    c_home, c_away = st.columns(2)

    with c_home:
        st.markdown(f"#### 🏠 {local}")
        st.markdown(
            f"**{home_stats['wins']}{t('cmp_wins')} · {home_stats['draws']}{t('cmp_draws')} · "
            f"{home_stats['losses']}{t('cmp_losses')}** "
            f"({t('cmp_last_home', n=home_stats['matches_analyzed'])})"
        )
        st.markdown(_form_log_html(home_stats["match_log"]), unsafe_allow_html=True)
        st.markdown("---")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric(t("cmp_goals_match"), f"{home_stats['avg_goals']:.1f}")
        mc2.metric(t("cmp_shots_on"), f"{home_stats['avg_shots_on']:.1f}")
        mc3.metric(t("cmp_xg_proxy"), f"{home_stats['avg_xg_proxy']:.2f}")
        mc1.metric(t("cmp_corners"), f"{home_stats['avg_corners']:.1f}")
        mc2.metric(t("cmp_cards"), f"{home_stats['avg_cards']:.1f}")
        mc3.metric(t("cmp_over25"), f"{int(home_stats['over25_rate']*100)}%")

    with c_away:
        st.markdown(f"#### ✈️ {visitante}")
        st.markdown(
            f"**{away_stats['wins']}{t('cmp_wins')} · {away_stats['draws']}{t('cmp_draws')} · "
            f"{away_stats['losses']}{t('cmp_losses')}** "
            f"({t('cmp_last_away', n=away_stats['matches_analyzed'])})"
        )
        st.markdown(_form_log_html(away_stats["match_log"]), unsafe_allow_html=True)
        st.markdown("---")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric(t("cmp_goals_match"), f"{away_stats['avg_goals']:.1f}")
        mc2.metric(t("cmp_shots_on"), f"{away_stats['avg_shots_on']:.1f}")
        mc3.metric(t("cmp_xg_proxy"), f"{away_stats['avg_xg_proxy']:.2f}")
        mc1.metric(t("cmp_corners"), f"{away_stats['avg_corners']:.1f}")
        mc2.metric(t("cmp_cards"), f"{away_stats['avg_cards']:.1f}")
        mc3.metric(t("cmp_over25"), f"{int(away_stats['over25_rate']*100)}%")

    st.divider()

    # ── Radar + Probabilidades ──────────────────────────────────────────────
    col_radar, col_probs = st.columns([1, 1])

    with col_radar:
        st.markdown(f"#### {t('cmp_radar')}")
        fig = _radar_chart(home_stats, away_stats)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_probs:
        st.markdown(f"#### {t('cmp_probs')}")
        probs = calculate_probabilities(home_stats, away_stats, h2h_sum or None)
        fair_odds = probs.implied_odds()

        st.markdown(prob_bar_html(f"🏠 {local}", probs.home, "#00d4aa"), unsafe_allow_html=True)
        st.markdown(prob_bar_html(f"⚖️ {t('draw')}", probs.draw, "#f0c040"), unsafe_allow_html=True)
        st.markdown(prob_bar_html(f"✈️ {visitante}", probs.away, "#7c4dff"), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(prob_bar_html("⚽ Over 2.5", probs.over25, "#ff8f00"), unsafe_allow_html=True)
        st.markdown(prob_bar_html(t("cmp_btts"), probs.btts, "#29b6f6"), unsafe_allow_html=True)

        st.caption(
            f"{t('cmp_fair_odds')}: "
            f"{t('home')} {fair_odds['home']} · {t('draw')} {fair_odds['draw']} · "
            f"{t('away')} {fair_odds['away']}"
        )

    st.divider()

    # ── Smart Alerts ────────────────────────────────────────────────────────
    st.markdown(f"#### {t('cmp_alerts')}")
    alerts = generate_alerts(home_stats, away_stats, h2h_sum or None,
                             n=n, min_strength=AlertStrength.MEDIUM)
    if alerts:
        alert_html = "".join(alert_card_html(a) for a in alerts)
        st.markdown(alert_html, unsafe_allow_html=True)
    else:
        st.info(t("cmp_no_alerts"))

    # ── H2H resumen ─────────────────────────────────────────────────────────
    if h2h_sum and h2h_sum.get("total", 0) > 0:
        with st.expander(t("cmp_h2h_header", n=h2h_sum["total"])):
            c1, c2, c3 = st.columns(3)
            c1.metric(t("cmp_h2h_wins_t1", team=local[:12]), h2h_sum["wins_team1"])
            c2.metric(t("cmp_h2h_draws"), h2h_sum["draws"])
            c3.metric(t("cmp_h2h_wins_t1", team=visitante[:12]), h2h_sum["wins_team2"])
            c1.metric(t("cmp_h2h_avg"), h2h_sum["avg_goals"])
            c2.metric(t("cmp_over25"), f"{int(h2h_sum['over25_rate']*100)}%")
            c3.metric("BTTS", f"{int(h2h_sum['btts_rate']*100)}%")

    # ── Comparativa de jugadores ────────────────────────────────────────────
    _player_comparison(df_players, local, visitante)
