/**
 * app.js — Core: data loading, tab management, i18n, landing, shared utilities
 * KICKDEX — GitHub Pages static frontend
 */

"use strict";

// ── i18n ───────────────────────────────────────────────────────────────────
const I18N = {
  es: {
    tab_inicio: "Inicio", tab_comparador: "Comparador", tab_h2h: "H2H",
    tab_jugadores: "Jugadores", tab_valor: "Value Bets", tab_arbitros: "Árbitros",
    arb_title: "Árbitros", arb_subtitle: "Perfil disciplinario histórico. Identifica árbitros con tendencia a sacar más o menos tarjetas.",
    league_all: "Todas", league_sp1: "La Liga", league_sp2: "Segunda",
    inicio_title: "Calendario y Partidos",
    inicio_subtitle: "Próximos partidos con cuotas Bet365. Pulsa «Analizar» para ver el análisis completo.",
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
    val_sub_calc: "Calculadora EV", val_sub_patterns: "Patrones históricos",
    val_odd_home: "Cuota 1 — Local", val_odd_draw: "Cuota X — Empate",
    val_odd_away: "Cuota 2 — Visitante", val_odd_over: "Cuota Over 2.5",
    val_odd_btts: "Cuota BTTS", val_run: "Calcular valor",
    val_prompt: "Selecciona equipos e introduce las cuotas de tu casa de apuestas",
    landing_title: "La terminal de datos del fútbol",
    landing_subtitle: "22 años de historia. 15.000+ partidos. Análisis profesional 100% gratuito.",
    landing_cta: "⚡ EMPEZAR A ANALIZAR",
    landing_f1_title: "Calendario en Vivo",
    landing_f1_body: "Partidos de hoy y próxima jornada de La Liga y Segunda, con cuotas Bet365.",
    landing_f2_title: "Análisis Pre-Partido",
    landing_f2_body: "Forma reciente, H2H, Smart Alerts y probabilidades Poisson para cualquier partido.",
    landing_f3_title: "Historial Completo",
    landing_f3_body: "Todos los enfrentamientos directos desde 2004 con cuotas y división.",
    landing_f4_title: "Player Scouting",
    landing_f4_body: "Estadísticas de cada jugador y buscador de oportunidades en player props.",
    landing_footer: "Uso educativo · Datos: football-data.co.uk + FBref",
    disclaimer: "Esta herramienta es exclusivamente informativa y no constituye asesoramiento de apuestas. Las probabilidades son estimaciones matemáticas basadas en datos históricos. El juego puede crear adicción — juega con responsabilidad.",
    odds: "Cuotas", home: "Local", draw: "Empate", away: "Visitante",
    player: "Jugador", shots: "Tiros", shots_on: "A Puerta",
    goals: "Goles", assists: "Asist.", matches: "PJ",
  },
  en: {
    tab_inicio: "Home", tab_comparador: "Match Analysis", tab_h2h: "H2H",
    tab_jugadores: "Players", tab_valor: "Value Bets", tab_arbitros: "Referees",
    arb_title: "Referees", arb_subtitle: "Historical disciplinary profile. Identify referees with a tendency to show more or fewer cards.",
    league_all: "All", league_sp1: "La Liga", league_sp2: "Segunda",
    inicio_title: "Calendar & Matches",
    inicio_subtitle: "Upcoming matches with Bet365 odds. Click «Analyze» for the full breakdown.",
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
    val_sub_calc: "EV Calculator", val_sub_patterns: "Historical Patterns",
    val_odd_home: "Odds 1 — Home", val_odd_draw: "Odds X — Draw",
    val_odd_away: "Odds 2 — Away", val_odd_over: "Odds Over 2.5",
    val_odd_btts: "Odds BTTS", val_run: "Calculate value",
    val_prompt: "Select teams and enter odds from your bookmaker",
    landing_title: "The football data terminal",
    landing_subtitle: "22 years of history. 15,000+ matches. Pro-level analytics, 100% free.",
    landing_cta: "⚡ START ANALYZING",
    landing_f1_title: "Live Calendar",
    landing_f1_body: "Today's and next matchday fixtures for La Liga and Segunda, with Bet365 odds.",
    landing_f2_title: "Pre-Match Analysis",
    landing_f2_body: "Recent form, H2H, Smart Alerts and Poisson probabilities for every match.",
    landing_f3_title: "Full History",
    landing_f3_body: "Every head-to-head since 2004 with odds and division.",
    landing_f4_title: "Player Scouting",
    landing_f4_body: "Per-player stats and player-prop opportunity finder.",
    landing_footer: "Educational use · Data: football-data.co.uk + FBref",
    disclaimer: "This tool is for informational purposes only and does not constitute betting advice. Probabilities are mathematical estimates based on historical data. Gambling can be addictive — play responsibly.",
    odds: "Odds", home: "Home", draw: "Draw", away: "Away",
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
  document.querySelectorAll("[data-counter]").forEach(el => {
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

function initLanding() {
  const seen    = localStorage.getItem("kdx_seen");
  const landing = document.getElementById("landing-overlay");
  if (!seen && landing) {
    landing.style.display = "flex";
    setTimeout(() => { animateCounters(); activateLandingCards(); }, 200);
  }
  const startBtn = document.getElementById("landing-start");
  if (startBtn) {
    startBtn.addEventListener("click", () => {
      if (landing) landing.style.display = "none";
      localStorage.setItem("kdx_seen", "1");
    });
  }
  // Also animate when logo re-opens the landing
  const logo = document.querySelector(".logo");
  if (logo) {
    logo.addEventListener("click", () => {
      setTimeout(() => { animateCounters(); activateLandingCards(); }, 100);
    });
  }
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
  valuePatterns: [],
  referees:    [],
  meta:        {},
  loaded:      false,
};

// ── Data fetching ──────────────────────────────────────────────────────────
const DATA_BASE = "./data/";

async function fetchJSON(file) {
  const res = await fetch(DATA_BASE + file);
  if (!res.ok) throw new Error(`HTTP ${res.status} loading ${file}`);
  return res.json();
}

async function loadAllData() {
  const metaEl = document.getElementById("metaInfo");
  if (metaEl) metaEl.innerHTML = `<span class="spinner"></span> Cargando datos...`;

  try {
    const [meta, teams, teamStats, h2h, players, playersDetail, valuePatterns, leagues, fixtures, referees] = await Promise.all([
      fetchJSON("meta.json"),
      fetchJSON("teams.json"),
      fetchJSON("team_stats.json"),
      fetchJSON("h2h.json"),
      fetchJSON("players.json").catch(() => ({})),
      fetchJSON("players_detail.json").catch(() => ({})),
      fetchJSON("value_patterns.json").catch(() => []),
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
    APP.valuePatterns  = valuePatterns;
    APP.leagues        = leagues;
    APP.fixtures       = fixtures;
    APP.referees       = referees;
    APP.loaded         = true;

    updateHeader();
    populateAllSelects();
    initSegControls();
    initModules();

    if (typeof renderPatterns === "function") renderPatterns();

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
  ["cmp-home","cmp-away","val-home","val-away"].forEach(id => populateSelect(id, cmpTeams));
  ["h2h-t1","h2h-t2"].forEach(id => populateSelect(id, APP.teams));
  populateSelect("jug-team", APP.teams);
}

function initSegControls() {
  const populateLeagueSelect = (id) => {
    const sel = document.getElementById(id);
    if (!sel || sel.tagName !== "SELECT") return;
    Object.entries(APP.leagues).forEach(([code, data]) => {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = data.name;
      sel.appendChild(opt);
    });
  };

  populateLeagueSelect("cmpLeagueFilter");
  populateLeagueSelect("h2hLeagueFilter");
  populateLeagueSelect("inicioLeagueFilter");

  const cmpFilter = document.getElementById("cmpLeagueFilter");
  if (cmpFilter) {
    cmpFilter.addEventListener("change", e => {
      const teams = getTeamsByLeague(e.target.value);
      ["cmp-home","cmp-away","val-home","val-away"].forEach(id => populateSelect(id, teams));
    });
  }

  const h2hFilter = document.getElementById("h2hLeagueFilter");
  if (h2hFilter) {
    h2hFilter.addEventListener("change", e => {
      const teams = getTeamsByLeague(e.target.value);
      ["h2h-t1","h2h-t2"].forEach(id => populateSelect(id, teams));
    });
  }

  const inicioFilter = document.getElementById("inicioLeagueFilter");
  if (inicioFilter) {
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
  if (typeof initValor      === "function") initValor();
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

  const avgGoals = ((hH.avg_goals ?? 0) + (aA.avg_goals ?? 0)) / 2;
  if (avgGoals >= 2.2) add("HIGH", "GOALS", `⚽ Muchos goles esperados — promedio combinado ${avgGoals.toFixed(1)}`);
  
  const over25 = ((hH.over25_rate ?? 0) + (aA.over25_rate ?? 0)) / 2;
  if (over25 >= 0.65) add("HIGH", "OVER_UNDER", `📈 Tendencia Over 2.5 — ${pct(over25)}`);

  const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  alerts.sort((a, b) => order[a.strength] - order[b.strength]);
  return alerts.slice(0, 8);
}

// ── Table sorting ──────────────────────────────────────────────────────────

function initTableSort(tableEl) {
  if (!tableEl) return;
  const headers = tableEl.querySelectorAll("thead th");
  let lastCol = -1, ascending = true;

  headers.forEach((th, col) => {
    if (!th.querySelector(".sort-icon")) {
      const icon = document.createElement("span");
      icon.className = "sort-icon";
      icon.textContent = "⇅";
      th.appendChild(icon);
    }

    th.addEventListener("click", () => {
      ascending = lastCol === col ? !ascending : true;
      lastCol = col;
      
      headers.forEach(h => {
        h.classList.remove("sorted");
        const ic = h.querySelector(".sort-icon");
        if (ic) ic.textContent = "⇅";
      });
      th.classList.add("sorted");
      const ic = th.querySelector(".sort-icon");
      if (ic) ic.textContent = ascending ? "↑" : "↓";

      const tbody = tableEl.querySelector("tbody");
      if (!tbody) return;
      const rows = Array.from(tbody.querySelectorAll("tr"));

      rows.sort((a, b) => {
        const aVal = a.cells[col].textContent.trim().replace(/[%+]/g, "");
        const bVal = b.cells[col].textContent.trim().replace(/[%+]/g, "");
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        return ascending 
          ? (isNaN(aNum) ? aVal.localeCompare(bVal) : aNum - bNum)
          : (isNaN(aNum) ? bVal.localeCompare(aVal) : bNum - aNum);
      });
      rows.forEach(r => tbody.appendChild(r));
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
