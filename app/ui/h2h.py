"""
Tab 2 — Historial H2H.
Muestra todos los enfrentamientos históricos entre dos equipos con cuotas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.engine.metrics import get_h2h, get_h2h_summary
from app.config import CURRENT_SEASON_LABEL


def _timeline_chart(df_h2h_full: pd.DataFrame, team1: str, team2: str) -> go.Figure:
    """Gráfico de barras de goles por partido en H2H."""
    df = df_h2h_full.sort_values("Date", ascending=True).tail(15).copy()
    if df.empty:
        return None

    labels = df.apply(
        lambda r: f"{r['HomeTeam'][:3].upper()} vs {r['AwayTeam'][:3].upper()}<br>{r['Date'].strftime('%m/%Y')}",
        axis=1
    ).tolist()

    home_goals = pd.to_numeric(df["FTHG"], errors="coerce").fillna(0).tolist()
    away_goals = pd.to_numeric(df["FTAG"], errors="coerce").fillna(0).tolist()

    fig = go.Figure(data=[
        go.Bar(name="Goles Local", x=labels, y=home_goals, marker_color="#00d4aa"),
        go.Bar(name="Goles Visitante", x=labels, y=away_goals, marker_color="#7c4dff"),
    ])
    fig.update_layout(
        barmode="group",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1f2e",
        font=dict(color="#b0bec5", size=10),
        xaxis=dict(gridcolor="#2a3040", tickangle=-30),
        yaxis=dict(gridcolor="#2a3040", title="Goles"),
        legend=dict(bgcolor="#1a1f2e"),
        height=280,
        margin=dict(l=10, r=10, t=10, b=60),
    )
    return fig


def render(df: pd.DataFrame, teams: list[str]) -> None:
    """Renderiza la pestaña Historial H2H."""
    st.markdown("### 📚 Historial de Enfrentamientos Directos")
    st.caption(f"Base de datos histórica desde 2004 · Temporada actual: {CURRENT_SEASON_LABEL}")

    col1, col2 = st.columns(2)
    with col1:
        default1 = teams.index("Real Madrid") if "Real Madrid" in teams else 0
        t1 = st.selectbox("Equipo 1", teams, index=default1, key="h2h_t1")
    with col2:
        other = [t for t in teams if t != t1]
        default2 = other.index("Barcelona") if "Barcelona" in other else 0
        t2 = st.selectbox("Equipo 2", other, index=default2, key="h2h_t2")

    # Obtener datos
    h2h_display = get_h2h(df, t1, t2)
    h2h_sum = get_h2h_summary(df, t1, t2)

    if h2h_display is None or h2h_display.empty:
        st.info(f"No hay enfrentamientos registrados entre **{t1}** y **{t2}** en la base de datos.")
        return

    # ── Resumen estadístico ──────────────────────────────────────────────────
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total partidos", h2h_sum.get("total", 0))
    c2.metric(f"Victorias {t1[:10]}", h2h_sum.get("wins_team1", 0))
    c3.metric("Empates", h2h_sum.get("draws", 0))
    c4.metric(f"Victorias {t2[:10]}", h2h_sum.get("wins_team2", 0))
    c5.metric("Goles/partido", h2h_sum.get("avg_goals", 0))

    col_a, col_b = st.columns(2)
    col_a.metric("Over 2.5 rate", f"{int(h2h_sum.get('over25_rate', 0)*100)}%")
    col_b.metric("BTTS rate", f"{int(h2h_sum.get('btts_rate', 0)*100)}%")

    st.divider()

    # ── Gráfico de goles ─────────────────────────────────────────────────────
    raw_mask = (
        ((df["HomeTeam"] == t1) & (df["AwayTeam"] == t2)) |
        ((df["HomeTeam"] == t2) & (df["AwayTeam"] == t1))
    )
    raw_h2h = df[raw_mask].copy()
    fig = _timeline_chart(raw_h2h, t1, t2)
    if fig:
        st.markdown("##### Goles por partido (últimos 15 enfrentamientos)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Tabla completa ───────────────────────────────────────────────────────
    st.markdown(f"##### Todos los enfrentamientos ({len(h2h_display)})")

    # Renombrar columnas para visualización
    display = h2h_display.rename(columns={
        "Date": "Fecha",
        "Resultado": "Resultado",
        "B365H": f"Cuota Local",
        "B365D": "Cuota Empate",
        "B365A": f"Cuota Visitante",
        "Liga": "Liga",
    })

    col_config = {
        "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
        "Cuota Local": st.column_config.NumberColumn("Cuota Local", format="%.2f"),
        "Cuota Empate": st.column_config.NumberColumn("Cuota Empate", format="%.2f"),
        "Cuota Visitante": st.column_config.NumberColumn("Cuota Visit.", format="%.2f"),
    }

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        column_config=col_config,
    )
