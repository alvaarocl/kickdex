/**
 * arbitros.js — Tab "Árbitros": referee disciplinary profile by league
 */

"use strict";

let _arbLeague = "all";

function initArbitros() {
  const sel = document.getElementById("arb-league-filter");
  if (sel) {
    // Populate leagues that have referee data
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
  renderArbitros();
}

function renderArbitros() {
  const box = document.getElementById("arbitros-result");
  if (!box) return;

  const all = APP.referees || [];
  const referees = _arbLeague === "all" ? all : all.filter(r => r.league === _arbLeague);

  if (referees.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" style="opacity:.4"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg>
    </div><p>Sin datos de árbitros para esta liga</p></div>`;
    return;
  }

  const svgRef = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/></svg>`;

  const leagueLabel = _arbLeague === "all"
    ? `${referees.length} árbitros (todas las ligas)`
    : `${referees.length} árbitros · ${APP.leagues[_arbLeague]?.name || _arbLeague}`;

  box.innerHTML = `
  <div class="section-title" style="margin-bottom:16px;">
    ${svgRef} Perfil Disciplinario <small>${leagueLabel}</small>
  </div>
  <p style="color:var(--muted);font-size:.85rem;margin-bottom:18px;">
    Datos históricos para identificar árbitros "over" o "under" en mercados disciplinarios.
    Mínimo 3 partidos pitados.
  </p>
  <div class="table-wrap">
    <table id="arbitrosTable">
      <thead>
        <tr>
          <th>Árbitro</th>
          <th title="Partidos pitados">PJ</th>
          <th title="Amarillas por partido">Amar./p</th>
          <th title="Rojas por partido">Rojas/p</th>
          <th title="Faltas por partido">Faltas/p</th>
          <th title="Tendencia disciplinaria">Tendencia</th>
        </tr>
      </thead>
      <tbody>
        ${referees.map(r => buildRefereeRow(r)).join("")}
      </tbody>
    </table>
  </div>
  <div class="disclaimer" style="margin-top:14px;">
    Los datos se basan en el registro histórico disponible. Fuente: football-data.co.uk
  </div>`;

  setTimeout(() => initAllTables(box), 50);
}

function buildRefereeRow(r) {
  const name    = r.name    || "—";
  const matches = r.matches || 0;
  const yp      = r.yellows_per_match ?? 0;
  const rp      = r.reds_per_match    ?? 0;
  const fp      = r.fouls_per_match   ?? 0;

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
    <td class="muted">${matches}</td>
    <td style="color:${ypColor};font-weight:600;">${fmt(yp, 2)}</td>
    <td>${fmt(rp, 2)}</td>
    <td style="color:${fpColor}">${fmt(fp, 1)}</td>
    <td><span class="${badgeCls}" style="font-size:.72rem;padding:3px 8px;border-radius:6px;font-weight:700;">${badge}</span></td>
  </tr>`;
}
