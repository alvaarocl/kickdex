/**
 * arbitros.js — Tab "Árbitros": referee disciplinary profile
 */

"use strict";

function initArbitros() {
  // It is automatically called after all JSON is loaded via app.js
  renderArbitros();
}

function renderArbitros() {
  const box = document.getElementById("arbitros-result");
  if (!box) return;

  const referees = APP.referees;

  if (!referees || referees.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">📭</div><p>Sin datos de árbitros disponibles</p></div>`;
    return;
  }

  const svgReferee = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/></svg>`;

  box.innerHTML = `
  <div class="section-title" style="margin-bottom:16px;">
    ${svgReferee} Perfil Disciplinario <small>${referees.length} árbitros (mínimo 3 partidos)</small>
  </div>
  <div class="controls" style="margin-bottom:18px;">
     <p style="color:var(--muted);font-size:.85rem;">Datos históricos para identificar árbitros "over" o "under" en mercados disciplinarios.</p>
  </div>
  <div class="table-wrap">
    <table id="arbitrosTable">
      <thead>
        <tr>
          <th>Árbitro</th>
          <th title="Partidos pitados">Partidos</th>
          <th title="Amarillas por partido">Amarillas/p</th>
          <th title="Rojas por partido">Rojas/p</th>
          <th title="Faltas por partido">Faltas/p</th>
        </tr>
      </thead>
      <tbody>
        ${referees.map(r => buildRefereeRow(r)).join("")}
      </tbody>
    </table>
  </div>
  <div class="disclaimer" style="margin-top:14px;">
    Los datos se basan en el registro histórico disponible.
  </div>`;
  setTimeout(() => initAllTables(box), 50);
}

function buildRefereeRow(r) {
  const name = r.name || "—";
  const matches = r.matches || 0;
  const yp = r.yellows_per_match ?? 0;
  const rp = r.reds_per_match ?? 0;
  const fp = r.fouls_per_match ?? 0;

  const ypColor = yp >= 5.5 ? "var(--red)" : yp >= 4.5 ? "var(--yellow)" : "var(--green)";
  const fpColor = fp >= 28 ? "var(--red)" : fp <= 22 ? "var(--green)" : "var(--text)";

  return `
  <tr>
    <td><b>${name}</b></td>
    <td class="muted">${matches}</td>
    <td style="color:${ypColor};font-weight:600;">${fmt(yp, 2)}</td>
    <td>${fmt(rp, 2)}</td>
    <td style="color:${fpColor}">${fmt(fp, 1)}</td>
  </tr>`;
}