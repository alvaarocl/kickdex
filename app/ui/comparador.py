"""
Tab ⚡ Comparador de Partido Premium.
Replica exactamente el Fixture Header y Stat Duel de la web estática.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.engine.metrics import get_recent_form, get_h2h_summary
from app.engine.smart_alerts import generate_alerts
from app.engine.probability import calculate_probabilities
from app.ui.styles import result_tag, prob_bar_html, alert_card_html
from app.config import ROLLING_WINDOW_OPTIONS, ROLLING_WINDOW_DEFAULT
from app.i18n import t

def _fixture_header_html(home, away, h_stats, a_stats):
    h_win_rate = f"{int(h_stats.get('win_rate', 0)*100)}% casa"
    a_win_rate = f"{int(a_stats.get('win_rate', 0)*100)}% fuera"
    
    return f"""
    <div class="fixture-header">
        <div class="fixture-team">
            <div class="fixture-team-info">
                <div class="fixture-team-name">{home}</div>
                <div class="fixture-team-sub">{h_win_rate}</div>
            </div>
        </div>
        <div class="fixture-vs">
            <div class="fixture-vs-badge">VS</div>
            <div class="fixture-sub-text">KICKDEX</div>
        </div>
        <div class="fixture-team away">
            <div class="fixture-team-info">
                <div class="fixture-team-name">{away}</div>
                <div class="fixture-team-sub">{a_win_rate}</div>
            </div>
        </div>
    </div>"""

def _stat_duel_html(home, away, h, a):
    def _row(label, hv, av, max_val, dec=1, pct=False, invert=False):
        h_val = hv if hv is not None and not np.isnan(hv) else 0
        a_val = av if av is not None and not np.isnan(av) else 0
        h_bar = max(0, min((max_val - h_val)/max_val if invert else h_val/max_val, 1)) * 100
        a_bar = max(0, min((max_val - a_val)/max_val if invert else a_val/max_val, 1)) * 100
        h_disp = f"{int(h_val*100)}%" if pct else f"{h_val:.{dec}f}"
        a_disp = f"{int(a_val*100)}%" if pct else f"{a_val:.{dec}f}"
        h_leading = "leading" if (h_val < a_val if invert else h_val > a_val) else ""
        a_leading = "leading" if (a_val < h_val if invert else a_val > h_val) else ""
        
        return f"""
        <div class="duel-row">
            <div class="duel-val-home {h_leading}">{h_disp}</div>
            <div class="duel-track-home"><div class="duel-bar-home" style="width:{h_bar}%"></div></div>
            <div class="duel-label">{label}</div>
            <div class="duel-track-away"><div class="duel-bar-away" style="width:{a_bar}%"></div></div>
            <div class="duel-val-away {a_leading}">{a_disp}</div>
        </div>"""

    rows = [
        _row("Victorias", h.get('win_rate'), a.get('win_rate'), 1, pct=True),
        _row("Goles/p", h.get('avg_goals'), a.get('avg_goals'), 3),
        _row("Gc enc./p", h.get('avg_goals_against'), a.get('avg_goals_against'), 3, invert=True),
        _row("xG proxy", h.get('avg_xg_proxy'), a.get('avg_xg_proxy'), 2.5),
        _row("Tiros/p", h.get('avg_shots'), a.get('avg_shots'), 20),
        _row("SoT/p", h.get('avg_shots_on'), a.get('avg_shots_on'), 10),
        _row("Córners/p", h.get('avg_corners'), a.get('avg_corners'), 12),
        _row("Over 2.5", h.get('over25_rate'), a.get('over25_rate'), 1, pct=True),
        _row("BTTS", h.get('btts_rate'), a.get('btts_rate'), 1, pct=True),
    ]
    
    header = f"""
    <div class="duel-header">
        <div style="text-align:right; font-size:.62rem; color:var(--brand); font-weight:800;">{home.upper()}</div>
        <div></div><div></div><div></div>
        <div style="text-align:left; font-size:.62rem; color:#fb7185; font-weight:800;">{away.upper()}</div>
    </div>"""
    
    return f'<div class="card" style="margin-bottom:20px;"><div class="section-title">Comparativa de estadísticas</div>{header}<div class="stat-duel">{"".join(rows)}</div></div>'

def _radar_chart(home, away, h_stats, a_stats):
    categories = ["Goles", "Victorias", "Tiros", "xG", "Defensa"]
    
    def norm(v, m):
        if v is None or np.isnan(v): return 0
        return max(0, min(v/m, 1)) * 100
    
    h_def = max(0, 1 - (h_stats.get('avg_goals_against', 0) / 3))
    a_def = max(0, 1 - (a_stats.get('avg_goals_against', 0) / 3))

    h_vals = [norm(h_stats.get('avg_goals'), 3), norm(h_stats.get('win_rate'), 1), norm(h_stats.get('avg_shots'), 20), norm(h_stats.get('avg_xg_proxy'), 2.5), h_def * 100]
    a_vals = [norm(a_stats.get('avg_goals'), 3), norm(a_stats.get('win_rate'), 1), norm(a_stats.get('avg_shots'), 20), norm(a_stats.get('avg_xg_proxy'), 2.5), a_def * 100]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=h_vals, theta=categories, fill='toself', name=home, line_color='#2EE6A6', fillcolor='rgba(46,230,166,0.1)'))
    fig.add_trace(go.Scatterpolar(r=a_vals, theta=categories, fill='toself', name=away, line_color='#fb7185', fillcolor='rgba(251,113,133,0.1)'))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 100]), bgcolor='rgba(0,0,0,0)', gridcolor='rgba(255,255,255,0.05)'),
        showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#8b9ab0', size=10), margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig

def render(df, teams, df_players):
    st.markdown('<h2 class="section-h2">Comparador de Partido</h2>', unsafe_allow_html=True)
    
    # Pre-carga
    ph = st.session_state.get("cmp_preload_home", "Real Madrid")
    pa = st.session_state.get("cmp_preload_away", "Barcelona")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    home = col1.selectbox("Local", teams, index=teams.index(ph) if ph in teams else 0)
    away = col2.selectbox("Visitante", teams, index=teams.index(pa) if pa in teams else 1)
    window = col3.selectbox("Ventana", [6, 10, 20], index=1)

    h_stats = get_recent_form(df, home, venue="Home", n=window)
    a_stats = get_recent_form(df, away, venue="Away", n=window)
    h2h_sum = get_h2h_summary(df, home, away)

    if not h_stats or not a_stats:
        st.warning("Datos insuficientes")
        return

    # ── UI Premium ──
    st.markdown(_fixture_header_html(home, away, h_stats, a_stats), unsafe_allow_html=True)
    st.markdown(_stat_duel_html(home, away, h_stats, a_stats), unsafe_allow_html=True)

    # Probabilidades
    probs = calculate_probabilities(h_stats, a_stats, h2h_sum or None)
    st.markdown('<div class="card" style="margin-bottom:20px;"><div class="section-title">Probabilidades KICKDEX</div>', unsafe_allow_html=True)
    st.markdown(prob_bar_html(f"🏠 {home}", probs.home, "#2EE6A6"), unsafe_allow_html=True)
    st.markdown(prob_bar_html("⚖️ Empate", probs.draw, "#8b9ab0"), unsafe_allow_html=True)
    st.markdown(prob_bar_html(f"✈️ {away}", probs.away, "#fb7185"), unsafe_allow_html=True)
    st.markdown('<hr/>', unsafe_allow_html=True)
    st.markdown(prob_bar_html("⚽ Over 2.5", probs.over25, "#5BD6FF"), unsafe_allow_html=True)
    st.markdown(prob_bar_html("🤝 BTTS", probs.btts, "#a78bfa"), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Radar + Alertas
    c_radar, c_alerts = st.columns(2)
    with c_radar:
        st.markdown('<div class="chart-box" style="height:100%;"><div class="section-title">Radar Comparativo</div>', unsafe_allow_html=True)
        st.plotly_chart(_radar_chart(home, away, h_stats, a_stats), use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)
    
    with c_alerts:
        st.markdown('<div class="card" style="height:100%;"><div class="section-title">Alertas Inteligentes</div>', unsafe_allow_html=True)
        alerts = generate_alerts(h_stats, a_stats, h2h_sum or None)
        for a in alerts:
            st.markdown(alert_card_html(a.text, "#2EE6A6" if a.strength=="HIGH" else "#F5B93C"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla de Jugadores
    st.divider()
    st.markdown('<h4 class="players-col-title">Scouting de Jugadores Pro</h4>', unsafe_allow_html=True)
    
    h_p = df_players[df_players["team"] == home].groupby("player").mean(numeric_only=True).sort_values("gls", ascending=False).head(10)
    a_p = df_players[df_players["team"] == away].groupby("player").mean(numeric_only=True).sort_values("gls", ascending=False).head(10)
    
    col_ph, col_pa = st.columns(2)
    with col_ph:
        st.markdown(f'<div class="players-col-title">{home}</div>', unsafe_allow_html=True)
        st.dataframe(h_p[["gls", "ast", "sh", "sot"]], use_container_width=True)
    with col_pa:
        st.markdown(f'<div class="players-col-title">{away}</div>', unsafe_allow_html=True)
        st.dataframe(a_p[["gls", "ast", "sh", "sot"]], use_container_width=True)

    # ── Calculadora Maestra ──────────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="calc-title">🔍 KICKDEX Terminal — Calculadora Maestra</div>', unsafe_allow_html=True)

    with st.container():
        ccol1, ccol2, ccol3 = st.columns([3, 1, 1])
        q_team  = ccol1.selectbox("Equipo",     teams,                                  key="q_sql",   label_visibility="collapsed")
        q_venue = ccol2.selectbox("Campo",      ["Todos", "Local", "Visitante"],         key="q_venue", label_visibility="collapsed")
        q_n     = ccol3.selectbox("Últimos N",  [5, 10, 20, 38], index=1,               key="q_n",     label_visibility="collapsed")

        if st.button("⚡ EJECUTAR CÁLCULO PRO", key="calc_run"):
            from app.engine.query_engine import QueryEngine
            from app.data.database import SessionLocal
            db = SessionLocal()
            try:
                qe = QueryEngine(db)
                venue_map = {"Todos": "All", "Local": "Home", "Visitante": "Away"}
                res = qe.get_team_stats(q_team, venue=venue_map[q_venue], last_n=q_n)
                if res:
                    st.success(f"**{q_team}** — Últimos {res['n_matches']} partidos ({q_venue})")
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("Goles Marcados",  f"{res['avg_goals_scored']:.2f}")
                    mc2.metric("Goles Encajados", f"{res['avg_goals_conceded']:.2f}")
                    mc3.metric("Win Rate",        f"{res['win_pct']:.1f}%")
                    mc4.metric("Córners/p",       f"{res.get('avg_corners', 0):.1f}")

                    if res.get("raw_corners"):
                        import plotly.graph_objects as go
                        fig_c = go.Figure(go.Bar(
                            x=[f"P{i+1}" for i in range(len(res["raw_corners"]))],
                            y=res["raw_corners"], marker_color="#2EE6A6", opacity=0.7,
                        ))
                        fig_c.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#8b9ab0", size=10),
                            margin=dict(l=10, r=10, t=10, b=10), height=120,
                            yaxis=dict(gridcolor="rgba(255,255,255,.05)"),
                            xaxis=dict(gridcolor="rgba(255,255,255,.02)"),
                        )
                        st.markdown("**Córners por partido:**")
                        st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info(f"Sin datos SQL para **{q_team}**. Los datos SQL se populan al importar los CSVs a la base de datos.")
            except Exception as e:
                st.error(f"Error en cálculo: {e}")
            finally:
                db.close()
