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


def render_backtesting_lab(df: pd.DataFrame) -> None:
    """Sub-pestaña: Laboratorio de Backtesting histórico."""
    from app.engine.backtester import Backtester
    import plotly.express as px

    st.markdown("#### 🧪 Laboratorio de Backtesting Pro")
    st.caption("Valida tus hipótesis de análisis con datos históricos reales (20 años).")

    with st.expander("🛠️ Configurar Estrategia", expanded=True):
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            market = st.selectbox("Mercado", ["1", "X", "2", "Over 2.5"], key="bt_market")
        with col2:
            metric = st.selectbox("Métrica Base (Rolling)", [
                "Home_Roll_Goals", "Away_Roll_Goals", 
                "Home_Roll_Corners", "Away_Roll_Corners",
                "Home_Roll_Shots", "Away_Roll_Shots"
            ], key="bt_metric")
        with col3:
            threshold = st.number_input("Valor Mínimo Métrica", value=1.5, step=0.1, key="bt_thresh")
            
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            min_o = st.slider("Cuota Mínima", 1.01, 10.0, 1.10)
        with col_o2:
            max_o = st.slider("Cuota Máxima", 1.01, 10.0, 5.0)

    if st.button("🚀 EJECUTAR BACKTEST", use_container_width=True):
        with st.spinner("Escaneando el histórico..."):
            tester = Backtester(df)
            result = tester.run_strategy(market, threshold, metric, min_o, max_o)
            summary = result.get_summary()
            
            if not summary:
                st.warning("No se encontraron partidos con esos filtros.")
                return

            st.success(f"Simulación completada sobre **{summary['total_bets']}** partidos.")
            
            # Dashboard de resultados
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Yield (ROI)", f"{summary['yield_roi']:.2f}%")
            m2.metric("Win Rate", f"{summary['win_rate']:.1f}%")
            m3.metric("Profit Total", f"{summary['total_profit']:.2f}u")
            m4.metric("Max Drawdown", f"{summary['max_drawdown']:.2f}u")

            # Curva de Equity
            fig = px.line(x=list(range(len(summary['equity_curve']))), y=summary['equity_curve'],
                          title="Curva de Rendimiento (Unidades)",
                          labels={'x': 'Número de Apuesta', 'y': 'Banca (u)'},
                          color_discrete_sequence=["#00d4aa"])
            fig.update_layout(paper_bgcolor="#0b0f1a", plot_bgcolor="#0b0f1a", font=dict(color="#8b9ab0"))
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de trades
            with st.expander("Ver detalle de operaciones"):
                st.dataframe(result.trades[["date", "match", "odds", "won", "profit", "balance"]], 
                             use_container_width=True, hide_index=True)


def render(df: pd.DataFrame, teams: list[str]) -> None:
    """Renderiza la pestaña Value Detection con sub-tabs actualizadas."""
    st.markdown("### 💎 Value Detection")

    sub1, sub2, sub3 = st.tabs(["🎯 Analizar Partido", "🔬 Scanner Histórico", "🧪 Lab Backtesting"])
    with sub1:
        render_partido_tab(df, teams)
    with sub2:
        render_scanner_tab(df)
    with sub3:
        render_backtesting_lab(df)
