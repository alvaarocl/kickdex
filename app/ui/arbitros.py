"""
UI — Panel de Árbitros.
Ventana temporal seleccionable + filtro por liga para todas las competiciones.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from app.engine.referees import get_referee_stats
from app.config import DISCLAIMER, LEAGUES

_WINDOW_OPTIONS = {
    "Temporada actual": "season",
    "Histórico completo":  None,
}

_LEAGUE_OPTIONS = {"Todas las ligas": None, **{v: k for k, v in LEAGUES.items()}}

_COLORS = ["#2EE6A6", "#fb7185", "#5BD6FF", "#F5B93C"]


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _radar(df: pd.DataFrame, refs: list[str]) -> go.Figure:
    cats = ["Amarillas/P", "Rojas/P", "Faltas/P", "Penaltis/P"]
    fig = go.Figure()
    for i, ref in enumerate(refs[:4]):
        row = df[df["Referee"] == ref]
        if row.empty:
            continue
        row = row.iloc[0]
        vals = [
            min((row.get("Amarillas/Part.") or 0) / 7,   1) * 100,
            min((row.get("Rojas/Part.")     or 0) / 0.6, 1) * 100,
            min((row.get("Faltas/Part.")    or 0) / 40,  1) * 100,
            min((row.get("Penaltis/Part.")  or 0) / 0.6, 1) * 100,
        ]
        r, g, b = _hex_to_rgb(_COLORS[i])
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=cats, fill="toself", name=ref,
            line_color=_COLORS[i],
            fillcolor=f"rgba({r},{g},{b},0.08)",
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 100]),
                   bgcolor="rgba(0,0,0,0)", gridcolor="rgba(255,255,255,.05)"),
        showlegend=True, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b9ab0", size=10),
        margin=dict(l=40, r=40, t=20, b=20), height=320,
    )
    return fig


def render(df: pd.DataFrame) -> None:
    st.markdown('<h2 class="section-h2">⚖️ Panel de Árbitros</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-desc">Perfil disciplinario por colegiado. '
        'Filtra por liga y alterna entre temporada actual e histórico completo.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        league_label = st.selectbox("🌍 Liga", list(_LEAGUE_OPTIONS.keys()), key="ref_league")
        league_code  = _LEAGUE_OPTIONS[league_label]
    with c2:
        window_label = st.selectbox("📅 Ventana", list(_WINDOW_OPTIONS.keys()), index=0, key="ref_window")
        window       = _WINDOW_OPTIONS[window_label]
    with c3:
        min_m = st.slider("Mín. partidos arbitrados", 1, 20, 5, key="ref_min")

    with st.spinner("Calculando estadísticas..."):
        stats = get_referee_stats(df, league_code=league_code, window=window, min_matches=min_m)

    if stats.empty:
        st.warning("No se encontraron árbitros con estos filtros. Prueba 'Todas las ligas' o reduce el mínimo de partidos.")
        return

    # ── KPIs ────────────────────────────────────────────────────────────────
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    top_am  = stats.sort_values("Amarillas/Part.", ascending=False).iloc[0]
    top_fa  = stats.sort_values("Faltas/Part.",    ascending=False).iloc[0]
    top_ro  = stats.sort_values("Rojas/Part.",     ascending=False).iloc[0]
    top_pen = stats.sort_values("Penaltis/Part.",  ascending=False).iloc[0]
    k1.metric("Más tarjetero 🟨",    top_am["Referee"],  f"{top_am['Amarillas/Part.']:.2f} am/p")
    k2.metric("Más riguroso ⏱️",     top_fa["Referee"],  f"{top_fa['Faltas/Part.']:.1f} fa/p")
    k3.metric("Más expulsiones 🟥",  top_ro["Referee"],  f"{top_ro['Rojas/Part.']:.2f} ro/p")
    k4.metric("Más penaltis 🎯",     top_pen["Referee"], f"{top_pen['Penaltis/Part.']:.2f} pen/p")

    # ── Búsqueda ────────────────────────────────────────────────────────────
    st.markdown("---")
    search   = st.text_input("🔍 Buscar árbitro", placeholder="Ej: Soto Grado, Gil Manzano...", key="ref_search")
    filtered = stats.copy()
    if search:
        filtered = filtered[filtered["Referee"].str.contains(search, case=False, na=False)]

    # ── Tabla ───────────────────────────────────────────────────────────────
    st.markdown(f"##### Ranking — {league_label} · {window_label}")

    display_cols = [c for c in ["Referee", "Liga", "Partidos", "Amarillas/Part.", "Rojas/Part.", "Faltas/Part.", "Penaltis/Part.", "Perfil"] if c in filtered.columns]
    col_cfg = {
        "Referee":         st.column_config.TextColumn("Árbitro",    width="medium"),
        "Liga":            st.column_config.TextColumn("Liga",        width="small"),
        "Partidos":        st.column_config.NumberColumn("Partidos",  format="%d"),
        "Amarillas/Part.": st.column_config.ProgressColumn("🟨 Amarillas/P", format="%.2f", min_value=0, max_value=7.0),
        "Rojas/Part.":     st.column_config.NumberColumn("🟥 Rojas/P",       format="%.2f"),
        "Faltas/Part.":    st.column_config.NumberColumn("⏱️ Faltas/P",      format="%.1f"),
        "Penaltis/Part.":  st.column_config.NumberColumn("🎯 Penaltis/P",    format="%.2f"),
        "Perfil":          st.column_config.TextColumn("Perfil"),
    }
    st.dataframe(
        filtered[display_cols].sort_values("Amarillas/Part.", ascending=False),
        use_container_width=True, hide_index=True, column_config=col_cfg, height=460,
    )

    # ── Radar comparativo ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### Comparador Visual")
    ref_list = filtered["Referee"].tolist()
    if len(ref_list) >= 2:
        sel = st.multiselect(
            "Selecciona hasta 4 árbitros:",
            ref_list, default=ref_list[:min(3, len(ref_list))],
            max_selections=4, key="ref_cmp",
        )
        if len(sel) >= 2:
            try:
                st.plotly_chart(_radar(filtered, sel), use_container_width=True, config={"displayModeBar": False})
            except Exception:
                st.info("Datos insuficientes para el radar con la selección actual.")
    else:
        st.info("Necesitas al menos 2 árbitros en el filtro para comparar.")

    # ── Histograma ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### Distribución Amarillas/Partido")
    fig_h = go.Figure(go.Histogram(
        x=filtered["Amarillas/Part."].dropna(), nbinsx=20,
        marker_color="#2EE6A6", opacity=0.75,
    ))
    fig_h.add_vline(x=4.5, line_dash="dash", line_color="#FF5A6E",
                    annotation_text="Over 4.5", annotation_font_color="#FF5A6E")
    fig_h.add_vline(x=3.0, line_dash="dash", line_color="#2EE6A6",
                    annotation_text="Under 3.0", annotation_font_color="#2EE6A6",
                    annotation_position="bottom right")
    fig_h.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b9ab0", size=10), height=220,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="rgba(255,255,255,.04)", title="Amarillas/Partido"),
        yaxis=dict(gridcolor="rgba(255,255,255,.04)", title="Árbitros"),
    )
    st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

    # ── Insights ────────────────────────────────────────────────────────────
    n_over  = int((filtered["Amarillas/Part."] >= 4.5).sum()) if "Amarillas/Part." in filtered.columns else 0
    n_under = int((filtered["Amarillas/Part."] <= 3.0).sum()) if "Amarillas/Part." in filtered.columns else 0

    st.info(
        f"💡 **Resumen disciplinario — {league_label} · {window_label}**\n\n"
        f"- **Árbitros con ≥4.5 am/p**: **{n_over}**. Perfil de alta intervención disciplinaria.\n"
        f"- **Árbitros con ≤3.0 am/p**: **{n_under}**. Perfil de menor intervención disciplinaria.\n"
        f"- Árbitros con >0.3 pen/p tienen mayor impacto en el resultado final.\n"
        f"- Fuente prioritaria: partidos actualizados por API-Football gratuita si hay clave; fallback CSV/manual cuando falte muestra."
    )

    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)
