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

  const todayFx  = upcoming.filter(f => f.date === today);
  const futureFx = upcoming.filter(f => f.date >  today);

  let html = "";

  if (todayFx.length > 0) {
    html += `<div class="fx-section-title">${t("inicio_today")}</div>`;
    html += todayFx.map(f => buildFixtureCard(f, false)).join("");
  }

  if (futureFx.length > 0) {
    html += `<div class="fx-section-title">${t("inicio_upcoming")}</div>`;
    html += futureFx.map(f => buildFixtureCard(f, false)).join("");
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
    html += recent.map(f => buildFixtureCard(f, true)).join("");
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

function buildFixtureCard(f, isResult) {
  const leagueCls   = f.league ? f.league.toLowerCase().replace(/\d/g, "") : "other";
  const leagueLabel = APP.leagues?.[f.league]?.name || f.league || "—";
  const dateLabel   = fxDateLabel(f.date, f.time);

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
    const odds = [];
    if (f.odds_home  != null) odds.push(`<div class="fx-odd"><span>1</span><strong>${f.odds_home}</strong></div>`);
    if (f.odds_draw  != null) odds.push(`<div class="fx-odd"><span>X</span><strong>${f.odds_draw}</strong></div>`);
    if (f.odds_away  != null) odds.push(`<div class="fx-odd"><span>2</span><strong>${f.odds_away}</strong></div>`);
    if (f.odds_over25 != null) odds.push(`<div class="fx-odd"><span>O2.5</span><strong>${f.odds_over25}</strong></div>`);
    if (odds.length) mainContent = `<div class="fx-odds">${odds.join("")}</div>`;
  }

  const analyzeBtn = !isResult
    ? `<button class="fx-analyze-btn" data-home="${escHtml(f.home)}" data-away="${escHtml(f.away)}">${t("inicio_analyze")} →</button>`
    : "";

  return `
  <div class="fx-card">
    <div class="fx-row">
      <span class="fx-league-badge ${leagueCls}">${leagueLabel}</span>
      <span class="fx-date">${dateLabel}</span>
    </div>
    <div class="fx-row fx-main">
      <div class="fx-teams">
        <span class="fx-team">${escHtml(f.home)}</span>
        <span class="fx-vs">vs</span>
        <span class="fx-team">${escHtml(f.away)}</span>
      </div>
      ${mainContent}
    </div>
    ${analyzeBtn ? `<div class="fx-actions">${analyzeBtn}</div>` : ""}
  </div>`;
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
