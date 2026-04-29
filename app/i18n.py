"""
Internacionalización KICKDEX — Español / Inglés.
Uso: from app.i18n import t; t("key")
El idioma activo se guarda en st.session_state.lang
"""

import streamlit as st

DEFAULT_LANG = "es"

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Global / Nav ─────────────────────────────────────────────────────────
    "app_tagline": {
        "es": "Big Data · Comparadores · Player Scouting · 100% Gratuito",
        "en": "Big Data · Comparisons · Player Scouting · 100% Free",
    },
    "tab_inicio": {"es": "🏠 Inicio", "en": "🏠 Home"},
    "tab_comparador": {"es": "⚡ Comparador", "en": "⚡ Match Analysis"},
    "tab_h2h": {"es": "📚 H2H Histórico", "en": "📚 Head-to-Head"},
    "tab_jugadores": {"es": "⚽ Jugadores", "en": "⚽ Players"},
    "tab_arbitros": {"es": "⚖️ Árbitros", "en": "⚖️ Referees"},

    # ── Sidebar ──────────────────────────────────────────────────────────────
    "sidebar_tool": {
        "es": "Herramienta gratuita de Big Data futbolístico",
        "en": "Free football big data terminal",
    },
    "sidebar_db": {"es": "📚 Base de Datos", "en": "📚 Database"},
    "sidebar_matches": {"es": "partidos", "en": "matches"},
    "sidebar_leagues": {"es": "Ligas", "en": "Leagues"},
    "sidebar_season": {"es": "Temporada actual", "en": "Current season"},
    "sidebar_update": {"es": "🔄 Actualizar datos", "en": "🔄 Refresh data"},
    "sidebar_no_data": {
        "es": "Sin datos. Revisa la carpeta `datos/`.",
        "en": "No data. Check the `datos/` folder.",
    },

    # ── Landing ──────────────────────────────────────────────────────────────
    "landing_title": {
        "es": "La terminal de datos del fútbol",
        "en": "The football data terminal",
    },
    "landing_subtitle": {
        "es": "22 años de historia. 15.000+ partidos. Análisis profesional 100% gratuito.",
        "en": "22 years of history. 15,000+ matches. Pro-level analytics, 100% free.",
    },
    "landing_cta": {
        "es": "⚡ EMPEZAR A ANALIZAR",
        "en": "⚡ START ANALYZING",
    },
    "landing_f1_title": {"es": "📅 Calendario en Vivo", "en": "📅 Live Calendar"},
    "landing_f1_body": {
        "es": "Partidos de hoy, próxima jornada y resultados recientes agrupados por liga.",
        "en": "Today's matches, upcoming fixtures and recent results grouped by league.",
    },
    "landing_f2_title": {"es": "⚡ Análisis Pre-Partido", "en": "⚡ Pre-Match Analysis"},
    "landing_f2_body": {
        "es": "Forma reciente, H2H, Smart Alerts y probabilidades matemáticas para cualquier partido.",
        "en": "Recent form, H2H, Smart Alerts and mathematical probabilities for every match.",
    },
    "landing_f3_title": {"es": "📚 Historial Completo", "en": "📚 Full History"},
    "landing_f3_body": {
        "es": "Todos los enfrentamientos directos desde 2004 con resultados, goles y división.",
        "en": "Every head-to-head since 2004 with results, goals and division.",
    },
    "landing_f4_title": {"es": "⚽ Player Scouting", "en": "⚽ Player Scouting"},
    "landing_f4_body": {
        "es": "Estadísticas de cada jugador, rankings por equipo y análisis por métricas.",
        "en": "Per-player stats, team rankings and metric-based analysis.",
    },
    "landing_footer": {
        "es": "Uso educativo · Datos: football-data.co.uk + FBref",
        "en": "Educational use · Data: football-data.co.uk + FBref",
    },

    # ── Inicio ───────────────────────────────────────────────────────────────
    "inicio_title": {"es": "🏠 Calendario y Partidos", "en": "🏠 Calendar & Matches"},
    "inicio_subtitle": {
        "es": "Próximos partidos y resultados recientes. Pulsa «Analizar» para ver el análisis completo.",
        "en": "Upcoming matches and recent results. Click «Analyze» to get the full breakdown.",
    },
    "inicio_today": {"es": "📆 Partidos de Hoy", "en": "📆 Today's Matches"},
    "inicio_upcoming": {"es": "🗓️ Próxima Jornada", "en": "🗓️ Next Matchday"},
    "inicio_recent": {"es": "✅ Resultados Recientes", "en": "✅ Recent Results"},
    "inicio_no_upcoming": {
        "es": "Aún no hay fixtures publicados para la próxima jornada. Football-data.co.uk suele añadirlos 2-3 días antes. Mientras, puedes ver los resultados recientes o ir directamente al Comparador.",
        "en": "No fixtures published for the next matchday yet. Football-data.co.uk usually adds them 2-3 days before kick-off. Check recent results or jump straight to Match Analysis.",
    },
    "inicio_analyze": {"es": "⚡ Analizar", "en": "⚡ Analyze"},
    "inicio_refresh": {"es": "🔄 Actualizar Calendario", "en": "🔄 Refresh Calendar"},
    "inicio_filter_league": {"es": "Filtrar por liga", "en": "Filter by league"},
    "league_all": {"es": "Todas", "en": "All"},
    "league_sp1": {"es": "La Liga", "en": "La Liga"},
    "league_sp2": {"es": "Segunda", "en": "Segunda"},
    "time": {"es": "Hora", "en": "Time"},
    "home": {"es": "Local", "en": "Home"},
    "draw": {"es": "Empate", "en": "Draw"},
    "away": {"es": "Visitante", "en": "Away"},

    # ── Comparador ───────────────────────────────────────────────────────────
    "cmp_title": {"es": "⚡ Análisis Pre-Partido", "en": "⚡ Pre-Match Analysis"},
    "cmp_league": {"es": "Liga", "en": "League"},
    "cmp_home": {"es": "🏠 Equipo Local", "en": "🏠 Home Team"},
    "cmp_away": {"es": "✈️ Equipo Visitante", "en": "✈️ Away Team"},
    "cmp_last": {"es": "Últimos", "en": "Last"},
    "cmp_analyze": {"es": "📊 ANALIZAR PARTIDO", "en": "📊 ANALYZE MATCH"},
    "cmp_select_prompt": {
        "es": "⚽ Selecciona dos equipos y pulsa ANALIZAR",
        "en": "⚽ Pick two teams and click ANALYZE",
    },
    "cmp_no_data": {
        "es": "No hay suficientes datos recientes para uno o ambos equipos.",
        "en": "Not enough recent data for one or both teams.",
    },
    "cmp_wins": {"es": "G", "en": "W"},
    "cmp_draws": {"es": "E", "en": "D"},
    "cmp_losses": {"es": "P", "en": "L"},
    "cmp_last_home": {"es": "últimos {n} en casa", "en": "last {n} at home"},
    "cmp_last_away": {"es": "últimos {n} fuera", "en": "last {n} away"},
    "cmp_goals_match": {"es": "Goles/partido", "en": "Goals/match"},
    "cmp_shots_on": {"es": "Tiros a puerta", "en": "Shots on target"},
    "cmp_xg_proxy": {"es": "xG (proxy)", "en": "xG (proxy)"},
    "cmp_corners": {"es": "Córners", "en": "Corners"},
    "cmp_cards": {"es": "Tarjetas", "en": "Cards"},
    "cmp_over25": {"es": "Over 2.5 rate", "en": "Over 2.5 rate"},
    "cmp_radar": {"es": "📡 Comparativa Visual", "en": "📡 Visual Comparison"},
    "cmp_probs": {"es": "🎯 Probabilidades Matemáticas", "en": "🎯 Mathematical Probabilities"},
    "cmp_btts": {"es": "🔵 Ambos marcan", "en": "🔵 Both teams score"},
    "cmp_estimated_probs": {
        "es": "Probabilidades estimadas",
        "en": "Estimated probabilities",
    },
    "cmp_alerts": {"es": "🔔 Smart Alerts", "en": "🔔 Smart Alerts"},
    "cmp_no_alerts": {
        "es": "No se detectaron tendencias significativas para este partido.",
        "en": "No significant trends detected for this match.",
    },
    "cmp_h2h_header": {"es": "📚 Historial H2H ({n} enfrentamientos)", "en": "📚 H2H History ({n} matches)"},
    "cmp_h2h_wins_t1": {"es": "Victorias {team}", "en": "{team} wins"},
    "cmp_h2h_draws": {"es": "Empates", "en": "Draws"},
    "cmp_h2h_avg": {"es": "Media goles", "en": "Avg goals"},
    "cmp_players_title": {"es": "👥 Comparativa de Jugadores", "en": "👥 Player Comparison"},
    "cmp_players_none": {
        "es": "Sin datos de jugadores disponibles para este partido.",
        "en": "No player data available for this match.",
    },
    "cmp_players_top": {"es": "Top por tiros por partido (temporada actual)", "en": "Top by shots per match (current season)"},
    "player": {"es": "Jugador", "en": "Player"},
    "shots": {"es": "Tiros", "en": "Shots"},
    "shots_on": {"es": "A Puerta", "en": "On Target"},
    "goals": {"es": "Goles", "en": "Goals"},
    "assists": {"es": "Asistencias", "en": "Assists"},
    "matches": {"es": "PJ", "en": "MP"},

    # ── H2H ──────────────────────────────────────────────────────────────────
    "h2h_title": {"es": "📚 Historial de Enfrentamientos Directos", "en": "📚 Head-to-Head History"},
    "h2h_subtitle": {
        "es": "Base de datos histórica desde 2004 · Temporada actual: {season}",
        "en": "Historical database since 2004 · Current season: {season}",
    },
    "h2h_team1": {"es": "Equipo 1", "en": "Team 1"},
    "h2h_team2": {"es": "Equipo 2", "en": "Team 2"},
    "h2h_empty": {
        "es": "No hay enfrentamientos registrados entre **{t1}** y **{t2}**.",
        "en": "No recorded matches between **{t1}** and **{t2}**.",
    },
    "h2h_total": {"es": "Total partidos", "en": "Total matches"},
    "h2h_goals_chart": {
        "es": "Goles por partido (últimos 15 enfrentamientos)",
        "en": "Goals per match (last 15 meetings)",
    },
    "h2h_all": {"es": "Todos los enfrentamientos ({n})", "en": "All meetings ({n})"},
    "date": {"es": "Fecha", "en": "Date"},
    "result": {"es": "Resultado", "en": "Result"},
    "league": {"es": "Liga", "en": "League"},
}


def get_lang() -> str:
    """Devuelve el idioma activo desde session_state."""
    return st.session_state.get("lang", DEFAULT_LANG)


def set_lang(lang: str) -> None:
    """Cambia el idioma activo."""
    st.session_state.lang = lang if lang in ("es", "en") else DEFAULT_LANG


def t(key: str, **kwargs) -> str:
    """
    Devuelve la traducción de `key` en el idioma activo.
    Soporta placeholders: t("key", team="Real Madrid")
    """
    lang = get_lang()
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
