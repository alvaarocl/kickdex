/**
 * landing.js — Standalone landing page logic for KICKDEX
 * Handles: i18n, hero edge widget, stat counters, CTA wiring.
 * Does NOT boot the full app (no fixture/player data fetch).
 */

"use strict";

// ── i18n (landing keys only) ───────────────────────────────
const LPI18N = {
  es: {
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
    edge_card_prob_model: "Prob. modelo",
    edge_card_prob_implied: "Prob. implícita",
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
  },
  en: {
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
    edge_card_prob_model: "Model prob.",
    edge_card_prob_implied: "Implied prob.",
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
  },
};

let LP_LANG = localStorage.getItem("kdx_lang") || "es";

function lpT(key) {
  return (LPI18N[LP_LANG] || LPI18N.es)[key] || key;
}

function lpApplyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(function(el) {
    var key = el.dataset.i18n;
    if (el.tagName === "INPUT") { el.placeholder = lpT(key); return; }
    el.textContent = lpT(key);
  });
  document.documentElement.lang = LP_LANG === "en" ? "en" : "es";
  var label = LP_LANG === "es" ? "🇪🇸 ES" : "🇬🇧 EN";
  document.querySelectorAll("#langToggle, #langToggleLp").forEach(function(b) { b.textContent = label; });
}

// Called by inline onclick="toggleLang()" on the language button
function toggleLang() {
  LP_LANG = LP_LANG === "es" ? "en" : "es";
  localStorage.setItem("kdx_lang", LP_LANG);
  lpApplyI18n();
}

// ── Stat counters ──────────────────────────────────────────
function lpAnimateCounters() {
  document.querySelectorAll("[data-counter]").forEach(function(el) {
    var target = parseInt(el.dataset.counter, 10);
    if (!target) return;
    var suffix = el.dataset.suffix || "";
    var abbrev = el.dataset.abbrev === "true";
    var dur    = 1400;
    var start  = performance.now();

    function step(now) {
      var t    = Math.min((now - start) / dur, 1);
      var ease = 1 - Math.pow(1 - t, 3);
      var val  = Math.round(ease * target);
      var display;
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

// ── Utilities ──────────────────────────────────────────────
function lpFormatPercent(value, decimals) {
  decimals = decimals === undefined ? 1 : decimals;
  var num = Number(value);
  if (!Number.isFinite(num)) return "—";
  return (num * 100).toFixed(decimals) + "%";
}

// ── Hero edge widget ───────────────────────────────────────
var LP_EDGES = null;

function lpUpdateHeroEdge() {
  var target = document.getElementById("hero-edge");
  if (!target) return;

  var edge = (LP_EDGES && LP_EDGES.top) || ((LP_EDGES && LP_EDGES.items) || [])[0];
  var statusEl  = document.getElementById("hero-edge-status");
  var matchEl   = document.getElementById("hero-edge-match");
  var probEl    = document.getElementById("hero-edge-prob");
  var impliedEl = document.getElementById("hero-edge-implied");
  var sampleEl  = document.getElementById("hero-edge-sample");

  if (!edge) {
    if (statusEl)  statusEl.textContent  = "data · sin cuotas";
    if (matchEl)   matchEl.innerHTML     = "Sin edges <em>con</em> cuotas";
    if (probEl)    probEl.textContent    = "—";
    if (impliedEl) impliedEl.textContent = "—";
    if (sampleEl)  sampleEl.textContent  = "0 evaluados";
    if (window.KDXEdge && window.KDXEdge.renderEdgeNumber) {
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

  var isLive       = edge.status === "upcoming";
  var sourceLabel  = isLive ? "live · Bet365" : "histórico · Bet365";
  var homeName     = (typeof teamDisplayName === "function" ? teamDisplayName(edge.home || "") : edge.home) || "Local";
  var awayName     = (typeof teamDisplayName === "function" ? teamDisplayName(edge.away || "") : edge.away) || "Visitante";
  var matchLabel   = homeName + " <em>vs</em> " + awayName;
  var selName      = edge.selection && (edge.selection === edge.home || edge.selection === edge.away)
    ? (typeof teamDisplayName === "function" ? teamDisplayName(edge.selection) : edge.selection)
    : edge.selection;
  var caption      = (selName || edge.market_label) + " · " + (edge.market_label || "1X2") + " · Bet365 " + (edge.odds || "—");

  if (statusEl)  statusEl.textContent = sourceLabel;
  if (matchEl)   matchEl.innerHTML    = matchLabel;
  if (probEl)    probEl.textContent   = lpFormatPercent(edge.probability);
  if (impliedEl) impliedEl.textContent = lpFormatPercent(edge.implied_probability);
  if (sampleEl) {
    var hm = (edge.model && edge.model.home_matches) || 0;
    var am = (edge.model && edge.model.away_matches) || 0;
    sampleEl.textContent = Math.min(hm, am) + " partidos";
  }

  if (window.KDXEdge && window.KDXEdge.renderEdgeNumber) {
    window.KDXEdge.renderEdgeNumber(target, {
      value: Number(edge.edge_pct),
      label: "EDGE",
      caption: caption,
      size: "xxl",
      tone: Number(edge.edge_pct) >= 0 ? "value" : "risk",
    });
  } else {
    target.dataset.edge        = String(edge.edge_pct || 0);
    target.dataset.edgeCaption = caption;
    target.dataset.edgeTone    = Number(edge.edge_pct) >= 0 ? "value" : "risk";
  }
}

// ── Landing metrics (total matches from meta.json) ─────────
var LP_META = null;

function lpUpdateLandingMetrics() {
  var total = Number(LP_META && LP_META.total_matches);
  var first = document.querySelector(".lp-stat-num[data-counter]");
  if (first && Number.isFinite(total) && total > 0) {
    first.dataset.counter = String(total);
    first.textContent = total >= 1000 ? Math.round(total / 1000) + "k+" : total + "+";
  }
}

// ── Fetch ──────────────────────────────────────────────────
function lpFetchJSON(path) {
  return fetch(path).then(function(r) {
    if (!r.ok) throw new Error("HTTP " + r.status + ": " + path);
    return r.json();
  });
}

// ── Bootstrap ──────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function() {
  lpApplyI18n();

  // Wire all "launch terminal" CTA buttons to navigate to the app
  ["landing-start", "lp-enter-nav", "lp-final-cta"].forEach(function(id) {
    var btn = document.getElementById(id);
    if (btn) btn.addEventListener("click", function() { window.location.href = "index.html"; });
  });

  // Kick off landing animations (uses #landing-overlay as scroll root)
  if (typeof initLandingAnimations === "function") {
    initLandingAnimations();
  }

  // Initial counter animation (placeholder values from HTML)
  setTimeout(lpAnimateCounters, 200);

  // Fetch only the two lightweight JSON files needed by the landing
  Promise.all([
    lpFetchJSON("data/meta.json"),
    lpFetchJSON("data/edges.json"),
  ]).then(function(results) {
    LP_META  = results[0];
    LP_EDGES = results[1];
    lpUpdateLandingMetrics();
    lpAnimateCounters();   // re-run with real total_matches value
    lpUpdateHeroEdge();
  }).catch(function(err) {
    console.warn("KICKDEX landing: data fetch failed", err);
  });
});
