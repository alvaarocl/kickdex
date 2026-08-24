/**
 * app.js — Core: data loading, tab management, i18n, landing, shared utilities
 * KICKDEX — GitHub Pages static frontend
 */

"use strict";

// ── i18n ───────────────────────────────────────────────────────────────────
const I18N = {
  es: {
    tab_inicio: "Inicio", tab_comparador: "Comparador", tab_h2h: "H2H",
    tab_jugadores: "Jugadores", tab_arbitros: "Árbitros", tab_live: "Directo",
    arb_title: "Árbitros", arb_subtitle: "Perfil disciplinario histórico. Identifica árbitros con tendencia a sacar más o menos tarjetas.",
    league_all: "Todas", league_sp1: "La Liga", league_sp2: "Segunda",
    inicio_title: "Calendario y Partidos",
    inicio_subtitle: "Consulta toda la temporada por liga, jornada y mes. Pulsa «Analizar» para ver el análisis completo.",
    inicio_filter: "Filtrar por liga",
    inicio_view: "Vista",
    inicio_view_upcoming: "Próximos",
    inicio_view_full: "Temporada completa",
    inicio_view_results: "Resultados",
    inicio_round: "Jornada",
    inicio_round_all: "Todas las jornadas",
    inicio_month: "Mes",
    inicio_month_all: "Todos los meses",
    inicio_load_more: "Mostrar más partidos",
    inicio_upcoming: "Próxima jornada",
    inicio_today: "Partidos de hoy",
    inicio_recent: "Resultados recientes",
    inicio_no_upcoming: "Aún no hay fixtures publicados para la próxima jornada. Football-data.co.uk los añade 2-3 días antes. Mientras, puedes analizar cualquier partido desde el Comparador.",
    inicio_analyze: "Analizar",
    loading: "Cargando partidos...",
    cmp_league: "Liga", cmp_home: "Equipo Local", cmp_away: "Equipo Visitante",
    cmp_last: "Ventana", cmp_analyze: "Analizar",
    cmp_prompt: "1. Selecciona liga · 2. Selecciona dos equipos · 3. Pulsa Analizar",
    cmp_players_title: "Comparativa de Jugadores",
    cmp_players_none: "Sin datos de jugadores para este partido",
    h2h_team1: "Equipo 1", h2h_team2: "Equipo 2", h2h_run: "Ver H2H",
    h2h_prompt: "Selecciona dos equipos para ver su historial",
    jug_team: "Equipo", jug_player: "Jugador", jug_run: "Ver Stats",
    jug_prompt: "Selecciona un equipo para ver las estadísticas de sus jugadores",
    landing_title: "La terminal de datos del fútbol",
    landing_subtitle: "22 años de historia. 15.000+ partidos. Análisis profesional 100% gratuito.",
    landing_cta: "⚡ EMPEZAR A ANALIZAR",
    landing_f1_title: "Calendario multiliga",
    landing_f1_body: "Temporada completa, próximos partidos y resultados agrupados por liga, jornada y mes.",
    landing_f2_title: "Análisis Pre-Partido",
    landing_f2_body: "Forma reciente, H2H, Smart Alerts y probabilidades Poisson para cualquier partido.",
    landing_f3_title: "Historial Completo",
    landing_f3_body: "Todos los enfrentamientos directos desde 2004 con resultados, goles y división.",
    landing_f4_title: "Player Scouting",
    landing_f4_body: "Stats individuales por temporada cuando la cobertura del feed lo permite. Consulta /coverage.",
    landing_footer: "Uso educativo · Datos: football-data.co.uk + FBref",
    disclaimer: "Esta herramienta es exclusivamente informativa. Las probabilidades son estimaciones matemáticas basadas en datos históricos.",
    home: "Local", draw: "Empate", away: "Visitante",
    player: "Jugador", shots: "Tiros", shots_on: "A Puerta",
    goals: "Goles", assists: "Asist.", matches: "PJ",

    // ── V3 brand landing ───────────────────────────────
    nav_features: "Características",
    nav_leagues: "Ligas",
    nav_how: "Methodology",
    hero_h1_a: "Football intelligence,",
    hero_h1_b: "indexed.",
    hero_sub: "Indexamos cada partido, cada jugador y cada cuota en una sola terminal. Si hay edge, lo ves en verde. Si hay riesgo, lo ves en rojo. El resto es ruido.",
    hero_promise: "Gratis. Independiente. Matemático.",
    hero_cta_secondary: "Read methodology",
    hero_stat_1: "partidos históricos",
    hero_stat_2: "temporadas de datos",
    hero_stat_3: "ligas europeas",
    hero_stat_4: "coste siempre",
    hero_scroll: "Descubre más",
    edge_card_match_caption: "Real Madrid · ML · Bet365 1.92",
    edge_card_prob_model: "Prob. modelo",
    edge_card_prob_implied: "Prob. implícita",
    edge_card_form_home: "Forma local",
    edge_card_sample: "Muestra",
    leagues_eyebrow: "Cobertura multiliga",
    leagues_h2: "11 ligas europeas indexadas",
    features_eyebrow: "Todo en una herramienta",
    features_h2: "Análisis profesional, gratis",
    features_sub: "Las mismas herramientas que usan los analistas deportivos, sin pagar nada.",
    feat_calendar_title: "Calendario multiliga",
    feat_calendar_desc: "Calendario de temporada con filtros de liga, jornada y mes. Un clic para analizar cualquier fixture cubierto.",
    feat_calendar_tag: "Actualizado diariamente",
    feat_trends_title: "Tendencias",
    feat_trends_desc: "Compara forma reciente, H2H y probabilidades Poisson para estudiar cada enfrentamiento con contexto histórico.",
    feat_trends_tag: "Datos históricos y modelo Poisson",
    feat_h2h_title: "H2H Histórico",
    feat_h2h_desc: "Todos los enfrentamientos directos desde 2004. Estadísticas, datos y división de cada partido.",
    feat_compare_title: "Comparador de Equipos",
    feat_compare_desc: "Forma reciente, tiros, goles, córners y tarjetas lado a lado. Ventanas de 6, 10 o 20 partidos.",
    feat_scout_title: "Player Scouting",
    feat_scout_desc: "Stats por jugador (goles, asistencias, tiros, minutos) según cobertura del feed. Ligas no cubiertas marcadas.",
    feat_ref_title: "Perfil de Árbitros",
    feat_ref_desc: "Historial disciplinario de árbitros: amarillas, rojas y faltas por partido, con ventanas recientes cuando hay datos actualizados.",
    how_eyebrow: "Simple y directo",
    how_h2: "Cómo funciona",
    how_s1_t: "Elige liga y equipos",
    how_s1_d: "Selecciona cualquiera de las 11 ligas europeas y los dos equipos del partido que quieres analizar.",
    how_s2_t: "Obtén el análisis completo",
    how_s2_d: "Forma reciente, H2H, probabilidades Poisson, smart alerts y comparativa de jugadores en segundos.",
    how_s3_t: "Analiza el contexto real",
    how_s3_d: "Cruza probabilidades, forma reciente e histórico para detectar tendencias estadísticas relevantes.",
    trust_1: "Sin registro ni cuenta",
    trust_2: "Datos de football-data.co.uk + FBref",
    trust_3: "Uso exclusivamente educativo",
    trust_4: "Modelo matemático Poisson bivariante",
    final_h2: "Read the match before it's played.",
    final_sub: "Sin login. Sin ads. Sin picks.",
    footer_data: "Datos:",
    footer_legal: "Aviso legal",
    footer_privacy: "Privacidad",
    footer_terms: "Términos",
    footer_methodology: "Metodología",
    footer_coverage: "Cobertura",
    footer_feedback: "Reportar / sugerir",
    coverage_strip: "Cobertura: ",
    coverage_strip_updated: "Actualizado",
    cmp_promptTitle: "",
  },
  en: {
    tab_inicio: "Home", tab_comparador: "Match Analysis", tab_h2h: "H2H",
    tab_jugadores: "Players", tab_arbitros: "Referees", tab_live: "Live",
    arb_title: "Referees", arb_subtitle: "Historical disciplinary profile. Identify referees with a tendency to show more or fewer cards.",
    league_all: "All", league_sp1: "La Liga", league_sp2: "Segunda",
    inicio_title: "Calendar & Matches",
    inicio_subtitle: "Browse the full season by league, matchday and month. Click «Analyze» for the full breakdown.",
    inicio_filter: "Filter by league",
    inicio_view: "View",
    inicio_view_upcoming: "Upcoming",
    inicio_view_full: "Full season",
    inicio_view_results: "Results",
    inicio_round: "Matchday",
    inicio_round_all: "All matchdays",
    inicio_month: "Month",
    inicio_month_all: "All months",
    inicio_load_more: "Show more matches",
    inicio_upcoming: "Next matchday",
    inicio_today: "Today's matches",
    inicio_recent: "Recent results",
    inicio_no_upcoming: "No fixtures published for the next matchday yet. Football-data.co.uk adds them 2-3 days before kick-off. In the meantime, analyze any match in the Match Analysis tab.",
    inicio_analyze: "Analyze",
    loading: "Loading matches...",
    cmp_league: "League", cmp_home: "Home Team", cmp_away: "Away Team",
    cmp_last: "Window", cmp_analyze: "Analyze",
    cmp_prompt: "1. Pick league · 2. Select two teams · 3. Click Analyze",
    cmp_players_title: "Player Comparison",
    cmp_players_none: "No player data available for this match",
    h2h_team1: "Team 1", h2h_team2: "Team 2", h2h_run: "See H2H",
    h2h_prompt: "Select two teams to see their head-to-head history",
    jug_team: "Team", jug_player: "Player", jug_run: "See Stats",
    jug_prompt: "Select a team to view player statistics",
    landing_title: "The football data terminal",
    landing_subtitle: "22 years of history. 15,000+ matches. Pro-level analytics, 100% free.",
    landing_cta: "⚡ START ANALYZING",
    landing_f1_title: "Multi-league calendar",
    landing_f1_body: "Full season, upcoming fixtures and results grouped by league, matchday and month.",
    landing_f2_title: "Pre-Match Analysis",
    landing_f2_body: "Recent form, H2H, Smart Alerts and Poisson probabilities for every match.",
    landing_f3_title: "Full History",
    landing_f3_body: "Every head-to-head since 2004 with results, goals and division.",
    landing_f4_title: "Player Scouting",
    landing_f4_body: "Per-player season stats where feed coverage allows. See /coverage.",
    landing_footer: "Educational use · Data: football-data.co.uk + FBref",
    disclaimer: "This tool is for informational purposes only. Probabilities are mathematical estimates based on historical data.",
    home: "Home", draw: "Draw", away: "Away",
    player: "Player", shots: "Shots", shots_on: "On Target",
    goals: "Goals", assists: "Assists", matches: "MP",

    // ── V3 brand landing ───────────────────────────────
    nav_features: "Features",
    nav_leagues: "Leagues",
    nav_how: "Methodology",
    hero_h1_a: "Football intelligence,",
    hero_h1_b: "indexed.",
    hero_sub: "We index every match, every player and every odds line into a single terminal. If there's edge, you see it in green. If there's risk, you see it in red. The rest is noise.",
    hero_promise: "Free. Independent. Math-first.",
    hero_cta_secondary: "Read methodology",
    hero_stat_1: "historical matches",
    hero_stat_2: "seasons of data",
    hero_stat_3: "european leagues",
    hero_stat_4: "cost, always",
    hero_scroll: "Discover more",
    edge_card_match_caption: "Real Madrid · ML · Bet365 1.92",
    edge_card_prob_model: "Model prob.",
    edge_card_prob_implied: "Implied prob.",
    edge_card_form_home: "Home form",
    edge_card_sample: "Sample",
    leagues_eyebrow: "Multi-league coverage",
    leagues_h2: "11 European leagues indexed",
    features_eyebrow: "Everything in one tool",
    features_h2: "Pro-level analytics, free",
    features_sub: "The same tools sports analysts use, without paying a cent.",
    feat_calendar_title: "Multi-league calendar",
    feat_calendar_desc: "Season calendar with league, matchday and month filters. Analyze any covered fixture in one click.",
    feat_calendar_tag: "Updated daily",
    feat_trends_title: "Trends",
    feat_trends_desc: "Compare recent form, H2H and Poisson probabilities to study every match with historical context.",
    feat_trends_tag: "Historical data + Poisson model",
    feat_h2h_title: "Historical H2H",
    feat_h2h_desc: "Every head-to-head since 2004. Stats, data and division for every match.",
    feat_compare_title: "Team Comparator",
    feat_compare_desc: "Recent form, shots, goals, corners and cards side by side. Windows of 6, 10 or 20 matches.",
    feat_scout_title: "Player Scouting",
    feat_scout_desc: "Per-player stats (goals, assists, shots, minutes) where feed coverage allows. Uncovered leagues are flagged.",
    feat_ref_title: "Referee Profile",
    feat_ref_desc: "Historical disciplinary record: yellows, reds and fouls per match, with recent windows when data is fresh.",
    how_eyebrow: "Simple and direct",
    how_h2: "How it works",
    how_s1_t: "Pick league and teams",
    how_s1_d: "Choose any of the 11 European leagues and the two teams of the match you want to analyze.",
    how_s2_t: "Get the full analysis",
    how_s2_d: "Recent form, H2H, Poisson probabilities, smart alerts and player comparison in seconds.",
    how_s3_t: "Read the real context",
    how_s3_d: "Cross probabilities, recent form and history to detect relevant statistical trends.",
    trust_1: "No signup, no account",
    trust_2: "Data from football-data.co.uk + FBref",
    trust_3: "For educational use only",
    trust_4: "Bivariate Poisson math model",
    final_h2: "Read the match before it's played.",
    final_sub: "No login. No ads. No picks.",
    footer_data: "Data:",
    footer_legal: "Legal notice",
    footer_privacy: "Privacy",
    footer_terms: "Terms",
    footer_methodology: "Methodology",
    footer_coverage: "Coverage",
    footer_feedback: "Report / suggest",
    coverage_strip: "Coverage: ",
    coverage_strip_updated: "Updated",
    cmp_promptTitle: "",
  },
};

let LANG = localStorage.getItem("kdx_lang") || "es";

function t(key) {
  return (I18N[LANG] || I18N.es)[key] || key;
}

function toggleLang() {
  LANG = LANG === "es" ? "en" : "es";
  localStorage.setItem("kdx_lang", LANG);
  applyI18n();
  const label = LANG === "es" ? "🇪🇸 ES" : "🇬🇧 EN";
  document.querySelectorAll("#langToggle, #langToggleLp").forEach(b => { b.textContent = label; });
  if (APP.loaded && typeof renderInicio === "function") renderInicio();
  if (APP.loaded && typeof updateCoverageStrip === "function") updateCoverageStrip();
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (el.tagName === "INPUT") { el.placeholder = t(key); return; }
    el.textContent = t(key);
  });
  document.documentElement.lang = LANG === "en" ? "en" : "es";

  // Keep both lang toggle buttons in sync
  const label = LANG === "es" ? "🇪🇸 ES" : "🇬🇧 EN";
  document.querySelectorAll("#langToggle, #langToggleLp").forEach(b => { b.textContent = label; });

  // Localized meta description
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) {
    metaDesc.setAttribute("content",
      LANG === "es"
        ? "La terminal de inteligencia futbolística. Edges en verde, riesgo en rojo, el resto es ruido. Gratis. Independiente. Matemático."
        : "The football intelligence terminal. Edges in green, risk in red, the rest is noise. Free. Independent. Math-first."
    );
  }
}

// ── Landing ────────────────────────────────────────────────────────────────
function animateCounters() {
  document.querySelectorAll(".lp-overlay [data-counter], .landing-overlay [data-counter]").forEach(el => {
    const target  = parseInt(el.dataset.counter, 10);
    const suffix  = el.dataset.suffix  || "";
    const abbrev  = el.dataset.abbrev === "true";
    const dur     = 1400;
    const start   = performance.now();

    function step(now) {
      const t   = Math.min((now - start) / dur, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      const val  = Math.round(ease * target);
      let display;
      if (abbrev && val >= 1000) {
        display = (val / 1000).toFixed(val >= 10000 ? 0 : 1) + "k";
      } else {
        display = val.toLocaleString("es-ES");
      }
      el.textContent = display + (t >= 1 ? suffix : "");
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
}

function activateLandingCards() {
  document.querySelectorAll(".landing-card").forEach(c => c.classList.add("visible"));
}

function closeLanding() {
  const landing = document.getElementById("landing-overlay");
  if (landing) {
    landing.style.opacity = "0";
    landing.style.transition = "opacity .25s ease";
    setTimeout(() => { landing.style.display = "none"; landing.style.opacity = ""; }, 260);
  }
  localStorage.setItem("kdx_seen", "1");
}

function _restartHeroAnims(landing) {
  const sel = ".lp-hero-content,.lp-badge,.lp-h1,.lp-hero-sub,.lp-hero-actions,.lp-hero-stats,.lp-hero-visual";
  landing.querySelectorAll(sel).forEach(el => {
    el.style.animation = "none";
    void el.offsetWidth; // force reflow
    el.style.animation = "";
  });
}

function openLanding() {
  const landing = document.getElementById("landing-overlay");
  if (!landing) return;
  landing.style.display = "block";
  landing.scrollTop = 0;
  void landing.offsetWidth; // force reflow so CSS animations restart
  _restartHeroAnims(landing);
  setTimeout(() => {
    animateCounters();
    if (typeof initLandingAnimations === "function") initLandingAnimations();
  }, 100);
}

function initLanding() {
  const landing = document.getElementById("landing-overlay");
  if (landing) {
    landing.style.display = "block";
    void landing.offsetWidth; // force reflow so CSS animations restart
    _restartHeroAnims(landing);
    setTimeout(() => {
      animateCounters();
      if (typeof initLandingAnimations === "function") initLandingAnimations();
    }, 200);
  }
  // All CTA buttons that close the landing
  ["landing-start", "lp-enter-nav", "lp-final-cta"].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.addEventListener("click", closeLanding);
  });
  // Logo re-opens landing
  const logo = document.querySelector(".logo");
  if (logo) logo.addEventListener("click", openLanding);
}

// ── State ──────────────────────────────────────────────────────────────────
const APP = {
  teams:       [],
  leagues:     {},
  fixtures:    { recent: [], upcoming: [], calendar: [] },
  teamStats:   {},
  h2h:         {},
  players:     {},
  playersDetail: {},
  playerCoverage: {},
  dataStatus:   {},
  dataHealth:   {},
  teamAssets:   { teams: {} },
  playerAssets: { players: {} },
  referees:    [],
  edges:       { items: [], top: null, stats: {} },
  meta:        {},
  loaded:      false,
};

const LEAGUE_META = {
  SP1: { country: "España", tier: 1 },
  SP2: { country: "España", tier: 2 },
  E0:  { country: "Inglaterra", tier: 1 },
  E1:  { country: "Inglaterra", tier: 2 },
  I1:  { country: "Italia", tier: 1 },
  I2:  { country: "Italia", tier: 2 },
  D1:  { country: "Alemania", tier: 1 },
  D2:  { country: "Alemania", tier: 2 },
  F1:  { country: "Francia", tier: 1 },
  F2:  { country: "Francia", tier: 2 },
  N1:  { country: "Países Bajos", tier: 1 },
};

const LEAGUE_COUNTRY_ORDER = [
  "España",
  "Inglaterra",
  "Italia",
  "Alemania",
  "Francia",
  "Países Bajos",
];

function getLeagueMeta(code) {
  return LEAGUE_META[code] || { country: "Otras", tier: 99 };
}

function compareLeagueCodes(a, b) {
  const ma = getLeagueMeta(a);
  const mb = getLeagueMeta(b);
  const ca = LEAGUE_COUNTRY_ORDER.indexOf(ma.country);
  const cb = LEAGUE_COUNTRY_ORDER.indexOf(mb.country);
  const oa = ca === -1 ? LEAGUE_COUNTRY_ORDER.length : ca;
  const ob = cb === -1 ? LEAGUE_COUNTRY_ORDER.length : cb;
  if (oa !== ob) return oa - ob;
  if (ma.tier !== mb.tier) return ma.tier - mb.tier;
  const na = APP.leagues?.[a]?.name || a;
  const nb = APP.leagues?.[b]?.name || b;
  return na.localeCompare(nb, "es", { sensitivity: "base" });
}

function sortLeagueCodes(codes) {
  return Array.from(new Set(codes.filter(Boolean))).sort(compareLeagueCodes);
}

function getLeagueLabel(code) {
  const name = APP.leagues?.[code]?.name || code;
  const meta = getLeagueMeta(code);
  if (!meta.country || meta.country === "Otras") return name;
  return `${meta.country} · ${meta.tier} · ${name}`;
}

function appendLeagueOption(sel, code) {
  const ld = APP.leagues?.[code];
  if (!sel || !ld) return;
  const opt = document.createElement("option");
  const meta = getLeagueMeta(code);
  opt.value = code;
  opt.textContent = getLeagueLabel(code);
  if (ld.roster_status === "partial") opt.textContent += " · cobertura parcial";
  opt.title = meta.country === "Otras" ? `${code} · ${ld.name}` : `${code} · ${meta.country} · ${ld.name}`;
  sel.appendChild(opt);
}

// ── Data fetching ──────────────────────────────────────────────────────────
const DATA_BASE = "./data/";
// Cache-bust: reuses the asset version embedded in index.html script tags so any
// bump in index.html also refreshes the JSON data files.
const _DATA_VERSION = (() => {
  const s = document.querySelector('script[src*="app.js?v="]');
  const m = s && s.src.match(/v=([^&]+)/);
  return m ? m[1] : Date.now().toString();
})();

async function fetchJSON(file) {
  const sep = file.includes("?") ? "&" : "?";
  const res = await fetch(DATA_BASE + file + sep + "v=" + _DATA_VERSION);
  if (!res.ok) throw new Error(`HTTP ${res.status} loading ${file}`);
  return res.json();
}

function initialsFor(value) {
  return String(value || "KD").trim().split(/\s+/).slice(0, 2).map(part => part[0] || "").join("").toUpperCase();
}

function teamAsset(name) {
  return APP.teamAssets?.teams?.[name] || { name, initials: initialsFor(name) };
}

function playerAsset(team, name) {
  return APP.playerAssets?.players?.[team + "::" + name] || { name, team, initials: initialsFor(name) };
}

function entityMedia(kind, name, team = "", extraClass = "") {
  const asset = kind === "player" ? playerAsset(team, name) : teamAsset(name);
  const src = asset.photo_local || asset.photo || asset.crest_local || asset.crest;
  const initials = asset.initials || initialsFor(name);
  const cls = kind === "player" ? "entity-media entity-media--player" : "entity-media entity-media--team";
  if (!src) return '<span class="' + cls + " " + extraClass + '" aria-hidden="true">' + escHtml(initials) + "</span>";
  return '<span class="' + cls + " " + extraClass + '"><img src="' + escHtml(src) + '" alt="" loading="lazy" onerror="this.parentElement.classList.add(\'is-fallback\');this.remove()"><i>' + escHtml(initials) + "</i></span>";
}

function formatPercent(value, decimals = 1) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "—";
  return `${(num * 100).toFixed(decimals)}%`;
}

function formatEdgePercent(value, decimals = 1) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "—";
  return `${num > 0 ? "+" : ""}${num.toFixed(decimals)}%`;
}

function matchEdgeKey(item) {
  return [
    String(item?.league || ""),
    String(item?.date || ""),
    String(item?.home || ""),
    String(item?.away || ""),
  ].join("|").toLowerCase();
}

function getFixtureEdges(fixture) {
  const key = matchEdgeKey(fixture);
  return (APP.edges?.items || []).filter(edge => matchEdgeKey(edge) === key);
}

function updateLandingMetrics() {
  const total = Number(APP.meta?.total_matches);
  const first = document.querySelector(".lp-stat-num[data-counter]");
  if (first && Number.isFinite(total) && total > 0) {
    first.dataset.counter = String(total);
    first.textContent = total >= 1000 ? `${Math.round(total / 1000)}k+` : `${total}+`;
  }
}

function updateCoverageStrip() {
  const el = document.getElementById("coverageStrip");
  if (!el) return;

  const status = APP.dataStatus || {};
  const players = status.players || {};
  const updated = status.updated_at;
  const totalMatches = APP.meta?.total_matches;
  const upcomingCount = (APP.fixtures?.upcoming || []).length;
  const playerLeagues = (players.covered_leagues || []).length;
  const refereeCount = Array.isArray(APP.referees) ? APP.referees.length : 0;

  const parts = [];
  if (totalMatches) parts.push(`<strong>${(totalMatches / 1000).toFixed(0)}k</strong> partidos`);
  if (upcomingCount) parts.push(`<strong>${upcomingCount}</strong> próximos`);
  if (playerLeagues) parts.push(`<strong>${playerLeagues}</strong> ligas con jugadores`);
  if (refereeCount) parts.push(`<strong>${refereeCount}</strong> árbitros`);

  if (!parts.length) { el.hidden = true; return; }

  const sep = '<span class="coverage-strip__sep"></span>';
  const updatedLabel = updated
    ? `${t("coverage_strip_updated")} ${new Date(updated).toLocaleDateString(LANG === "en" ? "en-GB" : "es-ES", { day: "2-digit", month: "short" })}`
    : "";

  el.innerHTML = parts.join(sep) + (updatedLabel ? `${sep}${updatedLabel}` : "")
    + `${sep}<a href="coverage.html">${t("footer_coverage") || "Coverage"} →</a>`;
  el.hidden = false;
}

function updateHeroEdge() {
  const target = document.getElementById("hero-edge");
  if (!target) return;

  const edge = APP.edges?.top || (APP.edges?.items || [])[0];
  const statusEl = document.getElementById("hero-edge-status");
  const matchEl = document.getElementById("hero-edge-match");
  const probEl = document.getElementById("hero-edge-prob");
  const impliedEl = document.getElementById("hero-edge-implied");
  const sampleEl = document.getElementById("hero-edge-sample");

  if (!edge) {
    if (statusEl) statusEl.textContent = "data · sin cuotas";
    if (matchEl) matchEl.innerHTML = "Sin edges <em>con</em> cuotas";
    if (probEl) probEl.textContent = "—";
    if (impliedEl) impliedEl.textContent = "—";
    if (sampleEl) sampleEl.textContent = "0 evaluados";
    if (window.KDXEdge?.renderEdgeNumber) {
      window.KDXEdge.renderEdgeNumber(target, {
        value: 0,
        label: "EDGE",
        caption: "Sin cuotas Bet365 disponibles en el feed actual",
        size: "xxl",
        tone: "neutral",
      });
    }
    return;
  }

  const isLive = edge.status === "upcoming";
  const sourceLabel = isLive ? "live · Bet365" : "histórico · Bet365";
  const matchLabel = `${edge.home || "Local"} <em>vs</em> ${edge.away || "Visitante"}`;
  const caption = `${edge.selection || edge.market_label} · ${edge.market_label || "1X2"} · Bet365 ${edge.odds || "—"}`;

  if (statusEl) statusEl.textContent = sourceLabel;
  if (matchEl) matchEl.innerHTML = matchLabel;
  if (probEl) probEl.textContent = formatPercent(edge.probability);
  if (impliedEl) impliedEl.textContent = formatPercent(edge.implied_probability);
  if (sampleEl) {
    const hm = edge.model?.home_matches || 0;
    const am = edge.model?.away_matches || 0;
    sampleEl.textContent = `${Math.min(hm, am)} partidos`;
  }

  if (window.KDXEdge?.renderEdgeNumber) {
    window.KDXEdge.renderEdgeNumber(target, {
      value: Number(edge.edge_pct),
      label: "EDGE",
      caption,
      size: "xxl",
      tone: Number(edge.edge_pct) >= 0 ? "value" : "risk",
    });
  } else {
    target.dataset.edge = String(edge.edge_pct || 0);
    target.dataset.edgeCaption = caption;
    target.dataset.edgeTone = Number(edge.edge_pct) >= 0 ? "value" : "risk";
  }
}

async function loadAllData() {
  const metaEl = document.getElementById("metaInfo");
  if (metaEl) metaEl.innerHTML = `<span class="spinner"></span> Cargando datos...`;

  try {
    // Critical path: everything except H2H (4.4MB) which loads in background
    const [meta, teams, teamStats, players, playersDetail, playerCoverage, dataStatus, dataHealth, leagues, fixtures, referees, edges, teamAssets, playerAssets] = await Promise.all([
      fetchJSON("meta.json"),
      fetchJSON("teams.json"),
      fetchJSON("team_stats.json"),
      fetchJSON("players.json").catch(() => ({})),
      fetchJSON("players_detail.json").catch(() => ({})),
      fetchJSON("player_coverage.json").catch(() => ({})),
      fetchJSON("data_status.json").catch(() => ({})),
      fetchJSON("data_health.json").catch(() => ({})),
      fetchJSON("leagues.json").catch(() => ({})),
      fetchJSON("fixtures.json").catch(() => ({ recent: [], upcoming: [] })),
      fetchJSON("referees.json").catch(() => []),
      fetchJSON("edges.json").catch(() => ({ items: [], top: null, stats: {} })),
      fetchJSON("team_assets.json").catch(() => ({ teams: {} })),
      fetchJSON("player_assets.json").catch(() => ({ players: {} })),
    ]);

    APP.meta           = meta;
    APP.teams          = teams;
    APP.teamStats      = teamStats;
    APP.h2h            = {};
    APP.h2hReady       = false;
    APP.players        = players;
    APP.playersDetail  = playersDetail;
    APP.playerCoverage = playerCoverage;
    APP.dataStatus     = dataStatus;
    APP.dataHealth     = dataHealth;
    APP.leagues        = leagues;
    APP.fixtures       = fixtures;
    APP.referees       = referees;
    APP.edges          = edges;
    APP.teamAssets     = teamAssets;
    APP.playerAssets   = playerAssets;
    APP.loaded         = true;

    updateHeader();
    updateLandingMetrics();
    updateHeroEdge();
    updateCoverageStrip();
    populateAllSelects();
    initSegControls();
    initModules();
    initGlobalSearch();
    updateLivePanel();
    applyRouteParams();

    // Background-load H2H (heavy 4.4MB file). Does not block initial render.
    fetchJSON("h2h.json")
      .then(h2h => {
        APP.h2h = h2h || {};
        APP.h2hReady = true;
        document.dispatchEvent(new CustomEvent("kdx:h2h-ready"));
      })
      .catch(err => {
        console.warn("H2H load failed:", err);
        APP.h2hReady = true; // Don't block forever
      });

  } catch (err) {
    console.error("Error loading data:", err);
    if (metaEl) {
      metaEl.textContent = "Error al cargar datos";
      metaEl.style.color = "var(--red)";
    }
  }
}

function updateHeader() {
  const m = APP.meta;
  const badge = document.getElementById("seasonBadge");
  if (badge) badge.textContent = m.season || "2026/27";
  const upd = m.updated_at ? new Date(m.updated_at).toLocaleDateString("es-ES") : "—";
  const info = document.getElementById("metaInfo");
  if (info) info.textContent = `${(m.total_matches || 0).toLocaleString()} partidos · actualizado ${upd}`;
}

function getTeamsByLeague(leagueCode) {
  if (!leagueCode || leagueCode === "all") return APP.teams;
  const ld = APP.leagues[leagueCode];
  return ld ? (ld.teams || []) : [];
}

function getPlayerLeagueCodes() {
  const byLeague = APP.playerCoverage?.by_league || {};
  const codes = Object.keys(byLeague).filter(code => (byLeague[code]?.player_rows || 0) > 0);
  if (codes.length) return sortLeagueCodes(codes);

  const playerTeams = new Set(Object.keys(APP.playersDetail || APP.players || {}));
  const fallbackCodes = Object.entries(APP.leagues || {})
    .filter(([, data]) => (data.teams || []).some(team => playerTeams.has(team)))
    .map(([code]) => code);
  return sortLeagueCodes(fallbackCodes);
}

function getPlayerTeamsByLeague(leagueCode) {
  const playerTeams = new Set(Object.keys(APP.playersDetail || APP.players || {}));
  if (!leagueCode || leagueCode === "all") return Array.from(playerTeams).sort();
  const teams = APP.leagues?.[leagueCode]?.teams || [];
  return teams.filter(team => playerTeams.has(team));
}

function populateSelect(id, teams) {
  const sel = document.getElementById(id);
  if (!sel) return;
  const prev = sel.value;
  while (sel.options.length > 1) sel.remove(1);
  teams.forEach(tm => {
    const opt = document.createElement("option");
    opt.value = tm; opt.textContent = tm;
    sel.appendChild(opt);
  });
  if (prev && [...sel.options].some(o => o.value === prev)) sel.value = prev;
}

function populateAllSelects() {
  const cmpTeams = getTeamsByLeague("all");
  ["cmp-home","cmp-away"].forEach(id => populateSelect(id, cmpTeams));
  // Jugadores: solo mostrar equipos con datos de jugadores reales
  populateSelect("jug-team", getPlayerTeamsByLeague("all"));
}

function initSegControls() {
  const populateLeagueSelect = (id) => {
    const sel = document.getElementById(id);
    if (!sel || sel.tagName !== "SELECT") return;
    const prev = sel.value;
    // Idempotent: keep only the first default option ("Todas"), remove the rest
    while (sel.options.length > 1) sel.remove(1);
    sortLeagueCodes(Object.keys(APP.leagues || {})).forEach(code => appendLeagueOption(sel, code));
    if ([...sel.options].some(opt => opt.value === prev)) sel.value = prev;
  };

  populateLeagueSelect("cmpLeagueFilter");
  const jugLeagueFilter = document.getElementById("jugLeagueFilter");
  if (jugLeagueFilter) {
    const prev = jugLeagueFilter.value;
    while (jugLeagueFilter.options.length > 1) jugLeagueFilter.remove(1);
    getPlayerLeagueCodes().forEach(code => appendLeagueOption(jugLeagueFilter, code));
    if ([...jugLeagueFilter.options].some(opt => opt.value === prev)) jugLeagueFilter.value = prev;
    jugLeagueFilter.addEventListener("change", e => {
      populateSelect("jug-team", getPlayerTeamsByLeague(e.target.value));
      const playerSel = document.getElementById("jug-player");
      if (playerSel) while (playerSel.options.length > 1) playerSel.remove(1);
      const result = document.getElementById("jug-result");
      if (result) {
        result.innerHTML = `<div class="state-box"><div class="icon">👤</div><p>Selecciona un equipo para ver sus jugadores</p></div>`;
      }
    });
  }

  const cmpFilter = document.getElementById("cmpLeagueFilter");
  if (cmpFilter) {
    cmpFilter.addEventListener("change", e => {
      const teams = getTeamsByLeague(e.target.value);
      ["cmp-home","cmp-away"].forEach(id => populateSelect(id, teams));
    });
  }

  const inicioFilter = document.getElementById("inicioLeagueFilter");
  if (inicioFilter) {
    const prev = inicioFilter.value;
    while (inicioFilter.options.length > 1) inicioFilter.remove(1);
    const fxLeagues = new Set([
      ...(APP.fixtures?.calendar || []).map(f => f.league),
      ...(APP.fixtures?.upcoming || []).map(f => f.league),
      ...(APP.fixtures?.recent   || []).map(f => f.league),
    ]);
    sortLeagueCodes(Array.from(fxLeagues)).forEach(code => appendLeagueOption(inicioFilter, code));
    if ([...inicioFilter.options].some(opt => opt.value === prev)) inicioFilter.value = prev;
    inicioFilter.addEventListener("change", e => {
      if (typeof renderInicio === "function") renderInicio(e.target.value);
    });
  }
}

function initTabs() {
  const tabs = document.getElementById("mainTabs");
  if (tabs) {
    tabs.addEventListener("click", e => {
      const btn = e.target.closest(".tab-btn");
      if (!btn) return;
      openTab(btn.dataset.tab);
    });
  }

  document.querySelectorAll(".sub-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".sub-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".sub-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const panel = document.getElementById("sub-" + btn.dataset.sub);
      if (panel) panel.classList.add("active");
    });
  });
}

function openTab(tabName) {
  const btn = document.querySelector('.tab-btn[data-tab="' + tabName + '"]');
  const panel = document.getElementById("tab-" + tabName);
  if (!btn || !panel) return false;
  document.querySelectorAll(".tab-btn").forEach(item => {
    item.classList.remove("active");
    item.setAttribute("aria-selected", "false");
  });
  document.querySelectorAll(".tab-panel").forEach(item => item.classList.remove("active"));
  btn.classList.add("active");
  btn.setAttribute("aria-selected", "true");
  panel.classList.add("active");
  return true;
}

function globalSearchItems() {
  const items = [];
  (APP.teams || []).forEach(name => items.push({
    type: "Equipo",
    label: name,
    meta: APP.teamAssets?.teams?.[name]?.league || "",
    href: "index.html?tab=comparador&home=" + encodeURIComponent(name),
    media: entityMedia("team", name),
  }));
  Object.entries(APP.players || {}).forEach(([team, rows]) => (rows || []).forEach(player => items.push({
    type: "Jugador",
    label: player.player,
    meta: team,
    href: "player.html?team=" + encodeURIComponent(team) + "&player=" + encodeURIComponent(player.player),
    media: entityMedia("player", player.player, team),
  })));
  (APP.referees || []).forEach(referee => items.push({
    type: "Arbitro",
    label: referee.name,
    meta: referee.league || "",
    href: "referee.html?name=" + encodeURIComponent(referee.name) + "&league=" + encodeURIComponent(referee.league || ""),
    media: '<span class="entity-media entity-media--ref">R</span>',
  }));
  [...(APP.fixtures?.upcoming || []), ...(APP.fixtures?.recent || [])].forEach(fixture => items.push({
    type: "Partido",
    label: fixture.home + " vs " + fixture.away,
    meta: fixture.date + " · " + (fixture.league || ""),
    href: typeof buildMatchHref === "function" ? buildMatchHref(fixture) : "match.html",
    media: entityMedia("team", fixture.home),
  }));
  return items;
}

function initGlobalSearch() {
  const input = document.getElementById("globalSearch");
  const results = document.getElementById("globalSearchResults");
  if (!input || !results) return;
  const items = globalSearchItems();
  const normalize = value => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const render = () => {
    const query = normalize(input.value).trim();
    if (query.length < 2) {
      results.hidden = true;
      results.innerHTML = "";
      return;
    }
    const matches = items.filter(item => normalize(item.label + " " + item.meta).includes(query)).slice(0, 10);
    results.innerHTML = matches.length ? matches.map(item =>
      '<a href="' + item.href + '">' + item.media + '<span><strong>' + escHtml(item.label) + '</strong><small>' + escHtml(item.type + " · " + item.meta) + '</small></span></a>'
    ).join("") : '<div class="kdx-search-empty">Sin resultados para “' + escHtml(input.value) + '”</div>';
    results.hidden = false;
  };
  input.addEventListener("input", render);
  input.addEventListener("focus", render);
  document.addEventListener("click", event => {
    if (!event.target.closest(".kdx-global-search")) results.hidden = true;
  });
  input.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      results.hidden = true;
      input.blur();
    }
  });
}

function updateLivePanel() {
  const status = document.getElementById("liveDataStatus");
  if (!status) return;
  const calendar = APP.dataHealth?.domains?.calendar;
  if (calendar?.updated_at) {
    status.textContent = "Calendario batch actualizado " + new Date(calendar.updated_at).toLocaleString("es-ES") + ". El feed live sigue desactivado.";
  }
}

function applyRouteParams() {
  const params = new URLSearchParams(location.search);
  const tab = params.get("tab");
  if (!tab || !openTab(tab)) return;
  if (typeof closeLanding === "function") closeLanding();
  if (tab === "comparador" && params.get("home")) {
    const home = document.getElementById("cmp-home");
    if (home) home.value = params.get("home");
  }
}

function initModules() {
  ["initInicio", "initComparador", "initH2H", "initJugadores", "initArbitros"].forEach(name => {
    const initializer = window[name];
    if (typeof initializer !== "function") return;
    try {
      initializer();
    } catch (error) {
      console.error(`KICKDEX module ${name} failed:`, error);
    }
  });
}

// ── Utilities ──────────────────────────────────────────────────────────────

function fmt(val, dec = 2) {
  if (val == null || isNaN(val)) return "—";
  return Number(val).toFixed(dec);
}

function pct(val, dec = 0) {
  if (val == null || isNaN(val)) return "—";
  return (Number(val) * 100).toFixed(dec) + "%";
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function probRow(label, value, color) {
  const p = clamp(value * 100, 0, 100).toFixed(1);
  return `
  <div class="prob-row">
    <span class="prob-label">${label}</span>
    <div class="prob-track">
      <div class="prob-fill" style="width:${p}%;background:${color || "var(--green)"}"></div>
    </div>
    <span class="prob-pct">${p}%</span>
  </div>`;
}

function statRow(label, value) {
  return `<div class="stat-row"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`;
}

function wdlTag(r) {
  if (r === "W") return `<span class="tag tag-w">V</span>`;
  if (r === "D") return `<span class="tag tag-d">E</span>`;
  return `<span class="tag tag-l">D</span>`;
}

function getTeamStats(team) {
  return APP.teamStats[team] || null;
}

function getH2H(t1, t2) {
  if (!APP.h2h) return null;
  return APP.h2h[`${t1}|${t2}`] || APP.h2h[`${t2}|${t1}`] || null;
}

function isH2HReady() { return APP.h2hReady === true; }

// ── Probability engine ────────────────────────────────────────────────────

function poissonPMF(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  let log_p = -lambda + k * Math.log(lambda);
  for (let i = 1; i <= k; i++) log_p -= Math.log(i);
  return Math.exp(log_p);
}

function calcProbabilities(homeStats, awayStats, h2hSummary) {
  const hHome = homeStats?.home || homeStats?.away;
  const aAway = awayStats?.away || awayStats?.home;
  if (!hHome || !aAway) return null;

  let lambdaH = (hHome.avg_goals ?? 1.5) * 0.7 + (aAway.avg_goals_against ?? 1.2) * 0.3;
  let lambdaA = (aAway.avg_goals ?? 1.2) * 0.7 + (hHome.avg_goals_against ?? 1.3) * 0.3;

  if (h2hSummary && h2hSummary.total >= 3) {
    const h2hGoals = h2hSummary.avg_goals ?? (lambdaH + lambdaA);
    lambdaH = lambdaH * 0.88 + (h2hGoals * 0.48) * 0.12;
    lambdaA = lambdaA * 0.88 + (h2hGoals * 0.52) * 0.12;
  }

  lambdaH = Math.max(0.3, Math.min(5.0, lambdaH));
  lambdaA = Math.max(0.3, Math.min(5.0, lambdaA));

  const MAX_GOALS = 8;
  let home = 0, draw = 0, away = 0, over25 = 0, btts = 0;

  for (let i = 0; i <= MAX_GOALS; i++) {
    for (let j = 0; j <= MAX_GOALS; j++) {
      const p = poissonPMF(i, lambdaH) * poissonPMF(j, lambdaA);
      if (i > j) home += p;
      else if (i === j) draw += p;
      else away += p;
      if (i + j > 2.5) over25 += p;
      if (i > 0 && j > 0) btts += p;
    }
  }

  const total = home + draw + away;
  return {
    home:     home  / total,
    draw:     draw  / total,
    away:     away  / total,
    over25:   over25,
    btts:     btts,
    lambda_h: lambdaH,
    lambda_a: lambdaA,
  };
}

// ── Smart Alerts engine ────────────────────────────────────────────────────

function generateAlerts(homeStats, awayStats, h2hSummary) {
  const alerts = [];
  const hH = homeStats?.home || homeStats?.away;
  const aA = awayStats?.away || awayStats?.home;
  if (!hH || !aA) return alerts;

  const add = (strength, type, text) => alerts.push({ strength, type, text });
  const homeName = homeStats._name || "Local";
  const awayName = awayStats._name || "Visitante";

  // Goals volume
  const avgGoals = ((hH.avg_goals ?? 0) + (aA.avg_goals ?? 0)) / 2;
  if (avgGoals >= 2.2) add("HIGH",   "GOALS", `⚽ Partido con muchos goles esperados — media combinada ${avgGoals.toFixed(1)}`);
  if (avgGoals <= 1.3) add("HIGH",   "GOALS", `🔒 Partido bajo en goles esperado — media combinada ${avgGoals.toFixed(1)}`);

  // Over/Under 2.5
  const over25 = ((hH.over25_rate ?? 0) + (aA.over25_rate ?? 0)) / 2;
  if (over25 >= 0.65) add("HIGH",   "OVER_UNDER", `📈 Fuerte tendencia Over 2.5 — ${pct(over25)} de los partidos`);
  if (over25 <= 0.30) add("HIGH",   "OVER_UNDER", `📉 Fuerte tendencia Under 2.5 — solo ${pct(over25)} superan 2.5 goles`);

  // BTTS
  const btts = ((hH.btts_rate ?? 0) + (aA.btts_rate ?? 0)) / 2;
  if (btts >= 0.62) add("HIGH",   "BTTS", `🎯 Alta probabilidad BTTS — ${pct(btts)} de partidos con ambos marcando`);
  if (btts <= 0.28) add("MEDIUM", "BTTS", `🛡️ Poca probabilidad BTTS — ${pct(btts)} de partidos con ambos marcando`);

  // Clean sheets
  const hCS = hH.clean_sheet_rate ?? 0;
  const aCS = aA.clean_sheet_rate ?? 0;
  if (hCS >= 0.45) add("MEDIUM", "DEFENSE", `🧤 ${homeName} en casa — portería a cero en ${pct(hCS)} de sus partidos`);
  if (aCS >= 0.40) add("MEDIUM", "DEFENSE", `🧤 ${awayName} fuera — portería a cero en ${pct(aCS)} de sus partidos`);

  // Defensive fragility
  const hGA = hH.avg_goals_against ?? 0;
  const aGA = aA.avg_goals_against ?? 0;
  if (hGA >= 2.0) add("MEDIUM", "DEFENSE", `⚠️ ${homeName} encaja ${hGA.toFixed(1)} goles/partido en casa`);
  if (aGA >= 2.0) add("MEDIUM", "DEFENSE", `⚠️ ${awayName} encaja ${aGA.toFixed(1)} goles/partido fuera`);

  // Dominant home form
  if ((hH.win_rate ?? 0) >= 0.65) add("HIGH", "FORM", `🏠 ${homeName} dominante en casa — ${pct(hH.win_rate)} victorias`);
  if ((aA.win_rate ?? 0) >= 0.55) add("HIGH", "FORM", `✈️ ${awayName} fuerte fuera — ${pct(aA.win_rate)} victorias`);

  // Form streaks from match log
  const streak = (log, res) => {
    let n = 0;
    for (const m of (log || [])) { if ((m.result || "").toUpperCase() === res) n++; else break; }
    return n;
  };
  const hWins = streak(hH.match_log, "W");
  const aWins = streak(aA.match_log, "W");
  const hLoss = streak(hH.match_log, "L");
  const aLoss = streak(aA.match_log, "L");
  if (hWins >= 4) add("HIGH",   "FORM", `🔥 ${homeName} en racha — ${hWins} victorias seguidas en casa`);
  if (aWins >= 3) add("HIGH",   "FORM", `🔥 ${awayName} en racha — ${aWins} victorias seguidas fuera`);
  if (hLoss >= 3) add("MEDIUM", "FORM", `📉 ${homeName} en mala racha — ${hLoss} derrotas seguidas en casa`);
  if (aLoss >= 3) add("MEDIUM", "FORM", `📉 ${awayName} en mala racha — ${aLoss} derrotas seguidas fuera`);

  // H2H patterns
  if (h2hSummary && h2hSummary.total >= 4) {
    if ((h2hSummary.over25_rate ?? 0) >= 0.65)
      add("MEDIUM", "H2H", `📊 H2H: Over 2.5 en ${pct(h2hSummary.over25_rate)} de sus enfrentamientos directos`);
    if ((h2hSummary.btts_rate ?? 0) >= 0.60)
      add("MEDIUM", "H2H", `📊 H2H: BTTS en ${pct(h2hSummary.btts_rate)} de sus enfrentamientos directos`);
    if ((h2hSummary.over25_rate ?? 1) <= 0.30)
      add("MEDIUM", "H2H", `📊 H2H: muy pocos goles — Over 2.5 solo en ${pct(h2hSummary.over25_rate)} de sus duelos`);
  }

  const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  alerts.sort((a, b) => order[a.strength] - order[b.strength]);
  return alerts.slice(0, 8);
}

// ── Table sorting — multi-criterion (click = single, shift+click = add) ────

const _tableSorts = new WeakMap(); // tableEl → [{col, dir, label}, ...]

function _thLabel(th) {
  return th.getAttribute("title") || th.textContent.replace(/[⇅↑↓]/g, "").trim();
}

function _cellValue(td) {
  if (!td) return null;
  const raw = td.dataset.sort ?? td.textContent;
  const num = parseFloat(String(raw).replace(/[%+,\s]/g, ""));
  return isNaN(num) ? String(raw).trim().toLowerCase() : num;
}

function _compare(a, b) {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), "es");
}

function _applySort(tableEl) {
  const sorts = _tableSorts.get(tableEl) || [];
  const tbody = tableEl.querySelector("tbody");
  if (!tbody || sorts.length === 0) return;
  const rows = Array.from(tbody.querySelectorAll("tr"));
  rows.sort((a, b) => {
    for (const s of sorts) {
      const av = _cellValue(a.cells[s.col]);
      const bv = _cellValue(b.cells[s.col]);
      const cmp = _compare(av, bv);
      if (cmp !== 0) return s.dir === "asc" ? cmp : -cmp;
    }
    return 0;
  });
  rows.forEach(r => tbody.appendChild(r));
}

function _renderHeaderIcons(tableEl) {
  const sorts = _tableSorts.get(tableEl) || [];
  tableEl.querySelectorAll("thead th").forEach((th, col) => {
    if (th.dataset.nosort !== undefined) return;
    // Remove old sort indicators
    th.querySelectorAll(".sort-icon, .sort-badge").forEach(el => el.remove());
    th.classList.remove("sorted");

    const s = sorts.find(s => s.col === col);
    const icon = document.createElement("span");
    icon.className = "sort-icon";
    if (s) {
      icon.textContent = s.dir === "asc" ? "↑" : "↓";
      th.classList.add("sorted");
      if (sorts.length > 1) {
        const badge = document.createElement("span");
        badge.className = "sort-badge";
        badge.textContent = sorts.indexOf(s) + 1;
        th.appendChild(badge);
      }
    } else {
      icon.textContent = "⇅";
    }
    th.appendChild(icon);
  });
}

function _renderSortChips(tableEl) {
  const sorts = _tableSorts.get(tableEl) || [];
  // Find or create chip container just before table's parent (.table-wrap)
  const wrap = tableEl.closest(".table-wrap") || tableEl.parentElement;
  let panel = wrap.previousElementSibling;
  if (!panel || !panel.classList.contains("sort-chips")) {
    panel = document.createElement("div");
    panel.className = "sort-chips";
    wrap.parentElement.insertBefore(panel, wrap);
  }
  panel.innerHTML = "";
  if (sorts.length === 0) return;

  sorts.forEach((s, i) => {
    const chip = document.createElement("span");
    chip.className = "sort-chip";
    chip.innerHTML = `${s.label} ${s.dir === "asc" ? "↑" : "↓"} <span class="x" title="Quitar criterio">×</span>`;
    chip.querySelector(".x").addEventListener("click", () => {
      const arr = _tableSorts.get(tableEl);
      arr.splice(i, 1);
      _applySort(tableEl);
      _renderSortChips(tableEl);
      _renderHeaderIcons(tableEl);
    });
    panel.appendChild(chip);
  });
}

function initTableSort(tableEl) {
  if (!tableEl) return;
  if (_tableSorts.has(tableEl)) return; // idempotente
  _tableSorts.set(tableEl, []);
  _renderHeaderIcons(tableEl);

  tableEl.querySelectorAll("thead th").forEach((th, col) => {
    if (th.dataset.nosort !== undefined) return;

    th.style.cursor = "pointer";
    th.addEventListener("click", e => {
      const sorts = _tableSorts.get(tableEl);
      const idx   = sorts.findIndex(s => s.col === col);

      if (e.shiftKey) {
        // Shift+click: add/toggle this column as secondary criterion
        if (idx >= 0) {
          sorts[idx].dir = sorts[idx].dir === "asc" ? "desc" : "asc";
        } else {
          sorts.push({ col, dir: "desc", label: _thLabel(th) });
        }
      } else {
        // Plain click: single-column sort (toggle dir if already active)
        if (sorts.length === 1 && idx === 0) {
          sorts[0].dir = sorts[0].dir === "asc" ? "desc" : "asc";
        } else {
          _tableSorts.set(tableEl, [{ col, dir: "desc", label: _thLabel(th) }]);
        }
      }
      _applySort(tableEl);
      _renderSortChips(tableEl);
      _renderHeaderIcons(tableEl);
    });
  });
}

function initAllTables(container) {
  (container || document).querySelectorAll("table").forEach(t => initTableSort(t));
}

// ── Bootstrap ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initLanding();
  applyI18n();
  const lt = document.getElementById("langToggle");
  if (lt) lt.textContent = LANG === "es" ? "🇪🇸 ES" : "🇬🇧 EN";
  initTabs();
  loadAllData();
});
