"""
Tab 3 — Player Scouting.
Perfiles individuales de jugadores y análisis por métricas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def _sparkline(values: list[float], color: str = "#00d4aa") -> go.Figure:
    """Mini gráfico de línea para tendencia de un jugador."""
    fig = go.Figure(go.Scatter(
        y=values, mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=5, color=color),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=80,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, zeroline=False),
        showlegend=False,
    )
    return fig


def _metric_search(df_players: pd.DataFrame) -> None:
    """Sección de búsqueda por consistencia estadística."""
    st.markdown("---")
    st.markdown("#### 🔍 Buscador por Métrica")
    st.caption("Encuentra jugadores que superen un umbral estadístico con alta consistencia")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric = st.selectbox("Métrica", ["Tiros Totales", "Tiros a Puerta", "Faltas", "Tarjetas"], key="pp_metric")
    with col2:
        line = st.number_input("Umbral (superar)", min_value=0.5, max_value=8.0, step=0.5, value=1.5, key="pp_line")
    with col3:
        min_games = st.slider("Mínimo partidos", 3, 15, 5, key="pp_min_games")
    with col4:
        min_pct = st.slider("% Mínimo acierto", 50, 100, 65, key="pp_min_pct")

    col_map = {"Tiros Totales": "sh", "Tiros a Puerta": "sot", "Faltas": "fls", "Tarjetas": "crdy"}
    metric_col = col_map[metric]

    if st.button("🔍 BUSCAR JUGADORES", type="primary"):
        results = []
        for (player, team), grp in df_players.groupby(["player", "team"]):
            grp_sorted = grp.sort_values("date", ascending=False).head(min_games)
            if len(grp_sorted) < min_games:
                continue
            vals = pd.to_numeric(grp_sorted[metric_col], errors="coerce").dropna()
            if len(vals) == 0:
                continue
            success = int((vals > line).sum())
            pct = success / len(vals) * 100
            if pct < min_pct:
                continue
            avg = float(vals.mean())
            last5 = grp_sorted.head(5)[metric_col].tolist()
            results.append({
                "Jugador": player,
                "Equipo": team,
                "% Acierto": f"{pct:.0f}%",
                f"Media {metric}": f"{avg:.2f}",
                "Último": f"{float(grp_sorted.iloc[0][metric_col]):.1f}",
                "Últimos 5": " ".join(
                    "✅" if float(v) > line else "❌" for v in last5
                ),
                "_pct": pct,
            })

        if results:
            results_df = pd.DataFrame(results).sort_values("_pct", ascending=False).drop(columns=["_pct"])
            st.success(f"✅ {len(results_df)} jugadores encontrados")
            st.dataframe(results_df, hide_index=True, use_container_width=True)
        else:
            st.info("No se encontraron jugadores que cumplan los criterios.")


def render(df_players: pd.DataFrame) -> None:
    """Renderiza la pestaña Player Scouting."""
    st.markdown("### ⚽ Player Scouting")

    if df_players is None or df_players.empty:
        st.warning(
            "No hay datos de jugadores disponibles. "
            "Ejecuta `python -m app.data.player_scraper` para descargarlos."
        )
        return

    # ── Selector de equipo / jugador ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        teams = sorted(df_players["team"].dropna().unique().tolist())
        team = st.selectbox("Equipo", teams, key="scout_team")
    with col2:
        players = sorted(df_players[df_players["team"] == team]["player"].dropna().unique().tolist())
        if not players:
            st.warning("Sin jugadores para este equipo.")
            return
        player = st.selectbox("Jugador", players, key="scout_player")

    player_df = df_players[df_players["player"] == player].sort_values("date", ascending=False)

    if player_df.empty:
        st.info("Sin datos para este jugador.")
        return

    st.divider()

    # ── Métricas resumen ─────────────────────────────────────────────────────
    last10 = player_df.head(10)
    st.markdown(f"#### {player} · {team}")
    st.caption(f"Últimos {len(last10)} partidos de la temporada actual")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Goles", f"{last10['gls'].mean():.2f}/pj")
    m2.metric("Tiros", f"{last10['sh'].mean():.2f}/pj")
    m3.metric("A Puerta", f"{last10['sot'].mean():.2f}/pj")
    m4.metric("Faltas", f"{last10['fls'].mean():.2f}/pj")
    m5.metric("Tarjetas", f"{last10['crdy'].mean():.2f}/pj")

    # ── Sparklines de tendencia ──────────────────────────────────────────────
    col_sh, col_sot, col_fls = st.columns(3)
    with col_sh:
        st.caption("Tiros por partido")
        vals = last10["sh"].tolist()[::-1]
        if vals:
            st.plotly_chart(_sparkline(vals, "#00d4aa"), use_container_width=True, config={"displayModeBar": False})
    with col_sot:
        st.caption("Tiros a puerta")
        vals = last10["sot"].tolist()[::-1]
        if vals:
            st.plotly_chart(_sparkline(vals, "#7c4dff"), use_container_width=True, config={"displayModeBar": False})
    with col_fls:
        st.caption("Faltas cometidas")
        vals = last10["fls"].tolist()[::-1]
        if vals:
            st.plotly_chart(_sparkline(vals, "#ff8f00"), use_container_width=True, config={"displayModeBar": False})

    # ── Tabla detallada ──────────────────────────────────────────────────────
    st.markdown("##### Partido a partido (últimos 10)")
    display_cols = ["date", "sh", "sot", "gls", "ast", "fls", "crdy"]
    display_cols = [c for c in display_cols if c in player_df.columns]
    display = player_df.head(10)[display_cols].rename(columns={
        "date": "Fecha", "sh": "Tiros", "sot": "A Puerta",
        "gls": "Goles", "ast": "Asistencias", "fls": "Faltas", "crdy": "T.Amarillas",
    })
    col_config = {
        "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
    }
    st.dataframe(display, hide_index=True, use_container_width=True, column_config=col_config)

    # ── Top jugadores del equipo ──────────────────────────────────────────────
    with st.expander(f"📊 Rankings del equipo {team}"):
        team_df = df_players[df_players["team"] == team]
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Top rematadores (media tiros/pj)")
            top_sh = (
                team_df.groupby("player")["sh"].mean()
                .sort_values(ascending=False).head(8).reset_index()
            )
            top_sh.columns = ["Jugador", "Media Tiros"]
            top_sh["Media Tiros"] = top_sh["Media Tiros"].round(2)
            st.dataframe(top_sh, hide_index=True, use_container_width=True)
        with c2:
            st.caption("Top infractores (media faltas/pj)")
            top_fls = (
                team_df.groupby("player")["fls"].mean()
                .sort_values(ascending=False).head(8).reset_index()
            )
            top_fls.columns = ["Jugador", "Media Faltas"]
            top_fls["Media Faltas"] = top_fls["Media Faltas"].round(2)
            st.dataframe(top_fls, hide_index=True, use_container_width=True)

    # ── Búsqueda por métrica ──────────────────────────────────────────────────
    _metric_search(df_players)
