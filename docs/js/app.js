/**
 * app.js — Core: data loading, tab management, shared utilities
 * Analista Pro — GitHub Pages static frontend
 */

"use strict";

// ── State ──────────────────────────────────────────────────────────────────
const APP = {
  teams:       [],
  teamStats:   {},
  h2h:         {},
  players:     {},
  playersDetail: {},
  valuePatterns: [],
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
  // Show loading state
  const metaEl = document.getElementById("metaInfo");
  metaEl.innerHTML = `<span class="spinner"></span> Cargando datos...`;

  try {
    const [meta, teams, teamStats, h2h, players, playersDetail, valuePatterns] = await Promise.all([
      fetchJSON("meta.json"),
      fetchJSON("teams.json"),
      fetchJSON("team_stats.json"),
      fetchJSON("h2h.json"),
      fetchJSON("players.json").catch(() => ({})),
      fetchJSON("players_detail.json").catch(() => ({})),
      fetchJSON("value_patterns.json").catch(() => []),
    ]);

    APP.meta           = meta;
    APP.teams          = teams;
    APP.teamStats      = teamStats;
    APP.h2h            = h2h;
    APP.players        = players;
    APP.playersDetail  = playersDetail;
    APP.valuePatterns  = valuePatterns;
    APP.loaded         = true;

    updateHeader();
    populateAllSelects();
    initModules();

    // Load patterns immediately
    if (typeof renderPatterns === "function") renderPatterns();

  } catch (err) {
    console.error("Error loading data:", err);
    metaEl.textContent = "Error al cargar datos";
    metaEl.style.color = "var(--red)";
  }
}

function updateHeader() {
  const m = APP.meta;
  document.getElementById("seasonBadge").textContent = m.season || "2025/26";
  const upd = m.updated_at ? new Date(m.updated_at).toLocaleDateString("es-ES") : "—";
  document.getElementById("metaInfo").textContent =
    `${(m.total_matches || 0).toLocaleString()} partidos · actualizado ${upd}`;
}

function populateAllSelects() {
  const ids = [
    "cmp-home","cmp-away",
    "h2h-t1","h2h-t2",
    "val-home","val-away",
    "jug-team",
  ];
  ids.forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const prev = sel.value;
    // Keep placeholder
    while (sel.options.length > 1) sel.remove(1);
    APP.teams.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t; opt.textContent = t;
      sel.appendChild(opt);
    });
    if (prev) sel.value = prev;
  });
}

// ── Tab management ─────────────────────────────────────────────────────────
function initTabs() {
  document.getElementById("mainTabs").addEventListener("click", e => {
    const btn = e.target.closest(".tab-btn");
    if (!btn) return;
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });

  // Sub-tabs (Value)
  document.querySelectorAll(".sub-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".sub-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".sub-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("sub-" + btn.dataset.sub).classList.add("active");
    });
  });
}

function initModules() {
  if (typeof initComparador === "function") initComparador();
  if (typeof initH2H        === "function") initH2H();
  if (typeof initJugadores  === "function") initJugadores();
  if (typeof initValor      === "function") initValor();
}

// ── Utilities ──────────────────────────────────────────────────────────────

/** Format number to fixed decimals or "—" */
function fmt(val, dec = 2) {
  if (val == null || isNaN(val)) return "—";
  return Number(val).toFixed(dec);
}

/** Return percentage string */
function pct(val, dec = 0) {
  if (val == null || isNaN(val)) return "—";
  return (Number(val) * 100).toFixed(dec) + "%";
}

/** Clamp value */
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

/** Create a probability bar row */
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

/** Build a stat row */
function statRow(label, value) {
  return `<div class="stat-row"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`;
}

/** WDL tag */
function wdlTag(r) {
  if (r === "W") return `<span class="tag tag-w">V</span>`;
  if (r === "D") return `<span class="tag tag-d">E</span>`;
  return `<span class="tag tag-l">D</span>`;
}

/** Get team stats with fallback to smallest available window */
function getTeamStats(team) {
  return APP.teamStats[team] || null;
}

/** Get H2H data for a pair (order-independent) */
function getH2H(t1, t2) {
  return APP.h2h[`${t1}|${t2}`] || APP.h2h[`${t2}|${t1}`] || null;
}

// ── Probability engine (Poisson bivariante) ────────────────────────────────

function poissonPMF(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  let log_p = -lambda + k * Math.log(lambda);
  for (let i = 1; i <= k; i++) log_p -= Math.log(i);
  return Math.exp(log_p);
}

/**
 * Calculate match probabilities using bivariate Poisson
 * @param {object} homeStats  - home/away form object from team_stats.json
 * @param {object} awayStats
 * @param {object|null} h2hSummary
 * @returns {{ home, draw, away, over25, btts, lambda_h, lambda_a }}
 */
function calcProbabilities(homeStats, awayStats, h2hSummary) {
  const hHome = homeStats?.home;
  const aAway = awayStats?.away;

  if (!hHome || !aAway) return null;

  let lambdaH = (hHome.avg_goals ?? 1.5) * 0.7 + (aAway.avg_goals_against ?? 1.2) * 0.3;
  let lambdaA = (aAway.avg_goals ?? 1.2) * 0.7 + (hHome.avg_goals_against ?? 1.3) * 0.3;

  // H2H adjustment (small weight)
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
  const hA = homeStats?.away;
  const aA = awayStats?.away;
  const aH = awayStats?.home;

  if (!hH || !aA) return alerts;

  // Helper
  const add = (strength, type, text) => alerts.push({ strength, type, text });

  // GOALS
  const avgGoals = ((hH.avg_goals ?? 0) + (aA.avg_goals ?? 0)) / 2;
  if (avgGoals >= 2.2) add("HIGH",   "GOALS",  `⚽ Partido de muchos goles esperado — promedio combinado ${avgGoals.toFixed(1)} goles`);
  else if (avgGoals <= 1.0) add("HIGH", "GOALS", `🔒 Partido cerrado esperado — promedio combinado ${avgGoals.toFixed(1)} goles`);

  // OVER/UNDER
  const over25 = ((hH.over25_rate ?? 0) + (aA.over25_rate ?? 0)) / 2;
  if (over25 >= 0.65) add("HIGH",   "OVER_UNDER", `📈 Alta tendencia Over 2.5 — ${pct(over25)} de los partidos`);
  else if (over25 <= 0.30) add("MEDIUM", "OVER_UNDER", `📉 Baja tendencia Over 2.5 — ${pct(over25)} de los partidos`);

  // BTTS
  const bttsRate = ((hH.btts_rate ?? 0) + (aA.btts_rate ?? 0)) / 2;
  if (bttsRate >= 0.60) add("HIGH",   "BTTS", `🎯 Alta probabilidad Ambos Marcan — ${pct(bttsRate)} histórico`);
  else if (bttsRate <= 0.25) add("MEDIUM", "BTTS", `🚫 Baja probabilidad Ambos Marcan — ${pct(bttsRate)} histórico`);

  // FORM local
  const homeWR = hH.win_rate ?? 0;
  if (homeWR >= 0.60) add("HIGH",   "FORM", `🏠 ${homeStats._name || "Local"} en casa: racha ganadora ${pct(homeWR)}`);
  else if (homeWR <= 0.25) add("MEDIUM", "FORM", `📉 ${homeStats._name || "Local"} flojo en casa — solo ${pct(homeWR)} victorias`);

  // FORM visitante
  const awayWR = aA.win_rate ?? 0;
  if (awayWR >= 0.50) add("HIGH",   "FORM", `✈️ ${awayStats._name || "Visitante"} fuera de casa: sólido ${pct(awayWR)} victorias`);

  // DEFENSE
  const homeGAg = hH.avg_goals_against ?? 999;
  if (homeGAg <= 0.6) add("MEDIUM", "DEFENSE", `🛡️ ${homeStats._name || "Local"} defiende muy bien en casa — ${homeGAg.toFixed(1)} goles encajados/partido`);
  else if (homeGAg >= 2.0) add("MEDIUM", "DEFENSE", `⚠️ ${homeStats._name || "Local"} concede mucho en casa — ${homeGAg.toFixed(1)} goles/partido`);

  // H2H
  if (h2hSummary && h2hSummary.total >= 5) {
    const goalsH2H = h2hSummary.avg_goals ?? 0;
    if (goalsH2H >= 2.8) add("MEDIUM", "H2H", `⚔️ Historial H2H muy ofensivo — promedio ${goalsH2H.toFixed(1)} goles`);
    const over25H2H = h2hSummary.over25_rate ?? 0;
    if (over25H2H >= 0.65) add("MEDIUM", "H2H", `📊 H2H: ${pct(over25H2H)} de los encuentros Over 2.5`);
    const bttsH2H = h2hSummary.btts_rate ?? 0;
    if (bttsH2H >= 0.60) add("LOW", "H2H", `🎯 H2H: ${pct(bttsH2H)} con Ambos Marcan`);
  }

  // Sort: HIGH first, then MEDIUM, then LOW; cap at 8
  const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  alerts.sort((a, b) => order[a.strength] - order[b.strength]);
  return alerts.slice(0, 8);
}

// ── Table sorting ──────────────────────────────────────────────────────────

/**
 * Wire up click-to-sort on all <th> inside a given table element.
 * Sorts rows by the clicked column; toggles asc/desc on repeat clicks.
 */
function initTableSort(tableEl) {
  if (!tableEl) return;
  const headers = tableEl.querySelectorAll("thead th");
  let lastCol = -1, ascending = true;

  headers.forEach((th, col) => {
    // Add sort icon if not present
    if (!th.querySelector(".sort-icon")) {
      const icon = document.createElement("span");
      icon.className = "sort-icon";
      icon.textContent = "⇅";
      th.appendChild(icon);
    }

    th.addEventListener("click", () => {
      if (lastCol === col) {
        ascending = !ascending;
      } else {
        ascending = true;
        lastCol = col;
      }

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
        const aCell = a.cells[col];
        const bCell = b.cells[col];
        if (!aCell || !bCell) return 0;
        const aText = aCell.textContent.trim().replace(/[%+]/g, "");
        const bText = bCell.textContent.trim().replace(/[%+]/g, "");
        const aNum  = parseFloat(aText);
        const bNum  = parseFloat(bText);
        const cmp   = isNaN(aNum) || isNaN(bNum)
          ? aText.localeCompare(bText, "es")
          : aNum - bNum;
        return ascending ? cmp : -cmp;
      });

      rows.forEach(r => tbody.appendChild(r));
    });
  });
}

/** Call after any dynamic table is inserted into DOM */
function initAllTables(container) {
  (container || document).querySelectorAll("table").forEach(t => initTableSort(t));
}

// ── Bootstrap ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  loadAllData();
});
