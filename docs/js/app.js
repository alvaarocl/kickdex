/**
 * app.js — Core: data loading, tab management, i18n, landing, shared utilities
 * KICKDEX — GitHub Pages static frontend
 */

"use strict";

// ── i18n ───────────────────────────────────────────────────────────────────
const I18N = {
  es: {
    tab_inicio: "Inicio", tab_comparador: "Comparador", tab_h2h: "H2H",
    tab_jugadores: "Jugadores", tab_arbitros: "Árbitros",
    arb_title: "Árbitros", arb_subtitle: "Perfil disciplinario histórico. Identifica árbitros con tendencia a sacar más o menos tarjetas.",
    league_all: "Todas", league_sp1: "La Liga", league_sp2: "Segunda",
    inicio_title: "Calendario y Partidos",
    inicio_subtitle: "Próximos partidos y resultados recientes. Pulsa «Analizar» para ver el análisis completo.",
    inicio_filter: "Filtrar por liga",
    inicio_upcoming: "Próxima jornada",
    inicio_today: "Partidos de hoy",
    inicio_recent: "Resultados recientes",
    inicio_no_upcoming: "Aún no hay fixtures publicados para la próxima jornada. Football-data.co.uk los añade 2-3 días antes. Mientras, puedes analizar cualquier partido desde el Comparador.",
    inicio_analyze: "Analizar",
    loading: "Cargando partidos...",
    cmp_league: "Liga", cmp_home: "Equipo Local", cmp_away: "Equipo Visitante",
    cmp_last: "Ventana", cmp_analyze: "Analizar",
    cmp_prompt: "Selecciona dos equipos y pulsa Analizar",
    cmp_players_title: "Comparativa de Jugadores",
    cmp_players_none: "Sin datos de jugadores para este partido",
    h2h_team1: "Equipo 1", h2h_team2: "Equipo 2", h2h_run: "Ver H2H",
    h2h_prompt: "Selecciona dos equipos para ver su historial",
    jug_team: "Equipo", jug_player: "Jugador", jug_run: "Ver Stats",
    jug_prompt: "Selecciona un equipo para ver las estadísticas de sus jugadores",
    landing_title: "La terminal de datos del fútbol",
    landing_subtitle: "22 años de historia. 15.000+ partidos. Análisis profesional 100% gratuito.",
    landing_cta: "⚡ EMPEZAR A ANALIZAR",
    landing_f1_title: "Calendario en Vivo",
    landing_f1_body: "Partidos de hoy, próxima jornada y resultados recientes agrupados por liga.",
    landing_f2_title: "Análisis Pre-Partido",
    landing_f2_body: "Forma reciente, H2H, Smart Alerts y probabilidades Poisson para cualquier partido.",
    landing_f3_title: "Historial Completo",
    landing_f3_body: "Todos los enfrentamientos directos desde 2004 con resultados, goles y división.",
    landing_f4_title: "Player Scouting",
    landing_f4_body: "Estadísticas de cada jugador, rankings por equipo y análisis por métricas.",
    landing_footer: "Uso educativo · Datos: football-data.co.uk + FBref",
    disclaimer: "Esta herramienta es exclusivamente informativa. Las probabilidades son estimaciones matemáticas basadas en datos históricos.",
    home: "Local", draw: "Empate", away: "Visitante",
    player: "Jugador", shots: "Tiros", shots_on: "A Puerta",
    goals: "Goles", assists: "Asist.", matches: "PJ",
  },
  en: {
    tab_inicio: "Home", tab_comparador: "Match Analysis", tab_h2h: "H2H",
    tab_jugadores: "Players", tab_arbitros: "Referees",
    arb_title: "Referees", arb_subtitle: "Historical disciplinary profile. Identify referees with a tendency to show more or fewer cards.",
    league_all: "All", league_sp1: "La Liga", league_sp2: "Segunda",
    inicio_title: "Calendar & Matches",
    inicio_subtitle: "Upcoming matches and recent results. Click «Analyze» for the full breakdown.",
    inicio_filter: "Filter by league",
    inicio_upcoming: "Next matchday",
    inicio_today: "Today's matches",
    inicio_recent: "Recent results",
    inicio_no_upcoming: "No fixtures published for the next matchday yet. Football-data.co.uk adds them 2-3 days before kick-off. In the meantime, analyze any match in the Match Analysis tab.",
    inicio_analyze: "Analyze",
    loading: "Loading matches...",
    cmp_league: "League", cmp_home: "Home Team", cmp_away: "Away Team",
    cmp_last: "Window", cmp_analyze: "Analyze",
    cmp_prompt: "Select two teams and click Analyze",
    cmp_players_title: "Player Comparison",
    cmp_players_none: "No player data available for this match",
    h2h_team1: "Team 1", h2h_team2: "Team 2", h2h_run: "See H2H",
    h2h_prompt: "Select two teams to see their head-to-head history",
    jug_team: "Team", jug_player: "Player", jug_run: "See Stats",
    jug_prompt: "Select a team to view player statistics",
    landing_title: "The football data terminal",
    landing_subtitle: "22 years of history. 15,000+ matches. Pro-level analytics, 100% free.",
    landing_cta: "⚡ START ANALYZING",
    landing_f1_title: "Live Calendar",
    landing_f1_body: "Today's matches, upcoming fixtures and recent results grouped by league.",
    landing_f2_title: "Pre-Match Analysis",
    landing_f2_body: "Recent form, H2H, Smart Alerts and Poisson probabilities for every match.",
    landing_f3_title: "Full History",
    landing_f3_body: "Every head-to-head since 2004 with results, goals and division.",
    landing_f4_title: "Player Scouting",
    landing_f4_body: "Per-player stats, team rankings and metric-based analysis.",
    landing_footer: "Educational use · Data: football-data.co.uk + FBref",
    disclaimer: "This tool is for informational purposes only. Probabilities are mathematical estimates based on historical data.",
    home: "Home", draw: "Draw", away: "Away",
    player: "Player", shots: "Shots", shots_on: "On Target",
    goals: "Goals", assists: "Assists", matches: "MP",
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
  const lt = document.getElementById("langToggle");
  if (lt) lt.textContent = LANG === "es" ? "🇪🇸 ES" : "🇬🇧 EN";
  if (APP.loaded && typeof renderInicio === "function") renderInicio();
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (el.tagName === "INPUT") { el.placeholder = t(key); return; }
    el.textContent = t(key);
  });
  document.documentElement.lang = LANG === "en" ? "en" : "es";
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
  fixtures:    { recent: [], upcoming: [] },
  teamStats:   {},
  h2h:         {},
  players:     {},
  playersDetail: {},
  playerCoverage: {},
  dataStatus:   {},
  referees:    [],
  meta:        {},
  loaded:      false,
};

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

async function loadAllData() {
  const metaEl = document.getElementById("metaInfo");
  if (metaEl) metaEl.innerHTML = `<span class="spinner"></span> Cargando datos...`;

  try {
    const [meta, teams, teamStats, h2h, players, playersDetail, playerCoverage, dataStatus, leagues, fixtures, referees] = await Promise.all([
      fetchJSON("meta.json"),
      fetchJSON("teams.json"),
      fetchJSON("team_stats.json"),
      fetchJSON("h2h.json"),
      fetchJSON("players.json").catch(() => ({})),
      fetchJSON("players_detail.json").catch(() => ({})),
      fetchJSON("player_coverage.json").catch(() => ({})),
      fetchJSON("data_status.json").catch(() => ({})),
      fetchJSON("leagues.json").catch(() => ({})),
      fetchJSON("fixtures.json").catch(() => ({ recent: [], upcoming: [] })),
      fetchJSON("referees.json").catch(() => []),
    ]);

    APP.meta           = meta;
    APP.teams          = teams;
    APP.teamStats      = teamStats;
    APP.h2h            = h2h;
    APP.players        = players;
    APP.playersDetail  = playersDetail;
    APP.playerCoverage = playerCoverage;
    APP.dataStatus     = dataStatus;
    APP.leagues        = leagues;
    APP.fixtures       = fixtures;
    APP.referees       = referees;
    APP.loaded         = true;

    updateHeader();
    populateAllSelects();
    initSegControls();
    initModules();

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
  if (badge) badge.textContent = m.season || "2025/26";
  const upd = m.updated_at ? new Date(m.updated_at).toLocaleDateString("es-ES") : "—";
  const info = document.getElementById("metaInfo");
  if (info) info.textContent = `${(m.total_matches || 0).toLocaleString()} partidos · actualizado ${upd}`;
}

function getTeamsByLeague(leagueCode) {
  if (!leagueCode || leagueCode === "all") return APP.teams;
  const ld = APP.leagues[leagueCode];
  return (ld && ld.teams && ld.teams.length) ? ld.teams : APP.teams;
}

function getPlayerLeagueCodes() {
  const byLeague = APP.playerCoverage?.by_league || {};
  const codes = Object.keys(byLeague).filter(code => (byLeague[code]?.player_rows || 0) > 0);
  if (codes.length) return codes.sort();

  const playerTeams = new Set(Object.keys(APP.playersDetail || APP.players || {}));
  return Object.entries(APP.leagues || {})
    .filter(([, data]) => (data.teams || []).some(team => playerTeams.has(team)))
    .map(([code]) => code)
    .sort();
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
    // Idempotent: keep only the first default option ("Todas"), remove the rest
    while (sel.options.length > 1) sel.remove(1);
    Object.entries(APP.leagues).forEach(([code, data]) => {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = data.name;
      sel.appendChild(opt);
    });
  };

  populateLeagueSelect("cmpLeagueFilter");
  const jugLeagueFilter = document.getElementById("jugLeagueFilter");
  if (jugLeagueFilter) {
    while (jugLeagueFilter.options.length > 1) jugLeagueFilter.remove(1);
    getPlayerLeagueCodes().forEach(code => {
      const ld = APP.leagues[code];
      if (!ld) return;
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = ld.name;
      jugLeagueFilter.appendChild(opt);
    });
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
    while (inicioFilter.options.length > 1) inicioFilter.remove(1);
    const fxLeagues = new Set([
      ...(APP.fixtures?.upcoming || []).map(f => f.league),
      ...(APP.fixtures?.recent   || []).map(f => f.league),
    ]);
    fxLeagues.forEach(code => {
      const ld = APP.leagues[code];
      if (!ld) return;
      const opt = document.createElement("option");
      opt.value = code; opt.textContent = ld.name;
      inicioFilter.appendChild(opt);
    });
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
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const panel = document.getElementById("tab-" + btn.dataset.tab);
      if (panel) panel.classList.add("active");
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

function initModules() {
  if (typeof initInicio     === "function") initInicio();
  if (typeof initComparador === "function") initComparador();
  if (typeof initH2H        === "function") initH2H();
  if (typeof initJugadores  === "function") initJugadores();
  if (typeof initArbitros   === "function") initArbitros();
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
  return APP.h2h[`${t1}|${t2}`] || APP.h2h[`${t2}|${t1}`] || null;
}

// ── Probability engine ────────────────────────────────────────────────────

function poissonPMF(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  let log_p = -lambda + k * Math.log(lambda);
  for (let i = 1; i <= k; i++) log_p -= Math.log(i);
  return Math.exp(log_p);
}

function calcProbabilities(homeStats, awayStats, h2hSummary) {
  const hHome = homeStats?.home;
  const aAway = awayStats?.away;
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
  const hH = homeStats?.home;
  const aA = awayStats?.away;
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
