/**
 * inicio.js — Tab "Inicio": calendario, próximos partidos, resultados recientes
 */

"use strict";

function initInicio() {
  renderInicio("all");
}

function renderInicio(leagueFilter) {
  const box = document.getElementById("inicio-result");
  if (!box) return;

  const league   = leagueFilter || "all";
  const fixtures = APP.fixtures || { recent: [], upcoming: [] };
  const today    = new Date().toISOString().slice(0, 10);

  let upcoming = (fixtures.upcoming || []).slice();
  let recent   = (fixtures.recent   || []).slice();

  if (league !== "all") {
    upcoming = upcoming.filter(f => f.league === league);
    recent   = recent.filter(f => f.league === league);
  }

  let html = "";
  const totalUpcoming = upcoming.length;
  const nextDate = upcoming[0]?.date;
  const leagueCount = new Set(upcoming.map(f => f.league)).size;
  if (totalUpcoming > 0) {
    html += `
    <div class="calendar-summary">
      <div class="calendar-summary-item"><strong>${totalUpcoming}</strong><span>próximos</span></div>
      <div class="calendar-summary-item"><strong>${leagueCount}</strong><span>ligas</span></div>
      <div class="calendar-summary-item"><strong>${nextDate ? fxDateLabel(nextDate, "") : "—"}</strong><span>siguiente</span></div>
    </div>`;
  }

  if (upcoming.length > 0) {
    html += `<div class="fx-section-title">${t("inicio_upcoming")}</div>`;
    html += buildCalendarAgenda(upcoming, false);
  }

  if (upcoming.length === 0) {
    html += `
    <div class="card" style="margin-bottom:20px;padding:28px 24px;text-align:center;">
      <div style="font-size:2rem;margin-bottom:10px;">📅</div>
      <p style="color:var(--muted);font-size:.9rem;line-height:1.6;max-width:500px;margin:0 auto;">
        ${t("inicio_no_upcoming")}
      </p>
    </div>`;
  }

  if (recent.length > 0) {
    html += `<div class="fx-section-title">${t("inicio_recent")}</div>`;
    html += buildCalendarAgenda(recent.slice(0, 24), true);
  }

  if (!html) {
    html = `<div class="state-box"><p>Sin datos disponibles</p></div>`;
  }

  box.innerHTML = html;

  // Wire Analizar buttons → navigate to Comparador with pre-loaded teams
  box.querySelectorAll(".fx-analyze-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const home = btn.dataset.home;
      const away = btn.dataset.away;

      // Switch to comparador tab
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      const cmpBtn = document.querySelector(".tab-btn[data-tab='comparador']");
      if (cmpBtn) cmpBtn.classList.add("active");
      const cmpPanel = document.getElementById("tab-comparador");
      if (cmpPanel) cmpPanel.classList.add("active");

      // Reset league filter to "all" so both teams are available in the selects
      const leagueFilter = document.getElementById("cmpLeagueFilter");
      if (leagueFilter) leagueFilter.value = "all";
      if (typeof populateSelect === "function") {
        populateSelect("cmp-home", APP.teams);
        populateSelect("cmp-away", APP.teams);
      }

      // Pre-load teams in selects
      const homeEl = document.getElementById("cmp-home");
      const awayEl = document.getElementById("cmp-away");
      if (homeEl) homeEl.value = home;
      if (awayEl) awayEl.value = away;

      // Scroll to top and run analysis
      window.scrollTo({ top: 0, behavior: "smooth" });
      if (typeof runComparador === "function") runComparador();
    });
  });
}

function buildCalendarAgenda(fixtures, isResult) {
  const byDate = new Map();
  fixtures.forEach(f => {
    if (!byDate.has(f.date)) byDate.set(f.date, []);
    byDate.get(f.date).push(f);
  });

  return Array.from(byDate.entries()).map(([date, dayFixtures]) => {
    const byLeague = new Map();
    sortFixtures(dayFixtures).forEach(f => {
      const key = f.league || "other";
      if (!byLeague.has(key)) byLeague.set(key, []);
      byLeague.get(key).push(f);
    });
    const leagueBlocks = Array.from(byLeague.entries()).map(([league, items]) => {
      const label = typeof getLeagueLabel === "function"
        ? getLeagueLabel(league)
        : (APP.leagues?.[league]?.name || league);
      return `
      <div class="calendar-league-block">
        <div class="calendar-league-head">
          <span>${escHtml(label)}</span>
          <strong>${items.length}</strong>
        </div>
        ${items.map(f => buildFixtureCard(f, isResult)).join("")}
      </div>`;
    }).join("");

    return `
    <section class="calendar-day">
      <div class="calendar-day-head">
        <span>${fxDateLabel(date, "")}</span>
        <strong>${dayFixtures.length} partidos</strong>
      </div>
      ${leagueBlocks}
    </section>`;
  }).join("");
}

function sortFixtures(fixtures) {
  return fixtures.slice().sort((a, b) => {
    const leagueCmp = typeof compareLeagueCodes === "function"
      ? compareLeagueCodes(a.league, b.league)
      : String(a.league || "").localeCompare(String(b.league || ""));
    if (leagueCmp !== 0) return leagueCmp;
    return String(a.time || "").localeCompare(String(b.time || ""));
  });
}

function buildFixtureCard(f, isResult) {
  const leagueCls   = f.league ? f.league.toLowerCase().replace(/\d/g, "") : "other";
  const leagueLabel = APP.leagues?.[f.league]?.name || f.league || "—";
  const dateLabel   = fxDateLabel(f.date, f.time);
  const fixtureEdges = typeof getFixtureEdges === "function" ? getFixtureEdges(f) : [];
  const topEdge = fixtureEdges.slice().sort((a, b) => (b.edge_pct || 0) - (a.edge_pct || 0))[0];
  const edgeBadge = topEdge ? `
      <span class="fx-edge-badge" title="${escHtml(topEdge.selection)} · Bet365 ${escHtml(topEdge.odds)}">
        ${typeof formatEdgePercent === "function" ? formatEdgePercent(topEdge.edge_pct) : `+${topEdge.edge_pct}%`} EDGE
      </span>` : "";

  let mainContent = "";

  if (isResult) {
    const homeWon = f.home_score > f.away_score;
    const awayWon = f.away_score > f.home_score;
    mainContent = `
      <div class="fx-score">
        <span class="${homeWon ? "fx-score-win" : ""}">${f.home_score}</span>
        <span class="fx-score-sep">–</span>
        <span class="${awayWon ? "fx-score-win" : ""}">${f.away_score}</span>
      </div>`;
  } else {
    const round = f.round ? `<span>J${escHtml(f.round)}</span>` : "";
    const venue = f.venue ? `<span>${escHtml(f.venue)}</span>` : "";
    mainContent = `<div class="fx-meta">${round}${venue}<span>Previa disponible</span></div>`;
  }

  const analyzeBtn = !isResult
    ? `<button class="fx-analyze-btn" data-home="${escHtml(f.home)}" data-away="${escHtml(f.away)}">${t("inicio_analyze")} →</button>`
    : "";
  const matchBtn = `<a class="fx-match-btn" href="${buildMatchHref(f)}">Ficha</a>`;

  return `
  <div class="fx-card">
    <div class="fx-row">
      <span class="fx-league-badge ${leagueCls}">${leagueLabel}</span>
      <span class="fx-date">${dateLabel}</span>
      ${edgeBadge}
    </div>
    <div class="fx-row fx-main">
      <div class="fx-teams">
        <span class="fx-team">${escHtml(f.home)}</span>
        <span class="fx-vs">vs</span>
        <span class="fx-team">${escHtml(f.away)}</span>
      </div>
      ${mainContent}
    </div>
    <div class="fx-actions">${matchBtn}${analyzeBtn || ""}</div>
  </div>`;
}

function buildMatchHref(f) {
  const params = new URLSearchParams({
    league: f.league || "",
    date: f.date || "",
    home: f.home || "",
    away: f.away || "",
  });
  return `match.html?${params.toString()}`;
}

function fxDateLabel(dateStr, timeStr) {
  if (!dateStr) return "—";
  const today    = new Date().toISOString().slice(0, 10);
  const diffDays = Math.round(
    (new Date(dateStr) - new Date(today)) / 86400000
  );

  let label;
  const loc = typeof LANG !== "undefined" && LANG === "en" ? "en-GB" : "es-ES";
  if (diffDays === 0)       label = loc === "en-GB" ? "Today" : "Hoy";
  else if (diffDays === 1)  label = loc === "en-GB" ? "Tomorrow" : "Mañana";
  else if (diffDays === -1) label = loc === "en-GB" ? "Yesterday" : "Ayer";
  else {
    label = new Date(dateStr + "T12:00:00").toLocaleDateString(loc, {
      weekday: "short", day: "numeric", month: "short"
    });
  }

  if (timeStr && timeStr !== "nan" && timeStr !== "") label += ` · ${timeStr}`;
  return label;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
