"""
Tab 1 — Comparador de Partido.
Muestra forma reciente de ambos equipos, Smart Alerts y probabilidades matemáticas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.engine.metrics import get_recent_form, get_h2h_summary
from app.engine.smart_alerts import generate_alerts, AlertStrength
from app.engine.probability import calculate_probabilities
from app.ui.styles import result_tag, prob_bar_html, alert_card_html
from app.config import ROLLING_WINDOW_OPTIONS, ROLLING_WINDOW_DEFAULT, MIN_MATCHES_FOR_STATS


def _form_log_html(match_log: list[dict]) -> str:
    """Genera HTML del historial de partidos."""
    rows = []
    for m in reversed(match_log):  # más reciente arriba
        tag = result_tag(m["result"])
        venue = "🏠" if m["venue"] == "C" else "✈️"
        rows.append(
            f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
            f'{tag} {venue} <span style="color:#b0bec5;font-size:0.82rem;">'
            f'{m["score"]} vs <b>{m["opponent"]}</b> ({m["date"]})</span></div>'
        )
    return "\n".join(rows) if rows else "<span style='color:#8b9ab0'>Sin partidos recientes</span>"


def _radar_chart(home_stats: dict, away_stats: dict) -> go.Figure:
    """Gráfico de araña comparando métricas normalizadas de ambos equipos."""
    categories = ["Goles", "Tiros", "A Puerta", "Córners", "xG (proxy)"]
    home_vals = [
        home_stats.get("avg_goals", 0),
        home_stats.get("avg_shots", 0) / 3,      # normalizar /3 para escala ~0-5
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
        name=home_stats.get("team", "Local"),
        line_color="#00d4aa",
        fillcolor="rgba(0,212,170,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=away_vals + [away_vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=away_stats.get("team", "Visitante"),
        line_color="#7c4dff",
        fillcolor="rgba(124,77,255,0.15)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1f2e",
            radialaxis=dict(visible=True, range=[0, 5], gridcolor="#2a3040", tickfont=dict(color="#8b9ab0")),
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


def render(df: pd.DataFrame, teams: list[str]) -> None:
    """Renderiza la pestaña Comparador."""
    st.markdown("### ⚡ Análisis Pre-Partido")

    # ── Selectores ──────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        default_home = teams.index("Real Madrid") if "Real Madrid" in teams else 0
        local = st.selectbox("🏠 Equipo Local", teams, index=default_home, key="cmp_home")
    with col2:
        away_teams = [t for t in teams if t != local]
        default_away = away_teams.index("Barcelona") if "Barcelona" in away_teams else 0
        visitante = st.selectbox("✈️ Equipo Visitante", away_teams, index=default_away, key="cmp_away")
    with col3:
        n = st.selectbox("Últimos", ROLLING_WINDOW_OPTIONS, index=ROLLING_WINDOW_OPTIONS.index(ROLLING_WINDOW_DEFAULT), key="cmp_n")

    analizar = st.button("📊 ANALIZAR PARTIDO", type="primary", use_container_width=True)

    if not analizar:
        st.markdown(
            '<div style="text-align:center;color:#8b9ab0;margin-top:60px;font-size:1.1rem;">'
            '⚽ Selecciona dos equipos y pulsa ANALIZAR</div>',
            unsafe_allow_html=True
        )
        return

    # ── Calcular stats ───────────────────────────────────────────────────────
    with st.spinner("Calculando..."):
        home_stats = get_recent_form(df, local, venue="Home", n=n)
        away_stats = get_recent_form(df, visitante, venue="Away", n=n)
        h2h_sum = get_h2h_summary(df, local, visitante)

    if not home_stats or not away_stats:
        st.warning("No hay suficientes datos recientes para uno o ambos equipos en la temporada actual.")
        return

    # ── Layout principal ─────────────────────────────────────────────────────
    st.divider()

    # Forma reciente — dos columnas
    c_home, c_away = st.columns(2)

    with c_home:
        st.markdown(f"#### 🏠 {local}")
        st.markdown(
            f"**{home_stats['wins']}G · {home_stats['draws']}E · {home_stats['losses']}P** "
            f"(últimos {home_stats['matches_analyzed']} en casa)",
        )
        st.markdown(_form_log_html(home_stats["match_log"]), unsafe_allow_html=True)
        st.markdown("---")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Goles/partido", f"{home_stats['avg_goals']:.1f}")
        mc2.metric("Tiros a puerta", f"{home_stats['avg_shots_on']:.1f}")
        mc3.metric("xG (proxy)", f"{home_stats['avg_xg_proxy']:.2f}")
        mc1.metric("Córners", f"{home_stats['avg_corners']:.1f}")
        mc2.metric("Tarjetas", f"{home_stats['avg_cards']:.1f}")
        mc3.metric("Over 2.5 rate", f"{int(home_stats['over25_rate']*100)}%")

    with c_away:
        st.markdown(f"#### ✈️ {visitante}")
        st.markdown(
            f"**{away_stats['wins']}G · {away_stats['draws']}E · {away_stats['losses']}P** "
            f"(últimos {away_stats['matches_analyzed']} fuera)",
        )
        st.markdown(_form_log_html(away_stats["match_log"]), unsafe_allow_html=True)
        st.markdown("---")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Goles/partido", f"{away_stats['avg_goals']:.1f}")
        mc2.metric("Tiros a puerta", f"{away_stats['avg_shots_on']:.1f}")
        mc3.metric("xG (proxy)", f"{away_stats['avg_xg_proxy']:.2f}")
        mc1.metric("Córners", f"{away_stats['avg_corners']:.1f}")
        mc2.metric("Tarjetas", f"{away_stats['avg_cards']:.1f}")
        mc3.metric("Over 2.5 rate", f"{int(away_stats['over25_rate']*100)}%")

    st.divider()

    # ── Radar + Probabilidades ────────────────────────────────────────────────
    col_radar, col_probs = st.columns([1, 1])

    with col_radar:
        st.markdown("#### 📡 Comparativa Visual")
        fig = _radar_chart(home_stats, away_stats)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_probs:
        st.markdown("#### 🎯 Probabilidades Matemáticas")
        probs = calculate_probabilities(home_stats, away_stats, h2h_sum or None)
        fair_odds = probs.implied_odds()

        st.markdown(prob_bar_html(f"🏠 {local}", probs.home, "#00d4aa"), unsafe_allow_html=True)
        st.markdown(prob_bar_html("⚖️ Empate", probs.draw, "#f0c040"), unsafe_allow_html=True)
        st.markdown(prob_bar_html(f"✈️ {visitante}", probs.away, "#7c4dff"), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(prob_bar_html("⚽ Over 2.5", probs.over25, "#ff8f00"), unsafe_allow_html=True)
        st.markdown(prob_bar_html("🔵 Ambos marcan", probs.btts, "#29b6f6"), unsafe_allow_html=True)

        st.caption(
            f"Cuotas justas estimadas: "
            f"Local {fair_odds['home']} · Empate {fair_odds['draw']} · Visitante {fair_odds['away']}"
        )

    st.divider()

    # ── Smart Alerts ──────────────────────────────────────────────────────────
    st.markdown("#### 🔔 Smart Alerts")
    alerts = generate_alerts(home_stats, away_stats, h2h_sum or None, n=n, min_strength=AlertStrength.MEDIUM)

    if alerts:
        alert_html = "".join(alert_card_html(a) for a in alerts)
        st.markdown(alert_html, unsafe_allow_html=True)
    else:
        st.info("No se detectaron tendencias significativas para este partido.")

    # ── H2H resumen ───────────────────────────────────────────────────────────
    if h2h_sum and h2h_sum.get("total", 0) > 0:
        with st.expander(f"📚 Historial H2H ({h2h_sum['total']} enfrentamientos)"):
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Victorias {local}", h2h_sum["wins_team1"])
            c2.metric("Empates", h2h_sum["draws"])
            c3.metric(f"Victorias {visitante}", h2h_sum["wins_team2"])
            c1.metric("Media goles", h2h_sum["avg_goals"])
            c2.metric("Over 2.5 rate", f"{int(h2h_sum['over25_rate']*100)}%")
            c3.metric("BTTS rate", f"{int(h2h_sum['btts_rate']*100)}%")
