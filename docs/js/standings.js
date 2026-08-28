/**
 * standings.js - Tab "Clasificación": tabla de posiciones y máximos
 * goleadores vía football-data.org. Actualizado a diario, no en directo.
 */

"use strict";

let _clasifLeague = null;

function initStandings() {
  wireSubTabs();
  fetchStandingsData();

  document.addEventListener("kdx:tab-open", e => {
    if (e.detail?.tab === "clasificacion") fetchStandingsData();
  });

  const sel = document.getElementById("clasif-league");
  if (sel) {
    sel.addEventListener("change", e => {
      _clasifLeague = e.target.value;
      renderStandings();
      renderScorers();
    });
  }
}

// El wiring de .sub-btn/.sub-panel genérico no está en initTabs(); esta
// pestaña gestiona su propio toggle Tabla/Goleadores para no depender de
// eso (y no chocar con otras pestañas que pudieran usar la misma clase).
function wireSubTabs() {
  const panel = document.getElementById("tab-clasificacion");
  if (!panel) return;
  panel.querySelectorAll(".sub-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      panel.querySelectorAll(".sub-btn").forEach(b => b.classList.remove("active"));
      panel.querySelectorAll(".sub-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const sub = document.getElementById("sub-" + btn.dataset.sub);
      if (sub) sub.classList.add("active");
    });
  });
}

async function fetchStandingsData() {
  try {
    const [standings, scorers] = await Promise.all([
      fetchJSON("standings.json"),
      fetchJSON("scorers.json"),
    ]);
    APP.standings = standings;
    APP.scorers = scorers;
    populateClasifLeagueSelect();
    renderStandings();
    renderScorers();
  } catch (err) {
    console.warn("Standings/scorers load failed:", err);
    renderDisabledState("No se pudo cargar la clasificación.");
  }
}

function populateClasifLeagueSelect() {
  const sel = document.getElementById("clasif-league");
  if (!sel) return;
  const covered = Object.keys(APP.standings?.leagues || {});
  if (!covered.length) return;
  const prev = sel.value;
  sel.innerHTML = "";
  const ordered = typeof sortLeagueCodes === "function" ? sortLeagueCodes(covered) : covered.sort();
  ordered.forEach(code => {
    if (typeof appendLeagueOption === "function" && APP.leagues?.[code]) {
      appendLeagueOption(sel, code);
    } else {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = APP.leagues?.[code]?.name || code;
      sel.appendChild(opt);
    }
  });
  _clasifLeague = ordered.includes(prev) ? prev : ordered[0];
  sel.value = _clasifLeague;
}

function renderDisabledState(message) {
  const chip = null;
  const tableRoot = document.getElementById("clasif-table-root");
  const scorersRoot = document.getElementById("clasif-scorers-root");
  const html = `<div class="fx-empty">${escHtml(message)}</div>`;
  if (tableRoot) tableRoot.innerHTML = html;
  if (scorersRoot) scorersRoot.innerHTML = "";
}

function renderStandings() {
  const root = document.getElementById("clasif-table-root");
  if (!root) return;
  const data = APP.standings;
  if (!data?.enabled) {
    renderDisabledState(data?.note || "Clasificación desactivada: falta configurar el acceso a football-data.org.");
    return;
  }
  const league = data.leagues?.[_clasifLeague];
  if (!league) {
    root.innerHTML = `<div class="fx-empty">Sin clasificación disponible para esta liga.</div>`;
    return;
  }
  const updated = data.updated_at ? new Date(data.updated_at).toLocaleString("es-ES") : "—";
  root.innerHTML = `
  <div class="disclaimer" style="margin-bottom:12px;">
    Jornada ${league.matchday ?? "—"} · actualizado ${updated} · ${escHtml(data.note || "")}
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th data-nosort>#</th>
          <th>Equipo</th>
          <th title="Partidos jugados">PJ</th>
          <th title="Ganados">G</th>
          <th title="Empatados">E</th>
          <th title="Perdidos">P</th>
          <th title="Goles a favor / en contra">GF/GC</th>
          <th title="Diferencia de goles">DG</th>
          <th title="Puntos">Pts</th>
        </tr>
      </thead>
      <tbody>
        ${league.table.map((row, i) => standingsRow(row, i)).join("")}
      </tbody>
    </table>
  </div>`;
  setTimeout(() => initAllTables(root), 50);
}

function standingsRow(row, index) {
  const media = typeof entityMedia === "function" ? entityMedia("team", row.team) : "";
  const name = typeof teamDisplayName === "function" ? teamDisplayName(row.team) : row.team;
  // Posición por orden de la tabla (ya viene ordenada de football-data.org);
  // `row.position` puede empatar a inicio de temporada sin desempate aplicado.
  const pos = Number.isInteger(index) ? index + 1 : row.position;
  return `
  <tr>
    <td>${pos}</td>
    <td><span class="fx-team">${media}<b>${escHtml(name)}</b></span></td>
    <td>${row.played}</td>
    <td>${row.won}</td>
    <td>${row.draw}</td>
    <td>${row.lost}</td>
    <td>${row.goals_for}-${row.goals_against}</td>
    <td>${row.goal_diff > 0 ? "+" : ""}${row.goal_diff}</td>
    <td><b>${row.points}</b></td>
  </tr>`;
}

function renderScorers() {
  const root = document.getElementById("clasif-scorers-root");
  if (!root) return;
  const data = APP.scorers;
  if (!data?.enabled) {
    root.innerHTML = "";
    return;
  }
  const league = data.leagues?.[_clasifLeague];
  if (!league || !league.scorers?.length) {
    root.innerHTML = `<div class="fx-empty">Sin goleadores disponibles para esta liga.</div>`;
    return;
  }
  root.innerHTML = `
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th data-nosort>#</th>
          <th>Jugador</th>
          <th>Equipo</th>
          <th title="Goles">Goles</th>
          <th title="Partidos jugados">PJ</th>
          <th title="De penalti">Pen.</th>
        </tr>
      </thead>
      <tbody>
        ${league.scorers.map(scorerRow).join("")}
      </tbody>
    </table>
  </div>`;
  setTimeout(() => initAllTables(root), 50);
}

function scorerRow(row) {
  const teamName = typeof teamDisplayName === "function" ? teamDisplayName(row.team) : row.team;
  return `
  <tr>
    <td>${row.rank}</td>
    <td>${escHtml(row.player || "—")}</td>
    <td>${escHtml(teamName)}</td>
    <td><b>${row.goals}</b></td>
    <td>${row.played_matches ?? "—"}</td>
    <td>${row.penalties ?? 0}</td>
  </tr>`;
}
