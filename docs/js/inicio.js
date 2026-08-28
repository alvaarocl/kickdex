/**
 * inicio.js — Tab "Inicio": calendario, próximos partidos, resultados recientes
 * FASE 1 — fixture-first (fila densa) · 2026-08-28
 */

"use strict";

const INICIO_PAGE_SIZE = 60;
const INICIO_STATE = {
  league:  "all",
  view:    "upcoming",
  round:   "all",
  month:   "all",
  date:    "all",        // day-strip filter: "all" | "YYYY-MM-DD"
  visible: INICIO_PAGE_SIZE,
};

// ── Numeric format helper ─────────────────────────────────────────────────

function _fxFmt(val, decimals) {
  if (val === null || val === undefined) return "—";
  var n = Number(val);
  if (!isFinite(n) || n !== n) return "—";
  return n.toFixed(decimals !== undefined ? decimals : 1);
}

// ── Team stats helpers ────────────────────────────────────────────────────

function _fxTeamStats(team, venue) {
  return (APP.teamStats && APP.teamStats[team] && APP.teamStats[team][venue]) || null;
}

function _fxTeamForm(team, venue) {
  var stats = _fxTeamStats(team, venue);
  if (!stats || !Array.isArray(stats.match_log) || stats.match_log.length === 0) return [];
  return stats.match_log.slice(-5).map(function (m) {
    return (m.result || "").toUpperCase();
  });
}

// Build compact form dots string (8px, no outer margin)
function _fxFormDots(results) {
  if (!results || results.length === 0) {
    return '<span class="fx-dr-dash">—</span>';
  }
  // Pad to 5 on the left with empties (oldest → newest)
  var padded = [];
  for (var p = 0; p < Math.max(0, 5 - results.length); p++) padded.push(null);
  padded = padded.concat(results.slice(-5));

  return padded.map(function (r) {
    if (!r) return '<span class="fx-dr-dot fx-dr-dot-empty" aria-hidden="true"></span>';
    var cls   = r === "W" ? "w" : r === "D" ? "d" : "l";
    var label = r === "W" ? "Victoria" : r === "D" ? "Empate" : "Derrota";
    return '<span class="fx-dr-dot ' + cls + '" title="' + label + '"></span>';
  }).join("");
}

// Build 5 stat cells for a grid row
function _fxStatCells(stats) {
  function cell(label, title, val) {
    return '<span class="fx-dr-val' + (val === "—" ? " fx-dr-val--dash" : "") + '" data-label="' + label + '" title="' + title + '">' + val + '</span>';
  }
  if (!stats) {
    return cell("GF",   "Goles marcados/p",  "—") +
           cell("GC",   "Goles encajados/p", "—") +
           cell("TIR",  "Tiros/p",           "—") +
           cell("CÓR",  "Córners/p",         "—") +
           cell("TARJ", "Tarjetas/p",        "—");
  }
  return cell("GF",   "Goles marcados/p",  _fxFmt(stats.avg_goals)) +
         cell("GC",   "Goles encajados/p", _fxFmt(stats.avg_goals_against)) +
         cell("TIR",  "Tiros/p",           _fxFmt(stats.avg_shots)) +
         cell("CÓR",  "Córners/p",         _fxFmt(stats.avg_corners)) +
         cell("TARJ", "Tarjetas/p",        _fxFmt(stats.avg_cards));
}

// ── Trend helpers ─────────────────────────────────────────────────────────

// Returns the trend with highest rate from home trends of home team
// and away trends of away team. Returns null if no trends available.
function getBestTrend(homeTeam, awayTeam) {
  if (!APP.trends || !APP.trends.teams) return null;
  var homeData = APP.trends.teams[homeTeam];
  var awayData = APP.trends.teams[awayTeam];
  var all = (homeData && homeData.home ? homeData.home : [])
    .concat(awayData && awayData.away ? awayData.away : []);
  if (all.length === 0) return null;
  return all.reduce(function (best, t) {
    return (t.rate || 0) > (best.rate || 0) ? t : best;
  });
}

// ── Radar de la jornada ────────────────────────────────────────────────────

function buildJornadaRadar(fixtures) {
  // Only fixtures with both teams in team_stats
  var withStats = fixtures.filter(function (f) {
    return APP.teamStats && APP.teamStats[f.home] && APP.teamStats[f.away];
  });
  if (withStats.length === 0) return "";

  // 1. Mayor media goleadora (GF home + GF away)
  var topGoal = { sum: -1, f: null };
  withStats.forEach(function (f) {
    var hg = ((APP.teamStats[f.home].home || {}).avg_goals) || 0;
    var ag = ((APP.teamStats[f.away].away || {}).avg_goals) || 0;
    if (hg + ag > topGoal.sum) { topGoal.sum = hg + ag; topGoal.f = f; }
  });

  // 2. Tendencia más fuerte (highest rate across all matchups)
  var topTrend = null, topTrendFx = null;
  withStats.forEach(function (f) {
    var t = getBestTrend(f.home, f.away);
    if (t && (!topTrend || t.rate > topTrend.rate)) { topTrend = t; topTrendFx = f; }
  });

  // 3. Mayor riesgo de tarjetas (cards home + cards away)
  var topCards = { sum: -1, f: null };
  withStats.forEach(function (f) {
    var hc = ((APP.teamStats[f.home].home || {}).avg_cards) || 0;
    var ac = ((APP.teamStats[f.away].away || {}).avg_cards) || 0;
    if (hc + ac > topCards.sum) { topCards.sum = hc + ac; topCards.f = f; }
  });

  var cards = [];

  if (topGoal.f) {
    var hn = typeof teamDisplayName === "function" ? teamDisplayName(topGoal.f.home) : topGoal.f.home;
    var an = typeof teamDisplayName === "function" ? teamDisplayName(topGoal.f.away) : topGoal.f.away;
    var hgv = _fxFmt((APP.teamStats[topGoal.f.home].home || {}).avg_goals);
    var agv = _fxFmt((APP.teamStats[topGoal.f.away].away || {}).avg_goals);
    cards.push(_buildRadarCard(
      "Mayor media goleadora",
      _fxFmt(topGoal.sum) + " esp.",
      escHtml(hn) + " vs " + escHtml(an),
      escHtml(hgv) + " + " + escHtml(agv) + " goles/p",
      "⚽",
      buildMatchHref(topGoal.f)
    ));
  }

  if (topTrend && topTrendFx) {
    var pct     = Math.round(topTrend.rate * 100);
    var hitsStr = topTrend.hits + "/" + topTrend.window;
    var tTeam   = topTrend.team
      ? (typeof teamDisplayName === "function" ? teamDisplayName(topTrend.team) : topTrend.team)
      : "";
    cards.push(_buildRadarCard(
      "Tendencia más fuerte",
      pct + "% (" + hitsStr + ")",
      escHtml(tTeam),
      escHtml(topTrend.text || ""),
      "↗",
      buildMatchHref(topTrendFx)
    ));
  }

  if (topCards.f) {
    var hn2 = typeof teamDisplayName === "function" ? teamDisplayName(topCards.f.home) : topCards.f.home;
    var an2 = typeof teamDisplayName === "function" ? teamDisplayName(topCards.f.away) : topCards.f.away;
    var hcv = _fxFmt((APP.teamStats[topCards.f.home].home || {}).avg_cards);
    var acv = _fxFmt((APP.teamStats[topCards.f.away].away || {}).avg_cards);
    cards.push(_buildRadarCard(
      "Mayor riesgo tarjetas",
      _fxFmt(topCards.sum) + " tarj/p",
      escHtml(hn2) + " vs " + escHtml(an2),
      escHtml(hcv) + " + " + escHtml(acv) + " tarj/p",
      "🟨",
      buildMatchHref(topCards.f)
    ));
  }

  if (cards.length === 0) return "";
  return '<div class="fx-radar-grid">' + cards.join("") + '</div>' + _buildEdgeBacktestLine();
}

// Prueba retrospectiva del modelo de edge (edges.json stats). Honesto: es
// backtest sobre cuotas de cierre, no un histórico de aciertos "en vivo".
function _buildEdgeBacktestLine() {
  var s = (APP.edges && APP.edges.stats) || {};
  var evaluated = Number(s.evaluated_matches || 0);
  var positive  = Number(s.positive_edges || 0);
  var upcoming   = Number(s.upcoming_edges || 0);
  if (!evaluated && !positive) return "";
  var hits = (APP.edges.items || []).filter(function (x) {
    return x.result && x.result.hit === true;
  }).length;
  var settled = (APP.edges.items || []).filter(function (x) {
    return x.result && x.result.hit != null;
  }).length;
  var hitRate = settled ? Math.round(hits / settled * 100) : null;
  var parts = [];
  if (settled) parts.push('<b>' + hits + '/' + settled + '</b> edges acertados en backtest' + (hitRate != null ? ' (' + hitRate + '%)' : ''));
  parts.push(evaluated.toLocaleString('es-ES') + ' partidos evaluados');
  if (upcoming) parts.push('<b class="text-gold">' + upcoming + '</b> edges en próximos partidos');
  else parts.push('sin cuotas de partidos futuros (edge solo retrospectivo)');
  return '<p class="fx-edge-backtest muted">' + parts.join(' · ') +
    ' — <a href="methodology.html">metodología</a></p>';
}

function _buildRadarCard(title, value, desc, sub, icon, href) {
  return '<a class="fx-radar-card card" href="' + escHtml(href) + '">' +
    '<div class="fx-radar-icon" aria-hidden="true">' + icon + '</div>' +
    '<div class="card-title">' + escHtml(title) + '</div>' +
    '<div class="card-value">' + escHtml(value) + '</div>' +
    '<div class="card-sub">' + desc + '</div>' +
    '<div class="fx-radar-sub2">' + sub + '</div>' +
  '</a>';
}

// ── Day strip ─────────────────────────────────────────────────────────────

function buildDayStrip() {
  var today = new Date();
  var dayNames   = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

  // Build list: yesterday + today + next 4 days
  var days = [];
  for (var i = -1; i <= 4; i++) {
    var d = new Date(today);
    d.setDate(today.getDate() + i);
    var iso = d.toISOString().slice(0, 10);
    var label;
    if      (i === -1) label = "Ayer";
    else if (i ===  0) label = "Hoy";
    else if (i ===  1) label = "Mañana";
    else               label = dayNames[d.getDay()] + " " + d.getDate();
    days.push({ iso: iso, label: label });
  }

  var html = '<div class="day-strip" role="group" aria-label="Filtrar por día">';
  html += '<button class="day-strip-btn' + (INICIO_STATE.date === "all" ? " active" : "") +
    '" data-strip-date="all" type="button">Todos</button>';
  days.forEach(function (d) {
    var active = INICIO_STATE.date === d.iso ? " active" : "";
    html += '<button class="day-strip-btn' + active +
      '" data-strip-date="' + d.iso + '" type="button">' + escHtml(d.label) + '</button>';
  });
  html += '</div>';
  return html;
}

function _initDayStrip(container) {
  container.querySelectorAll("[data-strip-date]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var date = btn.dataset.stripDate;
      INICIO_STATE.date    = date;
      INICIO_STATE.visible = INICIO_PAGE_SIZE;
      // When picking a specific day, switch to full view so both results
      // and upcoming matches on that day are shown.
      if (date !== "all" && INICIO_STATE.view === "upcoming") {
        INICIO_STATE.view = "full";
        var viewSel = document.getElementById("inicioCalendarView");
        if (viewSel) viewSel.value = "full";
      }
      renderInicio(INICIO_STATE.league);
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────

function initInicio() {
  [
    ["inicioCalendarView", "view"],
    ["inicioRoundFilter",  "round"],
    ["inicioMonthFilter",  "month"],
  ].forEach(function (pair) {
    var id = pair[0], key = pair[1];
    var select = document.getElementById(id);
    if (!select || select.dataset.calendarBound === "1") return;
    select.dataset.calendarBound = "1";
    select.addEventListener("change", function () {
      INICIO_STATE[key]    = select.value;
      INICIO_STATE.visible = INICIO_PAGE_SIZE;
      // Changing view/round/month clears the day filter
      if (key === "view") INICIO_STATE.date = "all";
      renderInicio(document.getElementById("inicioLeagueFilter")?.value || "all");
    });
  });
  renderInicio(document.getElementById("inicioLeagueFilter")?.value || "all");
}

// ── Render ────────────────────────────────────────────────────────────────

function renderInicio(leagueFilter) {
  var box = document.getElementById("inicio-result");
  if (!box) return;

  var league   = leagueFilter || "all";
  var fixtures = APP.fixtures || { recent: [], upcoming: [] };
  var today    = new Date().toISOString().slice(0, 10);

  if (league !== INICIO_STATE.league) {
    INICIO_STATE.league  = league;
    INICIO_STATE.visible = INICIO_PAGE_SIZE;
  }

  var selected = getCompleteCalendar(fixtures);

  if (INICIO_STATE.view === "upcoming") {
    selected = selected.filter(function (f) { return !isFixtureResult(f) && f.date >= today; });
  } else if (INICIO_STATE.view === "results") {
    selected = selected.filter(isFixtureResult);
  }
  if (league !== "all") selected = selected.filter(function (f) { return f.league === league; });

  refreshCalendarOptions(selected);

  if (INICIO_STATE.round !== "all") {
    selected = selected.filter(function (f) { return String(f.round || "") === INICIO_STATE.round; });
  }
  if (INICIO_STATE.month !== "all") {
    selected = selected.filter(function (f) { return String(f.date || "").slice(0, 7) === INICIO_STATE.month; });
  }
  // Day strip filter (takes precedence over month)
  if (INICIO_STATE.date !== "all") {
    selected = selected.filter(function (f) { return f.date === INICIO_STATE.date; });
  }

  selected.sort(function (a, b) {
    var v = (String(a.date) + "T" + String(a.time || "00:00"))
      .localeCompare(String(b.date) + "T" + String(b.time || "00:00"));
    return INICIO_STATE.view === "results" ? -v : v;
  });

  var total   = selected.length;
  var visible = selected.slice(0, INICIO_STATE.visible);

  var leagueCount    = new Set(selected.map(function (f) { return f.league; })).size;
  var sourceLeagues  = (APP.fixtures && APP.fixtures.meta && APP.fixtures.meta.fixture_download && APP.fixtures.meta.fixture_download.leagues) || {};
  var completeLeagues = Object.keys(sourceLeagues).filter(function (k) {
    return sourceLeagues[k] && sourceLeagues[k].ok && sourceLeagues[k].total;
  });
  var isEnglish = typeof LANG !== "undefined" && LANG === "en";
  var coverageHint;
  if (league !== "all") {
    coverageHint = completeLeagues.indexOf(league) !== -1
      ? (isEnglish ? "Complete home-and-away calendar." : "Calendario completo de ida y vuelta.")
      : (isEnglish
          ? "This league currently shows only the matches published by the available feed."
          : "Esta liga muestra por ahora solo los partidos publicados por el feed disponible.");
  } else {
    coverageHint = isEnglish
      ? completeLeagues.length + " leagues have a complete season calendar; the rest show available matches."
      : completeLeagues.length + " ligas tienen calendario completo; el resto muestra los partidos disponibles.";
  }
  var viewLabel = INICIO_STATE.view === "full"
    ? t("inicio_view_full")
    : INICIO_STATE.view === "results"
      ? t("inicio_view_results")
      : t("inicio_view_upcoming");

  var html = "";

  // Day strip (always shown)
  html += buildDayStrip();

  // Summary row
  html += '<div class="calendar-summary">' +
    '<div class="calendar-summary-item"><strong>' + total.toLocaleString() + '</strong><span>' + escHtml(viewLabel) + '</span></div>' +
    '<div class="calendar-summary-item"><strong>' + leagueCount + '</strong><span>ligas</span></div>' +
    '<div class="calendar-summary-item"><strong>' + escHtml((APP.meta && APP.meta.season) || "2026/27") + '</strong><span>temporada</span></div>' +
    '</div>';

  html += '<p class="calendar-results-note">Mostrando ' +
    Math.min(visible.length, total).toLocaleString() + ' de ' + total.toLocaleString() +
    ' partidos. ' + escHtml(coverageHint) + '</p>';

  // Radar de la jornada (upcoming fixtures only, not results view)
  if (INICIO_STATE.view !== "results" && visible.length > 0) {
    var upcomingVisible = visible.filter(function (f) { return !isFixtureResult(f); });
    var radarHtml = buildJornadaRadar(upcomingVisible);
    if (radarHtml) {
      html += '<section class="fx-radar-section">' +
        '<h3 class="fx-radar-title">Radar de la jornada</h3>' +
        radarHtml +
        '</section>';
    }
  }

  if (visible.length) {
    html += '<div class="fx-section-title">' + escHtml(viewLabel) + '</div>';
    html += buildCalendarAgenda(visible, null);
    if (visible.length < total) {
      html += '<div class="calendar-load-more">' +
        '<button class="btn btn-secondary" id="inicioLoadMore" type="button">' +
        t("inicio_load_more") + " · " + (total - visible.length) +
        '</button></div>';
    }
  } else {
    html += '<div class="card" style="margin-bottom:20px;padding:28px 24px;text-align:center;">' +
      '<div style="font-size:2rem;margin-bottom:10px;">📅</div>' +
      '<p style="color:var(--muted);font-size:.9rem;line-height:1.6;max-width:500px;margin:0 auto;">' +
      'No hay partidos para esta combinación de filtros.' +
      '</p></div>';
  }

  box.innerHTML = html;

  // Wire day strip
  var strip = box.querySelector(".day-strip");
  if (strip) _initDayStrip(strip);

  // Load-more button
  var loadMore = document.getElementById("inicioLoadMore");
  if (loadMore) {
    loadMore.addEventListener("click", function () {
      INICIO_STATE.visible += INICIO_PAGE_SIZE;
      renderInicio(INICIO_STATE.league);
    });
  }
}

// ── Calendar structure ────────────────────────────────────────────────────

function getCompleteCalendar(fixtures) {
  if ((fixtures.calendar || []).length) return fixtures.calendar.slice();
  var merged = new Map();
  var combined = (fixtures.recent || []).concat(fixtures.upcoming || []);
  combined.forEach(function (f) {
    merged.set(f.league + "|" + f.date + "|" + f.home + "|" + f.away, f);
  });
  return Array.from(merged.values());
}

function isFixtureResult(fixture) {
  return fixture.home_score !== undefined && fixture.away_score !== undefined;
}

function refreshCalendarOptions(fixtures) {
  var rounds = Array.from(new Set(
    fixtures.map(function (f) { return f.round; })
      .filter(function (v) { return v !== null && v !== undefined && v !== ""; })
  )).sort(function (a, b) { return Number(a) - Number(b); });

  var months = Array.from(new Set(
    fixtures.map(function (f) { return String(f.date || "").slice(0, 7); })
      .filter(function (v) { return /^\d{4}-\d{2}$/.test(v); })
  )).sort();

  INICIO_STATE.round = replaceCalendarOptions(
    "inicioRoundFilter",
    INICIO_STATE.round,
    t("inicio_round_all"),
    rounds.map(function (v) { return [String(v), "Jornada " + v]; })
  );
  INICIO_STATE.month = replaceCalendarOptions(
    "inicioMonthFilter",
    INICIO_STATE.month,
    t("inicio_month_all"),
    months.map(function (v) { return [v, calendarMonthLabel(v)]; })
  );
}

function replaceCalendarOptions(id, selected, allLabel, options) {
  var select = document.getElementById(id);
  if (!select) return selected;
  select.innerHTML = "";
  var all = document.createElement("option");
  all.value = "all";
  all.textContent = allLabel;
  select.appendChild(all);
  options.forEach(function (pair) {
    var option = document.createElement("option");
    option.value = pair[0];
    option.textContent = pair[1];
    select.appendChild(option);
  });
  var next = options.some(function (pair) { return pair[0] === selected; }) ? selected : "all";
  select.value = next;
  return next;
}

function calendarMonthLabel(value) {
  var loc = typeof LANG !== "undefined" && LANG === "en" ? "en-GB" : "es-ES";
  var parts = value.split("-").map(Number);
  return new Date(parts[0], parts[1] - 1, 1).toLocaleDateString(loc, {
    month: "long",
    year: "numeric",
  });
}

// ── Calendar rendering ────────────────────────────────────────────────────

function buildCalendarAgenda(fixtures, isResult) {
  var byDate = new Map();
  fixtures.forEach(function (f) {
    if (!byDate.has(f.date)) byDate.set(f.date, []);
    byDate.get(f.date).push(f);
  });

  return Array.from(byDate.entries()).map(function (entry) {
    var date = entry[0], dayFixtures = entry[1];
    var byLeague = new Map();
    sortFixtures(dayFixtures).forEach(function (f) {
      var key = f.league || "other";
      if (!byLeague.has(key)) byLeague.set(key, []);
      byLeague.get(key).push(f);
    });

    var leagueBlocks = Array.from(byLeague.entries()).map(function (le) {
      var lg = le[0], items = le[1];
      var label = typeof getLeagueLabel === "function"
        ? getLeagueLabel(lg)
        : ((APP.leagues && APP.leagues[lg] && APP.leagues[lg].name) || lg);
      return '<div class="calendar-league-block">' +
        '<div class="calendar-league-head"><span>' + escHtml(label) + '</span><strong>' + items.length + '</strong></div>' +
        items.map(function (f) {
          return buildFixtureCard(f, isResult === null ? isFixtureResult(f) : isResult);
        }).join("") +
        '</div>';
    }).join("");

    return '<section class="calendar-day">' +
      '<div class="calendar-day-head"><span>' + escHtml(fxDateLabel(date, "")) + '</span><strong>' + dayFixtures.length + ' partidos</strong></div>' +
      leagueBlocks +
      '</section>';
  }).join("");
}

function sortFixtures(fixtures) {
  return fixtures.slice().sort(function (a, b) {
    var lc = typeof compareLeagueCodes === "function"
      ? compareLeagueCodes(a.league, b.league)
      : String(a.league || "").localeCompare(String(b.league || ""));
    if (lc !== 0) return lc;
    return String(a.time || "").localeCompare(String(b.time || ""));
  });
}

// ── Dense fixture card ─────────────────────────────────────────────────────
//
// UPCOMING: full dense row — form + 5 numeric stats per team + trend chip
// RESULT:   compact — team names + form + score + match button

function buildFixtureCard(f, isResult) {
  var leagueCls   = f.league ? f.league.toLowerCase().replace(/\d/g, "") : "other";
  var leagueLabel = (APP.leagues && APP.leagues[f.league] && APP.leagues[f.league].name) || f.league || "—";
  var timeLabel   = f.time && f.time !== "nan" ? f.time : "";
  var roundLabel  = f.round ? "J" + f.round : "";
  var metaParts   = [];
  if (timeLabel)  metaParts.push(timeLabel);
  if (roundLabel) metaParts.push(roundLabel);

  // Edge badge (carries over from existing logic)
  var fixtureEdges = typeof getFixtureEdges === "function" ? getFixtureEdges(f) : [];
  var topEdge = fixtureEdges
    .slice()
    .sort(function (a, b) { return (b.edge_pct || 0) - (a.edge_pct || 0); })[0];
  var edgeBadge = "";
  if (topEdge) {
    var edgeSrc = topEdge.odds_source
      ? "mejor cuota " + escHtml(String(topEdge.odds || ""))
      : "Bet365 cierre " + escHtml(String(topEdge.odds || ""));
    var conf = topEdge.confidence ? " · confianza " + escHtml(String(topEdge.confidence)) : "";
    edgeBadge = '<span class="fx-edge-badge" title="' + escHtml(String(topEdge.selection || "")) +
      " · " + edgeSrc + conf + '">' +
      (typeof formatEdgePercent === "function"
        ? formatEdgePercent(topEdge.edge_pct)
        : "+" + topEdge.edge_pct + "%") +
      " EDGE</span>";
  }

  var homeName  = typeof teamDisplayName === "function" ? teamDisplayName(f.home) : f.home;
  var awayName  = typeof teamDisplayName === "function" ? teamDisplayName(f.away) : f.away;
  var homeCrest = typeof entityMedia === "function" ? entityMedia("team", f.home) : "";
  var awayCrest = typeof entityMedia === "function" ? entityMedia("team", f.away) : "";

  var matchHref = buildMatchHref(f);

  // Shared card header
  var hd = '<div class="fx-dr-hd">' +
    '<span class="fx-league-badge ' + escHtml(leagueCls) + '">' + escHtml(leagueLabel) + '</span>' +
    (metaParts.length
      ? '<span class="fx-dr-meta">' + escHtml(metaParts.join(" · ")) + '</span>'
      : "") +
    edgeBadge +
    '</div>';

  // ── RESULT VARIANT ───────────────────────────────────────────
  if (isResult) {
    var homeWon = f.home_score > f.away_score;
    var awayWon = f.away_score > f.home_score;
    var homeForm = _fxTeamForm(f.home, "home");
    var awayForm = _fxTeamForm(f.away, "away");

    return '<div class="fx-card fx-dr-card fx-dr-card--result">' + hd +
      '<div class="fx-dr-res-body">' +
        '<div class="fx-dr-res-teams">' +
          '<div class="fx-dr-res-team">' +
            homeCrest +
            '<span class="fx-dr-name"><b>' + escHtml(homeName) + '</b></span>' +
            '<div class="fx-dr-form-wrap">' + _fxFormDots(homeForm) + '</div>' +
          '</div>' +
          '<div class="fx-dr-res-team">' +
            awayCrest +
            '<span class="fx-dr-name"><b>' + escHtml(awayName) + '</b></span>' +
            '<div class="fx-dr-form-wrap">' + _fxFormDots(awayForm) + '</div>' +
          '</div>' +
        '</div>' +
        '<div class="fx-dr-score">' +
          '<span class="' + (homeWon ? "fx-score-win" : "") + '">' + f.home_score + '</span>' +
          '<span class="fx-score-sep">–</span>' +
          '<span class="' + (awayWon ? "fx-score-win" : "") + '">' + f.away_score + '</span>' +
        '</div>' +
        '<a class="fx-dr-btn" href="' + matchHref + '" title="Ver ficha">→</a>' +
      '</div>' +
    '</div>';
  }

  // ── UPCOMING VARIANT (dense) ─────────────────────────────────
  var homeStats = _fxTeamStats(f.home, "home");
  var awayStats = _fxTeamStats(f.away, "away");
  var homeForm  = _fxTeamForm(f.home, "home");
  var awayForm  = _fxTeamForm(f.away, "away");

  // Trend chip: best trend from home team (home venue) or away team (away venue)
  var trendChip = "";
  var bestTrend = getBestTrend(f.home, f.away);
  if (bestTrend) {
    var icon     = bestTrend.rate >= 0.9 ? "↑" : "↗";
    var hitsStr  = bestTrend.hits + "/" + bestTrend.window;
    trendChip = '<span class="fx-dr-trend" title="' +
      escHtml(bestTrend.text || "") + " (" + escHtml(hitsStr) + ')">' +
      icon + " " + escHtml(bestTrend.text || "") +
      '</span>';
  }

  // Referee chip (null today; field is structural for future asignments)
  var refChip = "";
  if (f.referee) {
    var yellStr = (f.referee_yellows_per_match !== null && f.referee_yellows_per_match !== undefined)
      ? " 🟨" + _fxFmt(f.referee_yellows_per_match) + "/p"
      : "";
    refChip = '<span class="fx-dr-ref">⚖ ' + escHtml(f.referee) + escHtml(yellStr) + '</span>';
  }

  var footerInner = (trendChip || refChip)
    ? trendChip + refChip + '<a class="fx-dr-btn" href="' + matchHref + '" title="Ver ficha">→</a>'
    : '<a class="fx-dr-btn fx-dr-btn--alone" href="' + matchHref + '" title="Ver ficha">→</a>';

  return '<div class="fx-card fx-dr-card">' + hd +
    '<div class="fx-dr-grid">' +
      '<div class="fx-dr-col-hd" aria-hidden="true">' +
        '<span class="fx-dr-th-name"></span>' +
        '<span class="fx-dr-th fx-dr-th--form">FORMA</span>' +
        '<span class="fx-dr-th">GF</span>' +
        '<span class="fx-dr-th">GC</span>' +
        '<span class="fx-dr-th">TIR</span>' +
        '<span class="fx-dr-th">CÓR</span>' +
        '<span class="fx-dr-th">TARJ</span>' +
      '</div>' +
      '<div class="fx-dr-team-row">' +
        '<span class="fx-dr-name">' + homeCrest + '<b>' + escHtml(homeName) + '</b></span>' +
        '<div class="fx-dr-form-wrap">' + _fxFormDots(homeForm) + '</div>' +
        _fxStatCells(homeStats) +
      '</div>' +
      '<div class="fx-dr-team-row">' +
        '<span class="fx-dr-name">' + awayCrest + '<b>' + escHtml(awayName) + '</b></span>' +
        '<div class="fx-dr-form-wrap">' + _fxFormDots(awayForm) + '</div>' +
        _fxStatCells(awayStats) +
      '</div>' +
    '</div>' +
    '<div class="fx-dr-ft">' + footerInner + '</div>' +
  '</div>';
}

// ── Match href ────────────────────────────────────────────────────────────

function buildMatchHref(f) {
  var params = new URLSearchParams({
    league: f.league || "",
    date:   f.date   || "",
    home:   f.home   || "",
    away:   f.away   || "",
  });
  return "match.html?" + params.toString();
}

// ── Date label ────────────────────────────────────────────────────────────

function fxDateLabel(dateStr, timeStr) {
  if (!dateStr) return "—";
  var today    = new Date().toISOString().slice(0, 10);
  var diffDays = Math.round((new Date(dateStr) - new Date(today)) / 86400000);

  var label;
  var loc = typeof LANG !== "undefined" && LANG === "en" ? "en-GB" : "es-ES";
  if      (diffDays ===  0) label = loc === "en-GB" ? "Today"     : "Hoy";
  else if (diffDays ===  1) label = loc === "en-GB" ? "Tomorrow"  : "Mañana";
  else if (diffDays === -1) label = loc === "en-GB" ? "Yesterday" : "Ayer";
  else {
    label = new Date(dateStr + "T12:00:00").toLocaleDateString(loc, {
      weekday: "short", day: "numeric", month: "short",
    });
  }
  if (timeStr && timeStr !== "nan" && timeStr !== "") label += " · " + timeStr;
  return label;
}

// ── HTML escape ───────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g,  "&amp;")
    .replace(/"/g,  "&quot;")
    .replace(/</g,  "&lt;")
    .replace(/>/g,  "&gt;");
}
