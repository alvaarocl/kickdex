/**
 * arbitros.js - Tab "Arbitros": perfil disciplinario por liga.
 *
 * Tabla con calor por percentil de columna (ui_kit.js), comparación contra la
 * media de su liga, últimos partidos como pastillas de tarjetas y filtro de
 * árbitros en activo (los retirados hinchaban la lista: 170 en Championship).
 */

"use strict";

let _arbLeague = "all";
let _arbWindow = "season";
let _arbQuery = "";
let _arbActiveOnly = true;
let _arbShowAll = false;
let _arbInit = false;

const ARB_PAGE = 40;
const ARB_MIN_SAMPLE = 5;         // PJ mínimos para entrar en los "destacados"
const ARB_ACTIVE_DAYS = 450;      // mismo umbral que REFEREE_ACTIVE_DAYS (build_data.py)

function initArbitros() {
  if (_arbInit) { renderArbitros(); return; }
  _arbInit = true;

  const sel = document.getElementById("arb-league-filter");
  if (sel) {
    const prev = sel.value;
    while (sel.options.length > 1) sel.remove(1);
    const leaguesInData = typeof sortLeagueCodes === "function"
      ? sortLeagueCodes((APP.referees || []).map(r => r.league))
      : [...new Set((APP.referees || []).map(r => r.league))].sort();
    leaguesInData.forEach(code => {
      if (typeof appendLeagueOption === "function" && APP.leagues?.[code]) {
        appendLeagueOption(sel, code);
      } else {
        const opt = document.createElement("option");
        opt.value = code;
        opt.textContent = APP.leagues?.[code]?.name || code;
        sel.appendChild(opt);
      }
    });
    if ([...sel.options].some(opt => opt.value === prev)) sel.value = prev;
    sel.addEventListener("change", e => {
      _arbLeague = e.target.value;
      _arbShowAll = false;
      renderArbitros();
    });
  }

  const windowSel = document.getElementById("arb-window");
  if (windowSel) {
    windowSel.addEventListener("change", e => {
      _arbWindow = e.target.value;
      renderArbitros();
    });
  }

  const box = document.getElementById("arbitros-result");
  if (box) {
    box.innerHTML = `
      <div id="arb-summary"></div>
      <div class="ktoolbar">
        <input id="arb-search" class="ksearch" type="search" placeholder="Buscar árbitro…" autocomplete="off" aria-label="Buscar árbitro" />
        <button id="arb-active" class="ktoggle" type="button" aria-pressed="true" title="Oculta árbitros sin partidos en las últimas ~1,5 temporadas">Solo en activo</button>
        <span class="kcount" id="arb-count"></span>
      </div>
      <div id="arb-table"></div>`;
    document.getElementById("arb-search").addEventListener("input", e => {
      _arbQuery = e.target.value;
      renderArbitros();
    });
    document.getElementById("arb-active").addEventListener("click", e => {
      _arbActiveOnly = !_arbActiveOnly;
      e.currentTarget.setAttribute("aria-pressed", String(_arbActiveOnly));
      renderArbitros();
    });
  }

  renderArbitros();
}

function pickRefStats(r, window_) {
  const block = window_ === "all" ? r.overall : r.season;
  if (block) return { ...block, _available: true };
  if (window_ === "all" && r.season) return { ...r.season, _available: true };
  return null;
}

// PJ real: `overall.matches` está topado por la ventana ponderada (60).
function refMatches(r, stats) {
  if (_arbWindow === "all") {
    if (Number.isFinite(Number(r.career_matches))) return Number(r.career_matches);
  }
  return Number(stats.matches || 0);
}

function refIsActive(r) {
  if (typeof r.active === "boolean") return r.active;
  if (r.season) return true;
  const last = r.overall?.last_match || r.last_match;
  if (!last) return true; // agregados de temporada sin fecha → temporada actual
  return (Date.now() - new Date(last).getTime()) / 86400000 <= ARB_ACTIVE_DAYS;
}

function refLeagueName(code) {
  return APP.leagues?.[code]?.name || code || "";
}

function arbNorm(s) {
  return String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function renderArbitros() {
  const summary = document.getElementById("arb-summary");
  const tableBox = document.getElementById("arb-table");
  const countEl = document.getElementById("arb-count");
  if (!tableBox) return;

  const all = APP.referees || [];
  const byLeague = _arbLeague === "all" ? all : all.filter(r => r.league === _arbLeague);
  const windowLabel = _arbWindow === "all" ? "Histórico completo" : "Esta temporada";
  const leagueName = _arbLeague === "all" ? "todas las ligas" : refLeagueName(_arbLeague);

  let rows = byLeague
    .map(r => ({ r, stats: pickRefStats(r, _arbWindow), active: refIsActive(r) }))
    .filter(({ stats }) => stats && Number(stats.matches || 0) > 0)
    .map(row => ({ ...row, pj: refMatches(row.r, row.stats), yp: Number(row.stats.yellows_per_match) || 0 }));

  const inactiveCount = rows.filter(x => !x.active).length;
  if (_arbActiveOnly) rows = rows.filter(x => x.active);
  const q = arbNorm(_arbQuery);
  if (q) rows = rows.filter(x => arbNorm(x.r.name).includes(q));

  if (!rows.length) {
    if (summary) summary.innerHTML = "";
    if (countEl) countEl.textContent = "";
    tableBox.innerHTML = `<div class="state-box"><div class="icon">⚖</div>
      <p>No hay árbitros para <b>${escHtml(leagueName)}</b> en la ventana <b>${windowLabel}</b>${q ? ` que coincidan con “${escHtml(_arbQuery)}”` : ""}.</p>
      <p class="muted" style="margin-top:8px;">${_arbWindow === "season" ? 'Prueba con "Histórico completo".' : (_arbActiveOnly ? 'Desactiva "Solo en activo" para ver históricos.' : "")}</p></div>`;
    return;
  }

  // Media por liga (sobre árbitros con muestra suficiente de la ventana).
  const leagueAvg = {};
  const byCode = {};
  rows.forEach(x => (byCode[x.r.league] = byCode[x.r.league] || []).push(x));
  Object.entries(byCode).forEach(([code, list]) => {
    const pool = list.filter(x => x.pj >= ARB_MIN_SAMPLE);
    const src = pool.length >= 3 ? pool : list;
    leagueAvg[code] = {
      y: src.reduce((s, x) => s + x.yp, 0) / src.length,
      r: src.reduce((s, x) => s + (Number(x.stats.reds_per_match) || 0), 0) / src.length,
    };
  });

  // Muestra corta al final: un 7.00 con 1 partido no es "el más tarjetero".
  rows.sort((a, b) => (a.pj < ARB_MIN_SAMPLE) - (b.pj < ARB_MIN_SAMPLE) || b.yp - a.yp || b.pj - a.pj);

  if (summary) summary.innerHTML = buildRefSummary(rows, leagueAvg);
  if (countEl) {
    countEl.textContent = `${rows.length} árbitros · ${leagueName} · ${windowLabel}`
      + (_arbActiveOnly && inactiveCount ? ` · ${inactiveCount} retirados/inactivos ocultos` : "");
  }

  const showFouls = rows.some(({ stats }) => Number(stats.fouls_per_match) > 0);
  const showRecent = rows.some(({ r }) => (r.recent_matches || []).length);
  const rankY = kdxRanker(rows.filter(x => x.pj >= ARB_MIN_SAMPLE).map(x => x.yp));
  const rankR = kdxRanker(rows.filter(x => x.pj >= ARB_MIN_SAMPLE).map(x => x.stats.reds_per_match));
  const rankF = kdxRanker(rows.map(x => Number(x.stats.fouls_per_match)).filter(v => v > 0));
  const maxY = Math.max(...rows.filter(x => x.pj >= ARB_MIN_SAMPLE).map(x => x.yp), 1);
  const visible = _arbShowAll ? rows : rows.slice(0, ARB_PAGE);
  const showLeague = _arbLeague === "all";

  tableBox.innerHTML = `
  <div class="table-wrap ktable-wrap">
    <table id="arbitrosTable" class="ktable">
      <thead>
        <tr>
          <th data-nosort class="ctr">#</th>
          <th>Árbitro</th>
          <th class="num" title="Partidos pitados en la ventana">PJ</th>
          <th title="Amarillas por partido (media ponderada: lo reciente pesa más)">Amarillas/p</th>
          <th class="num hide-xs" title="Diferencia con la media de amarillas de su liga">vs liga</th>
          <th class="num" title="Rojas por partido">Rojas/p</th>
          ${showFouls ? '<th class="num hide-sm" title="Faltas por partido">Faltas/p</th>' : ""}
          ${showRecent ? '<th data-nosort class="hide-sm" title="Tarjetas en sus últimos 5 partidos (antiguo → reciente)">Últimos 5</th>' : ""}
          <th title="Perfil frente a su liga">Perfil</th>
        </tr>
      </thead>
      <tbody>
        ${visible.map((x, i) => buildRefereeRow(x, i, { showFouls, showRecent, showLeague, rankY, rankR, rankF, maxY, avg: leagueAvg[x.r.league] })).join("")}
      </tbody>
    </table>
  </div>
  ${rows.length > ARB_PAGE ? `<button class="btn btn-secondary btn-sm kmore" type="button" id="arb-more">${_arbShowAll ? "Mostrar menos" : `Mostrar los ${rows.length} árbitros`}</button>` : ""}
  <div class="klegend">
    <span><i style="background:rgba(255,90,110,.6)"></i>Top 10% de su columna</span>
    <span><i style="background:rgba(245,185,60,.55)"></i>Por encima de lo normal</span>
    <span><i style="background:rgba(46,230,166,.5)"></i>Por debajo de lo normal</span>
    <span>Perfil: <b style="color:#FF8A98">TARJETERO</b> ≥ +20% sobre su liga · <b style="color:var(--brand)">PERMISIVO</b> ≤ −20%</span>
  </div>
  <div class="disclaimer" style="margin-top:14px;">
    Fuente: football-data.co.uk (Premier League y Championship, partido a partido) y World Soccer Data (resto de ligas, agregado de temporada). Medias ponderadas por antigüedad: los partidos recientes pesan más. Con menos de ${ARB_MIN_SAMPLE} partidos la muestra es corta y no se colorea.
    <span class="jug-sort-hint">⇧+clic en una cabecera para ordenar por varias columnas</span>
  </div>`;

  document.getElementById("arb-more")?.addEventListener("click", () => {
    _arbShowAll = !_arbShowAll;
    renderArbitros();
  });
  setTimeout(() => initAllTables(tableBox), 30);
}

function buildRefSummary(rows, leagueAvg) {
  const pool = rows.filter(x => x.pj >= ARB_MIN_SAMPLE);
  const src = pool.length ? pool : rows;
  const strict = src.reduce((a, b) => (b.yp > a.yp ? b : a), src[0]);
  const lenient = src.reduce((a, b) => (b.yp < a.yp ? b : a), src[0]);
  const reds = src.reduce((a, b) => ((Number(b.stats.reds_per_match) || 0) > (Number(a.stats.reds_per_match) || 0) ? b : a), src[0]);
  const avgY = src.reduce((s, x) => s + x.yp, 0) / src.length;
  const link = x => `<a href="${refereeHref(x.r)}">${escHtml(x.r.name)}</a>${_arbLeague === "all" ? ` · ${escHtml(x.r.league)}` : ""}`;
  return `
  <div class="kstat-grid">
    <div class="kstat kstat--blue"><span>Media amarillas/p</span><strong>${fmt(avgY, 2)}</strong><small>${src.length} árbitros con ≥${ARB_MIN_SAMPLE} PJ</small></div>
    <div class="kstat kstat--red"><span>Más tarjetero</span><strong>${fmt(strict.yp, 2)}</strong><small>${link(strict)}</small></div>
    <div class="kstat kstat--green"><span>Más permisivo</span><strong>${fmt(lenient.yp, 2)}</strong><small>${link(lenient)}</small></div>
    <div class="kstat kstat--gold"><span>Más rojas/p</span><strong>${fmt(reds.stats.reds_per_match, 2)}</strong><small>${link(reds)}</small></div>
  </div>`;
}

function buildRefereeRow(x, index, o) {
  const { r, stats, pj, yp, active } = x;
  const rp = Number(stats.reds_per_match) || 0;
  const fp = Number(stats.fouls_per_match) > 0 ? Number(stats.fouls_per_match) : null; // 0 = sin dato
  const short = pj < ARB_MIN_SAMPLE;
  const avgY = o.avg?.y;
  const diff = Number.isFinite(avgY) ? yp - avgY : null;
  const ratio = Number.isFinite(avgY) && avgY > 0 ? yp / avgY : 1;

  let profile = `<span class="kchip kchip--mid">NEUTRO</span>`;
  if (short) profile = `<span class="kchip kchip--off" title="Menos de ${ARB_MIN_SAMPLE} partidos">MUESTRA CORTA</span>`;
  else if (ratio >= 1.2) profile = `<span class="kchip kchip--over">TARJETERO</span>`;
  else if (ratio <= 0.8) profile = `<span class="kchip kchip--under">PERMISIVO</span>`;

  const yClass = short ? "" : kdxHeatClass(o.rankY(yp), "risk");
  const rClass = short ? "" : kdxHeatClass(o.rankR(rp), "risk");
  const fClass = fp == null ? "" : kdxHeatClass(o.rankF(fp), "risk");

  const recent = (r.recent_matches || []).slice(0, 5).reverse();
  const recentCell = o.showRecent
    ? `<td class="hide-sm">${recent.length
        ? `<span class="kcards">${recent.map(m => kdxCardPill(m.yellows, m.reds, avgY)).join("")}</span>`
        : '<span class="muted">—</span>'}</td>`
    : "";

  const sub = [
    o.showLeague ? escHtml(refLeagueName(r.league)) : "",
    !active ? "inactivo" : "",
    _arbWindow === "all" && r.first_match ? `desde ${String(r.first_match).slice(0, 4)}` : "",
  ].filter(Boolean).join(" · ");

  const cap = _arbWindow === "all" && r.career_matches == null && pj >= 60 ? "+" : "";

  return `
  <tr>
    <td class="ctr"><span class="krank ${index < 3 && !short ? `krank--${index + 1}` : ""}">${index + 1}</span></td>
    <td>
      <span class="kent ${active ? "" : "kent--inactive"}">
        <span class="kent-avatar">${refInitials(r.name)}</span>
        <span class="kent-name"><a href="${refereeHref(r)}">${escHtml(r.name || "-")}</a>${sub ? `<small>${sub}</small>` : ""}</span>
      </span>
    </td>
    <td class="num muted" data-sort="${pj}">${pj}${cap}</td>
    <td class="${yClass}" data-sort="${yp}"><span class="kcell-bar">${fmt(yp, 2)}${kdxBar(yp, o.maxY, "risk")}</span></td>
    <td class="num hide-xs" data-sort="${diff ?? 0}">${short ? '<span class="kdiff">—</span>' : kdxDiff(diff)}</td>
    <td class="num ${rClass}" data-sort="${rp}">${fmt(rp, 2)}</td>
    ${o.showFouls ? `<td class="num hide-sm ${fClass}" data-sort="${fp == null ? -1 : fp}">${fp == null ? "—" : fmt(fp, 1)}</td>` : ""}
    ${recentCell}
    <td data-sort="${short ? -9 : ratio}">${profile}</td>
  </tr>`;
}

function refInitials(name) {
  return String(name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join("").toUpperCase();
}

function refereeHref(r) {
  const params = new URLSearchParams({
    name: r.name || "",
    league: r.league || "",
  });
  return `referee.html?${params.toString()}`;
}
