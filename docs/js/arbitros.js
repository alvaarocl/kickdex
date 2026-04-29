/**
 * arbitros.js — Tab "Árbitros": referee disciplinary profile by league
 */

"use strict";

let _arbLeague = "all";
let _arbWindow = "season";

function initArbitros() {
  const sel = document.getElementById("arb-league-filter");
  if (sel) {
    while (sel.options.length > 1) sel.remove(1);
    const leaguesInData = [...new Set((APP.referees || []).map(r => r.league))].sort();
    leaguesInData.forEach(code => {
      const ld = APP.leagues[code];
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = ld ? ld.name : code;
      sel.appendChild(opt);
    });
    sel.addEventListener("change", e => {
      _arbLeague = e.target.value;
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

  renderArbitros();
}

/**
 * Resolve stats block for a referee given current window.
 * Always returns data — falls back to overall if windowed block is null.
 */
function pickRefStats(r, window_) {
  const keyMap = {
    "5": "last5", "10": "last10", "all": "overall",
    "season": "season", "season_last10": "season_last10", "season_last5": "season_last5",
  };
  const key = keyMap[window_] || "overall";
  const block = r[key];

  if (block) return { ...block, _fallback: false };

  // Season fallback: if no season data, use overall
  if (window_.startsWith("season")) {
    const overall = r["overall"];
    if (overall) return { ...overall, _fallback: true };
  }

  const overall = r["overall"];
  if (overall) return { ...overall, _fallback: window_ !== "all" };

  return {
    matches:           r.matches           ?? 0,
    yellows_per_match: r.yellows_per_match ?? 0,
    reds_per_match:    r.reds_per_match    ?? 0,
    fouls_per_match:   r.fouls_per_match   ?? 0,
    _fallback: window_ !== "all",
  };
}

function renderArbitros() {
  const box = document.getElementById("arbitros-result");
  if (!box) return;

  const all      = APP.referees || [];
  const byLeague = _arbLeague === "all" ? all : all.filter(r => r.league === _arbLeague);

  if (byLeague.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" style="opacity:.4"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg>
    </div><p>Sin datos de árbitros para esta liga.</p></div>`;
    return;
  }

  const referees = byLeague.map(r => ({ r, stats: pickRefStats(r, _arbWindow) }));

  const svgRef = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/></svg>`;

  const windowLabelMap = {
    "season": "Esta temporada", "season_last10": "Esta temp. — Últ. 10",
    "season_last5": "Esta temp. — Últ. 5",
    "all": "Histórico completo", "10": "Histórico — Últ. 10", "5": "Histórico — Últ. 5",
  };
  const windowLabel = windowLabelMap[_arbWindow] || "Esta temporada";
  const leagueLabel = _arbLeague === "all"
    ? `${referees.length} árbitros · todas las ligas`
    : `${referees.length} árbitros · ${APP.leagues[_arbLeague]?.name || _arbLeague}`;

  const hasFallback = referees.some(({ stats }) => stats._fallback);
  const isSeason = _arbWindow.startsWith("season");
  const fallbackNote = hasFallback
    ? `<p style="color:var(--yellow);font-size:.82rem;margin-bottom:14px;">
        ⚠ ${isSeason ? "Algunos árbitros no tienen partidos esta temporada — mostrando histórico." : "Ventana reducida no disponible — mostrando histórico general."}
       </p>`
    : "";

  box.innerHTML = `
  <div class="section-title" style="margin-bottom:16px;">
    ${svgRef} Perfil Disciplinario <small>${leagueLabel} · ${windowLabel}</small>
  </div>
  <p style="color:var(--muted);font-size:.85rem;margin-bottom:10px;">
    Datos históricos para identificar perfiles disciplinarios altos o bajos.
  </p>
  ${fallbackNote}
  <div class="table-wrap">
    <table id="arbitrosTable">
      <thead>
        <tr>
          <th>Árbitro</th>
          <th title="Partidos pitados">PJ</th>
          <th title="Amarillas por partido">Amar./p</th>
          <th title="Rojas por partido">Rojas/p</th>
          <th title="Faltas por partido">Faltas/p</th>
          <th title="Tendencia disciplinaria" data-nosort>Tendencia</th>
        </tr>
      </thead>
      <tbody>
        ${referees.map(({ r, stats }) => buildRefereeRow(r, stats)).join("")}
      </tbody>
    </table>
  </div>
  <div class="disclaimer" style="margin-top:14px;">
    Fuente: football-data.co.uk · Datos con árbitros disponibles: Premier League, Championship, Serie A.
  </div>`;

  setTimeout(() => initAllTables(box), 50);
}

function buildRefereeRow(r, stats) {
  const name = r.name || "—";
  const yp   = stats.yellows_per_match ?? 0;
  const rp   = stats.reds_per_match    ?? 0;
  const fp   = stats.fouls_per_match   ?? 0;
  const pj   = stats.matches           ?? 0;

  const ypColor = yp >= 5.5 ? "var(--red)" : yp >= 4.5 ? "var(--yellow)" : yp >= 3.5 ? "var(--text)" : "var(--green)";
  const fpColor = fp >= 28  ? "var(--red)" : fp <= 22  ? "var(--green)"  : "var(--text)";

  let badge, badgeCls;
  if (yp >= 5.0) {
    badge = "OVER"; badgeCls = "badge-over-card";
  } else if (yp <= 2.8) {
    badge = "UNDER"; badgeCls = "badge-under-card";
  } else {
    badge = "NEUTRO"; badgeCls = "badge-fair";
  }

  return `
  <tr>
    <td><b>${name}</b></td>
    <td class="muted" data-sort="${pj}">${pj}</td>
    <td style="color:${ypColor};font-weight:600;" data-sort="${yp}">${fmt(yp, 2)}</td>
    <td data-sort="${rp}">${fmt(rp, 2)}</td>
    <td style="color:${fpColor}" data-sort="${fp}">${fmt(fp, 1)}</td>
    <td><span class="${badgeCls}" style="font-size:.72rem;padding:3px 8px;border-radius:6px;font-weight:700;">${badge}</span></td>
  </tr>`;
}
