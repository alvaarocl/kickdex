/**
 * inicio.js — Tab "Inicio": calendario, próximos partidos, resultados recientes
 */

"use strict";

const INICIO_PAGE_SIZE = 60;
const INICIO_STATE = {
  league: "all",
  view: "upcoming",
  round: "all",
  month: "all",
  visible: INICIO_PAGE_SIZE,
};

function initInicio() {
  [
    ["inicioCalendarView", "view"],
    ["inicioRoundFilter", "round"],
    ["inicioMonthFilter", "month"],
  ].forEach(([id, key]) => {
    const select = document.getElementById(id);
    if (!select || select.dataset.calendarBound === "1") return;
    select.dataset.calendarBound = "1";
    select.addEventListener("change", () => {
      INICIO_STATE[key] = select.value;
      INICIO_STATE.visible = INICIO_PAGE_SIZE;
      renderInicio(document.getElementById("inicioLeagueFilter")?.value || "all");
    });
  });
  renderInicio(document.getElementById("inicioLeagueFilter")?.value || "all");
}

function renderInicio(leagueFilter) {
  const box = document.getElementById("inicio-result");
  if (!box) return;

  const league   = leagueFilter || "all";
  const fixtures = APP.fixtures || { recent: [], upcoming: [] };
  const today    = new Date().toISOString().slice(0, 10);
  if (league !== INICIO_STATE.league) {
    INICIO_STATE.league = league;
    INICIO_STATE.visible = INICIO_PAGE_SIZE;
  }

  let selected = getCompleteCalendar(fixtures);
  if (INICIO_STATE.view === "upcoming") {
    selected = selected.filter(f => !isFixtureResult(f) && f.date >= today);
  } else if (INICIO_STATE.view === "results") {
    selected = selected.filter(isFixtureResult);
  }
  if (league !== "all") selected = selected.filter(f => f.league === league);

  refreshCalendarOptions(selected);
  if (INICIO_STATE.round !== "all") {
    selected = selected.filter(f => String(f.round || "") === INICIO_STATE.round);
  }
  if (INICIO_STATE.month !== "all") {
    selected = selected.filter(f => String(f.date || "").slice(0, 7) === INICIO_STATE.month);
  }

  selected.sort((a, b) => {
    const value = `${a.date || ""}T${a.time || "00:00"}`.localeCompare(
      `${b.date || ""}T${b.time || "00:00"}`
    );
    return INICIO_STATE.view === "results" ? -value : value;
  });

  const total = selected.length;
  const visible = selected.slice(0, INICIO_STATE.visible);
  const leagueCount = new Set(selected.map(f => f.league)).size;
  const sourceLeagues = APP.fixtures?.meta?.fixture_download?.leagues || {};
  const completeLeagues = Object.entries(sourceLeagues)
    .filter(([, info]) => info?.ok && info?.total)
    .map(([code]) => code);
  const isEnglish = typeof LANG !== "undefined" && LANG === "en";
  let coverageHint = "";
  if (league !== "all") {
    coverageHint = completeLeagues.includes(league)
      ? (isEnglish ? "Complete home-and-away calendar." : "Calendario completo de ida y vuelta.")
      : (isEnglish
        ? "This league currently shows only the matches published by the available feed."
        : "Esta liga muestra por ahora solo los partidos publicados por el feed disponible.");
  } else {
    coverageHint = isEnglish
      ? `${completeLeagues.length} leagues have a complete season calendar; the rest show available matches.`
      : `${completeLeagues.length} ligas tienen calendario completo; el resto muestra los partidos disponibles.`;
  }
  const viewLabel = INICIO_STATE.view === "full"
    ? t("inicio_view_full")
    : INICIO_STATE.view === "results"
      ? t("inicio_view_results")
      : t("inicio_view_upcoming");

  let html = `
    <div class="calendar-summary">
      <div class="calendar-summary-item"><strong>${total.toLocaleString()}</strong><span>${viewLabel}</span></div>
      <div class="calendar-summary-item"><strong>${leagueCount}</strong><span>ligas</span></div>
      <div class="calendar-summary-item"><strong>${escHtml(APP.meta?.season || "2026/27")}</strong><span>temporada</span></div>
    </div>
    <p class="calendar-results-note">Mostrando ${Math.min(visible.length, total).toLocaleString()} de ${total.toLocaleString()} partidos. ${coverageHint}</p>
  `;

  if (visible.length) {
    html += `<div class="fx-section-title">${viewLabel}</div>`;
    html += buildCalendarAgenda(visible, null);
    if (visible.length < total) {
      html += `
        <div class="calendar-load-more">
          <button class="btn btn-secondary" id="inicioLoadMore">${t("inicio_load_more")} · ${total - visible.length}</button>
        </div>`;
    }
  } else {
    html += `
      <div class="card" style="margin-bottom:20px;padding:28px 24px;text-align:center;">
        <div style="font-size:2rem;margin-bottom:10px;">📅</div>
        <p style="color:var(--muted);font-size:.9rem;line-height:1.6;max-width:500px;margin:0 auto;">
          No hay partidos para esta combinación de filtros.
        </p>
      </div>`;
  }

  box.innerHTML = html;

  const loadMore = document.getElementById("inicioLoadMore");
  if (loadMore) {
    loadMore.addEventListener("click", () => {
      INICIO_STATE.visible += INICIO_PAGE_SIZE;
      renderInicio(INICIO_STATE.league);
    });
  }

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

function getCompleteCalendar(fixtures) {
  if ((fixtures.calendar || []).length) return fixtures.calendar.slice();
  const merged = new Map();
  [...(fixtures.recent || []), ...(fixtures.upcoming || [])].forEach(f => {
    merged.set(`${f.league}|${f.date}|${f.home}|${f.away}`, f);
  });
  return Array.from(merged.values());
}

function isFixtureResult(fixture) {
  return fixture.home_score !== undefined && fixture.away_score !== undefined;
}

function refreshCalendarOptions(fixtures) {
  const rounds = Array.from(new Set(
    fixtures.map(f => f.round).filter(value => value !== null && value !== undefined && value !== "")
  )).sort((a, b) => Number(a) - Number(b));
  const months = Array.from(new Set(
    fixtures.map(f => String(f.date || "").slice(0, 7)).filter(value => /^\d{4}-\d{2}$/.test(value))
  )).sort();

  INICIO_STATE.round = replaceCalendarOptions(
    "inicioRoundFilter",
    INICIO_STATE.round,
    t("inicio_round_all"),
    rounds.map(value => [String(value), `Jornada ${value}`])
  );
  INICIO_STATE.month = replaceCalendarOptions(
    "inicioMonthFilter",
    INICIO_STATE.month,
    t("inicio_month_all"),
    months.map(value => [value, calendarMonthLabel(value)])
  );
}

function replaceCalendarOptions(id, selected, allLabel, options) {
  const select = document.getElementById(id);
  if (!select) return selected;
  select.innerHTML = "";
  const all = document.createElement("option");
  all.value = "all";
  all.textContent = allLabel;
  select.appendChild(all);
  options.forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  });
  const next = options.some(([value]) => value === selected) ? selected : "all";
  select.value = next;
  return next;
}

function calendarMonthLabel(value) {
  const loc = typeof LANG !== "undefined" && LANG === "en" ? "en-GB" : "es-ES";
  const [year, month] = value.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString(loc, {
    month: "long",
    year: "numeric",
  });
}

function buildCalendarAgenda(fixtures, isResult = null) {
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
        ${items.map(f => buildFixtureCard(f, isResult === null ? isFixtureResult(f) : isResult)).join("")}
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
  const topEdgeSelection = topEdge && (topEdge.selection === topEdge.home || topEdge.selection === topEdge.away)
    ? teamDisplayName(topEdge.selection)
    : topEdge?.selection;
  const edgeBadge = topEdge ? `
      <span class="fx-edge-badge" title="${escHtml(topEdgeSelection)} · Bet365 ${escHtml(topEdge.odds)}">
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
        <span class="fx-team">${typeof entityMedia === "function" ? entityMedia("team", f.home) : ""}<b>${escHtml(teamDisplayName(f.home))}</b></span>
        <span class="fx-vs">vs</span>
        <span class="fx-team">${typeof entityMedia === "function" ? entityMedia("team", f.away) : ""}<b>${escHtml(teamDisplayName(f.away))}</b></span>
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
