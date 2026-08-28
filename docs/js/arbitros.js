/**
 * arbitros.js - Tab "Arbitros": referee disciplinary profile by league.
 */

"use strict";

let _arbLeague = "all";
let _arbWindow = "season";

function initArbitros() {
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
        const ld = APP.leagues[code];
        const opt = document.createElement("option");
        opt.value = code;
        opt.textContent = ld ? ld.name : code;
        sel.appendChild(opt);
      }
    });
    if ([...sel.options].some(opt => opt.value === prev)) sel.value = prev;
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

function pickRefStats(r, window_) {
  const keyMap = {
    "all": "overall",
    "season": "season",
  };
  const key = keyMap[window_] || "season";
  const block = r[key];

  if (block) return { ...block, _available: true };

  const overall = r.overall;
  if (window_ === "all" && overall) return { ...overall, _available: true };

  return null;
}

function renderArbitros() {
  const box = document.getElementById("arbitros-result");
  if (!box) return;

  const all = APP.referees || [];
  const byLeague = _arbLeague === "all" ? all : all.filter(r => r.league === _arbLeague);

  if (byLeague.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" style="opacity:.4"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg>
    </div><p>Sin datos de arbitros para esta liga.</p></div>`;
    return;
  }

  const svgRef = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/></svg>`;

  const windowLabelMap = {
    "season": "Esta temporada",
    "all": "Historico completo",
  };
  const windowLabel = windowLabelMap[_arbWindow] || "Esta temporada";
  const leagueName = _arbLeague === "all" ? "todas las ligas" : (APP.leagues[_arbLeague]?.name || _arbLeague);

  const referees = byLeague
    .map(r => ({ r, stats: pickRefStats(r, _arbWindow) }))
    .filter(({ stats }) => stats && Number(stats.matches || 0) > 0);

  if (referees.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">
      ${svgRef}
    </div><p>No hay datos de arbitros para <b>${leagueName}</b> en la ventana <b>${windowLabel}</b>.</p>
    <p class="muted" style="margin-top:8px;">Prueba con "Historico completo" para ver el perfil agregado disponible.</p></div>`;
    return;
  }

  const leagueLabel = `${referees.length} arbitros - ${leagueName}`;
  const unavailableCount = byLeague.length - referees.length;
  const unavailableNote = unavailableCount > 0
    ? `<p style="color:var(--gold);font-size:.82rem;margin-bottom:14px;">
        ${unavailableCount} arbitros omitidos: no hay datos para "${windowLabel}".
       </p>`
    : "";

  // Ocultar la columna de faltas si NINGÚN árbitro visible tiene ese dato
  // (World Soccer Data no lo trae para la mayoría de ligas).
  const showFouls = referees.some(({ stats }) => stats.fouls_per_match != null);

  box.innerHTML = `
  <div class="section-title" style="margin-bottom:16px;">
    ${svgRef} Perfil Disciplinario <small>${leagueLabel} - ${windowLabel}</small>
  </div>
  <p style="color:var(--muted);font-size:.85rem;margin-bottom:10px;">
    La columna PJ corresponde a la ventana seleccionada, no al total historico.
    Perfil: <b style="color:var(--gold)">OVER</b> ≥ 5.0 amarillas/p · <b style="color:var(--brand)">UNDER</b> ≤ 2.8.
    <span class="jug-sort-hint">⇧+clic en una cabecera para ordenar por varias columnas</span>
  </p>
  ${unavailableNote}
  <div class="table-wrap">
    <table id="arbitrosTable">
      <thead>
        <tr>
          <th>Arbitro</th>
          <th title="Partidos pitados">PJ</th>
          <th title="Amarillas por partido">Amar./p</th>
          <th title="Rojas por partido">Rojas/p</th>
          ${showFouls ? '<th title="Faltas por partido">Faltas/p</th>' : ''}
          <th title="Perfil disciplinario (ordena por amarillas/p)">Perfil</th>
        </tr>
      </thead>
      <tbody>
        ${referees.map(({ r, stats }) => buildRefereeRow(r, stats, showFouls)).join("")}
      </tbody>
    </table>
  </div>
  <div class="disclaimer" style="margin-top:14px;">
    Fuente: football-data.co.uk (Premier League y Championship, partido a partido) y World Soccer Data (resto de ligas, agregado de temporada). Medias ponderadas por antigüedad: los partidos recientes pesan más que los antiguos.
  </div>`;

  setTimeout(() => initAllTables(box), 50);
}

function buildRefereeRow(r, stats, showFouls) {
  const name = r.name || "-";
  const href = refereeHref(r);
  const yp = stats.yellows_per_match ?? 0;
  const rp = stats.reds_per_match ?? 0;
  const fp = stats.fouls_per_match;
  const pj = stats.matches ?? 0;

  const ypColor = yp >= 5.5 ? "var(--red)" : yp >= 4.5 ? "var(--gold)" : yp >= 3.5 ? "var(--text)" : "var(--brand)";
  const fpColor = fp == null ? "var(--muted)" : fp >= 28 ? "var(--red)" : fp <= 22 ? "var(--brand)" : "var(--text)";
  const foulsCell = showFouls
    ? `<td style="color:${fpColor}" data-sort="${fp == null ? -1 : fp}">${fp == null ? "—" : fmt(fp, 1)}</td>`
    : "";

  // NEUTRO no aporta señal (la mayoría de árbitros con muestra corta caen ahí):
  // solo se marca OVER / UNDER, el resto queda en blanco.
  let badge = "";
  if (yp >= 5.0) badge = `<span class="badge-over-card" style="font-size:.72rem;padding:3px 8px;border-radius:6px;font-weight:700;">OVER</span>`;
  else if (yp <= 2.8) badge = `<span class="badge-under-card" style="font-size:.72rem;padding:3px 8px;border-radius:6px;font-weight:700;">UNDER</span>`;
  else badge = `<span class="muted" style="font-size:.72rem;">—</span>`;

  return `
  <tr>
    <td><b><a href="${href}">${name}</a></b></td>
    <td class="muted" data-sort="${pj}">${pj}</td>
    <td style="color:${ypColor};font-weight:600;" data-sort="${yp}">${fmt(yp, 2)}</td>
    <td data-sort="${rp}">${fmt(rp, 2)}</td>
    ${foulsCell}
    <td data-sort="${yp}">${badge}</td>
  </tr>`;
}

function refereeHref(r) {
  const params = new URLSearchParams({
    name: r.name || "",
    league: r.league || "",
  });
  return `referee.html?${params.toString()}`;
}
