"""
Tab 4 — Value Detection.
Compara probabilidades matemáticas con cuotas reales de Bet365.
Scanner de patrones históricos de valor con EV positivo.
"""

import streamlit as st
import pandas as pd
import numpy as np

from app.engine.metrics import get_recent_form, get_h2h_summary
from app.engine.probability import calculate_probabilities
from app.engine.value_detector import calculate_value, scan_value_patterns
from app.ui.styles import alert_card_html
from app.config import DISCLAIMER, ROLLING_WINDOW_DEFAULT, ROLLING_WINDOW_OPTIONS


def _value_row_html(vr) -> str:
    """Renderiza una fila de value result como HTML."""
    ev_pct = f"{vr.ev * 100:+.1f}%"
    edge_pct = f"{vr.edge * 100:+.1f}%"
    color = vr.color
    bg = f"{color}15"  # 15% opacity
    return f"""
    <div style="background:{bg};border-left:3px solid {color};border-radius:6px;
                padding:10px 14px;margin-bottom:8px;display:flex;
                justify-content:space-between;align-items:center;">
        <div>
            <span style="color:{color};font-weight:700;font-size:0.9rem;">{vr.label}</span>
            <span style="color:#b0bec5;margin-left:10px;font-size:0.85rem;">{vr.market}</span>
        </div>
        <div style="display:flex;gap:18px;font-size:0.82rem;">
            <span style="color:#8b9ab0;">Nuestro: <b style="color:#e8eaf6">{int(vr.our_prob*100)}%</b></span>
            <span style="color:#8b9ab0;">Implícito: <b style="color:#e8eaf6">{int(vr.implied_prob*100)}%</b></span>
            <span style="color:#8b9ab0;">Cuota: <b style="color:#e8eaf6">{vr.odds:.2f}</b></span>
            <span style="color:#8b9ab0;">Edge: <b style="color:{color}">{edge_pct}</b></span>
            <span style="color:#8b9ab0;">EV: <b style="color:{color}">{ev_pct}</b></span>
        </div>
    </div>"""


def _get_latest_odds(df: pd.DataFrame, home: str, away: str) -> dict:
    """
    Intenta recuperar las cuotas Bet365 del último enfrentamiento conocido
    entre estos dos equipos como proxy (si no hay partido futuro en el CSV).
    En Fase 2, esto vendrá de la Odds API.
    """
    mask = (df["HomeTeam"] == home) & (df["AwayTeam"] == away)
    matches = df[mask].sort_values("Date", ascending=False)
    if matches.empty:
        return {}
    last = matches.iloc[0]
    result = {}
    for col in ["B365H", "B365D", "B365A", "B365>2.5"]:
        val = last.get(col)
        if val is not None and np.isfinite(float(val if val == val else 0)) and float(val if val == val else 0) > 1.0:
            result[col] = float(val)
    return result


def render_partido_tab(df: pd.DataFrame, teams: list[str]) -> None:
    """Sub-pestaña: análisis de un partido concreto."""
    st.markdown("#### 🎯 Value Analysis — Partido Concreto")
    st.caption(
        "Comparamos nuestra probabilidad matemática con las cuotas históricas de Bet365 "
        "para ese enfrentamiento. Las cuotas en tiempo real llegarán en Fase 2."
    )

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        home = st.selectbox("🏠 Local", teams, key="val_home")
    with col2:
        away_opts = [t for t in teams if t != home]
        away = st.selectbox("✈️ Visitante", away_opts, key="val_away")
    with col3:
        n = st.selectbox("Últimos N", ROLLING_WINDOW_OPTIONS,
                         index=ROLLING_WINDOW_OPTIONS.index(ROLLING_WINDOW_DEFAULT), key="val_n")

    if not st.button("⚡ CALCULAR VALUE", type="primary"):
        return

    with st.spinner("Calculando probabilidades..."):
        home_stats = get_recent_form(df, home, venue="Home", n=n)
        away_stats = get_recent_form(df, away, venue="Away", n=n)
        h2h_sum = get_h2h_summary(df, home, away)
        odds = _get_latest_odds(df, home, away)

    if not home_stats or not away_stats:
        st.warning("Datos insuficientes para calcular probabilidades.")
        return

    probs = calculate_probabilities(home_stats, away_stats, h2h_sum or None)

    st.divider()
    st.markdown(f"##### {home} vs {away}")

    if not odds:
        st.info(
            "No hay cuotas históricas de Bet365 para este enfrentamiento en la base de datos. "
            "Introduce las cuotas manualmente:"
        )
        c1, c2, c3, c4 = st.columns(4)
        odds["B365H"] = c1.number_input("Cuota Local", min_value=1.01, value=2.10, step=0.05, key="manual_h")
        odds["B365D"] = c2.number_input("Cuota Empate", min_value=1.01, value=3.40, step=0.05, key="manual_d")
        odds["B365A"] = c3.number_input("Cuota Visitante", min_value=1.01, value=3.20, step=0.05, key="manual_a")
        odds["B365>2.5"] = c4.number_input("Over 2.5", min_value=1.01, value=1.85, step=0.05, key="manual_o")

    value_results = calculate_value(
        probs,
        b365h=odds.get("B365H"),
        b365d=odds.get("B365D"),
        b365a=odds.get("B365A"),
        b365_over25=odds.get("B365>2.5"),
    )

    if not value_results:
        st.warning("No hay cuotas disponibles para calcular value.")
        return

    has_value = any(v.is_value for v in value_results)
    if has_value:
        st.success("🟢 Se detectaron potenciales Value Bets para este partido")
    else:
        st.info("⚪ No se detecta value claro en este partido según nuestro modelo")

    for vr in value_results:
        st.markdown(_value_row_html(vr), unsafe_allow_html=True)

    st.markdown(
        f'<div class="disclaimer">{DISCLAIMER}</div>',
        unsafe_allow_html=True
    )


def render_scanner_tab(df: pd.DataFrame) -> None:
    """Sub-pestaña: scanner de patrones históricos con EV positivo."""
    st.markdown("#### 🔬 Scanner de Patrones Históricos")
    st.caption(
        "Analiza el histórico de partidos con cuotas reales para encontrar "
        "condiciones estadísticas que históricamente han generado valor."
    )

    col1, col2 = st.columns(2)
    with col1:
        min_sample = st.slider("Muestra mínima (partidos)", 20, 100, 30, step=10, key="scan_sample")
    with col2:
        min_acc = st.slider("Acierto mínimo (%)", 55, 85, 60, step=5, key="scan_acc") / 100

    if not st.button("🔬 EJECUTAR SCANNER", type="primary", key="scan_btn"):
        return

    with st.spinner("Analizando patrones históricos... (puede tardar unos segundos)"):
        # Necesitamos rolling metrics para el scanner
        from app.engine.metrics import calculate_rolling_metrics
        df_processed = calculate_rolling_metrics(df)
        patterns = scan_value_patterns(df_processed, min_sample=min_sample, min_accuracy=min_acc)

    if patterns.empty:
        st.info("No se encontraron patrones que cumplan los criterios seleccionados.")
        st.caption("Prueba a reducir la muestra mínima o el acierto mínimo.")
        return

    st.success(f"✅ {len(patterns)} patrones de valor encontrados en el histórico")

    # Destacar los top 5
    st.markdown("##### Top patrones por EV")
    st.dataframe(
        patterns.head(20),
        hide_index=True,
        use_container_width=True,
        column_config={
            "EV %": st.column_config.TextColumn("EV %"),
            "Prob. Real": st.column_config.TextColumn("Prob. Real"),
        }
    )

    st.caption(
        "**Cómo leer esto:** 'Home_Roll_Goals ≥ 1.5' significa que el equipo local promediaba "
        "≥1.5 goles en sus últimos 5 partidos antes del partido. 'EV +8.5%' significa que, "
        "historicamente, apostando €100 en esos casos, se ganaba €108.5 de media."
    )

    st.markdown(
        f'<div class="disclaimer">{DISCLAIMER}</div>',
        unsafe_allow_html=True
    )


def render(df: pd.DataFrame, teams: list[str]) -> None:
    """Renderiza la pestaña Value Detection con sub-tabs."""
    st.markdown("### 💎 Value Detection")

    sub1, sub2 = st.tabs(["🎯 Analizar Partido", "🔬 Scanner Histórico"])
    with sub1:
        render_partido_tab(df, teams)
    with sub2:
        render_scanner_tab(df)
