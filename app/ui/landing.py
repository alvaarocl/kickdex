"""
Landing Page animada — hero con efectos CSS keyframe, scroll suave entre secciones.
"""

import streamlit as st
import streamlit.components.v1 as components

_LANDING_HTML = """
<div class="landing-root">
  <div class="landing-hero">
    <span class="landing-logo-text">KICKDEX</span>
    <div class="landing-tagline">La terminal de datos del fútbol</div>
    <div class="landing-sub">
      22 años de historia &nbsp;·&nbsp; +85.000 partidos &nbsp;·&nbsp;
      11 ligas &nbsp;·&nbsp; Análisis profesional 100% gratuito
    </div>
    <div class="landing-stats">
      <div class="landing-stat">
        <div class="landing-stat-num">85K+</div>
        <div class="landing-stat-label">Partidos</div>
      </div>
      <div class="landing-stat">
        <div class="landing-stat-num">191</div>
        <div class="landing-stat-label">Equipos</div>
      </div>
      <div class="landing-stat">
        <div class="landing-stat-num">11</div>
        <div class="landing-stat-label">Ligas</div>
      </div>
      <div class="landing-stat">
        <div class="landing-stat-num">22</div>
        <div class="landing-stat-label">Temporadas</div>
      </div>
    </div>
  </div>

  <div class="landing-features">
    <div class="landing-feat">
      <div class="landing-feat-icon">⚡</div>
      <div class="landing-feat-title">Comparador Pro</div>
      <div class="landing-feat-body">
        Enfrenta cualquier par de equipos con estadísticas reales, radar comparativo,
        probabilidades Poisson y alertas inteligentes generadas por IA.
      </div>
    </div>
    <div class="landing-feat">
      <div class="landing-feat-icon">📊</div>
      <div class="landing-feat-title">Datos y Tendencias</div>
      <div class="landing-feat-body">
        Consulta forma reciente, patrones H2H, volumen de goles y métricas
        comparables para estudiar cualquier enfrentamiento.
      </div>
    </div>
    <div class="landing-feat">
      <div class="landing-feat-icon">⚖️</div>
      <div class="landing-feat-title">Árbitros</div>
      <div class="landing-feat-body">
        Perfil disciplinario de cada colegiado: tarjetas, faltas y penaltis
        con ventanas temporales seleccionables y filtro por liga.
      </div>
    </div>
    <div class="landing-feat">
      <div class="landing-feat-icon">📚</div>
      <div class="landing-feat-title">H2H Histórico</div>
      <div class="landing-feat-body">
        Head-to-head completo desde 2004 con tendencias, promedios de goles
        y patrones de resultado para cualquier enfrentamiento.
      </div>
    </div>
    <div class="landing-feat">
      <div class="landing-feat-icon">⚽</div>
      <div class="landing-feat-title">Scouting de Jugadores</div>
      <div class="landing-feat-body">
        Estadísticas individuales: goles, asistencias, tiros, faltas y tarjetas
        para identificar talento y riesgo en cada equipo.
      </div>
    </div>
    <div class="landing-feat">
      <div class="landing-feat-icon">🏠</div>
      <div class="landing-feat-title">Calendario en Vivo</div>
      <div class="landing-feat-body">
        Fixtures, resultados recientes y próxima jornada organizados por liga
        para las competiciones cubiertas.
      </div>
    </div>
  </div>
</div>
"""

_SCROLL_JS = """
<script>
(function() {
  function bindSmoothScroll() {
    var doc = window.parent.document;
    var tabs = doc.querySelectorAll('[data-baseweb="tab"]');
    tabs.forEach(function(t) {
      if (t._kx) return; t._kx = true;
      t.addEventListener('click', function() {
        setTimeout(function() { window.parent.scrollTo({top:0,behavior:'smooth'}); }, 60);
      });
    });
  }
  [150, 500, 1000].forEach(function(d) { setTimeout(bindSmoothScroll, d); });
})();
</script>
"""


def render():
    st.markdown(_LANDING_HTML, unsafe_allow_html=True)

    # CTA centrado — usa columnas para centrar el botón
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button("⚡  EMPEZAR A ANALIZAR", use_container_width=True, key="landing_cta"):
            components.html(
                "<script>window.parent.scrollTo({top:0,behavior:'smooth'});</script>",
                height=0,
            )
            st.session_state.show_landing = False
            st.rerun()

    st.markdown(
        '<div class="landing-footer">'
        'KICKDEX &nbsp;·&nbsp; football-data.co.uk &nbsp;·&nbsp; FBref &nbsp;·&nbsp; '
        'Análisis estadístico informativo basado en datos históricos.'
        '</div>',
        unsafe_allow_html=True,
    )

    components.html(_SCROLL_JS, height=0)
