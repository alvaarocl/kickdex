"""
Tab 2 — Historial H2H.
Muestra todos los enfrentamientos históricos entre dos equipos con cuotas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.engine.metrics import get_h2h, get_h2h_summary
from app.config import CURRENT_SEASON_LABEL, LEAGUES
from app.i18n import t


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
    st.markdown(f"### {t('h2h_title')}")
    st.caption(t("h2h_subtitle", season=CURRENT_SEASON_LABEL))

    # Filtro por liga
    league_options = ["ALL"] + list(LEAGUES.keys())

    def _league_label(code: str) -> str:
        if code == "ALL":
            return t("league_all")
        if code == "SP1":
            return t("league_sp1")
        if code == "SP2":
            return t("league_sp2")
        return code

    league_choice = st.radio(
        t("cmp_league"),
        options=league_options,
        format_func=_league_label,
        horizontal=True,
        key="h2h_league",
    )
    league_code = None if league_choice == "ALL" else league_choice
    if league_code:
        source = df[df["Div"] == league_code]
        teams = sorted(set(source["HomeTeam"].dropna()) | set(source["AwayTeam"].dropna()))
    else:
        source = df

    if not teams:
        st.warning(t("cmp_no_data"))
        return

    col1, col2 = st.columns(2)
    with col1:
        default1 = teams.index("Real Madrid") if "Real Madrid" in teams else 0
        t1 = st.selectbox(t("h2h_team1"), teams, index=default1, key="h2h_t1")
    with col2:
        other = [x for x in teams if x != t1]
        if not other:
            st.warning(t("cmp_no_data"))
            return
        default2 = other.index("Barcelona") if "Barcelona" in other else 0
        t2 = st.selectbox(t("h2h_team2"), other, index=default2, key="h2h_t2")

    # Usar source filtrado
    df = source

    # Obtener datos
    h2h_display = get_h2h(df, t1, t2)
    h2h_sum = get_h2h_summary(df, t1, t2)

    if h2h_display is None or h2h_display.empty:
        st.info(t("h2h_empty", t1=t1, t2=t2))
        return

    # ── Resumen estadístico ──────────────────────────────────────────────────
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("h2h_total"), h2h_sum.get("total", 0))
    c2.metric(t("cmp_h2h_wins_t1", team=t1[:10]), h2h_sum.get("wins_team1", 0))
    c3.metric(t("cmp_h2h_draws"), h2h_sum.get("draws", 0))
    c4.metric(t("cmp_h2h_wins_t1", team=t2[:10]), h2h_sum.get("wins_team2", 0))
    c5.metric(t("cmp_h2h_avg"), h2h_sum.get("avg_goals", 0))

    col_a, col_b = st.columns(2)
    col_a.metric(t("cmp_over25"), f"{int(h2h_sum.get('over25_rate', 0)*100)}%")
    col_b.metric("BTTS", f"{int(h2h_sum.get('btts_rate', 0)*100)}%")

    st.divider()

    # ── Gráfico de goles ─────────────────────────────────────────────────────
    raw_mask = (
        ((df["HomeTeam"] == t1) & (df["AwayTeam"] == t2)) |
        ((df["HomeTeam"] == t2) & (df["AwayTeam"] == t1))
    )
    raw_h2h = df[raw_mask].copy()
    fig = _timeline_chart(raw_h2h, t1, t2)
    if fig:
        st.markdown(f"##### {t('h2h_goals_chart')}")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Tabla completa (ya incluye columna Liga) ────────────────────────────
    st.markdown(f"##### {t('h2h_all', n=len(h2h_display))}")

    display = h2h_display.rename(columns={
        "Date": t("date"),
        "Resultado": t("result"),
        "B365H": f"{t('odds')} {t('home')}",
        "B365D": f"{t('odds')} {t('draw')}",
        "B365A": f"{t('odds')} {t('away')}",
        "Liga": t("league"),
    })

    col_config = {
        t("date"): st.column_config.DateColumn(t("date"), format="DD/MM/YYYY"),
        f"{t('odds')} {t('home')}": st.column_config.NumberColumn(
            f"{t('odds')} {t('home')}", format="%.2f"
        ),
        f"{t('odds')} {t('draw')}": st.column_config.NumberColumn(
            f"{t('odds')} {t('draw')}", format="%.2f"
        ),
        f"{t('odds')} {t('away')}": st.column_config.NumberColumn(
            f"{t('odds')} {t('away')}", format="%.2f"
        ),
    }

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        column_config=col_config,
    )
