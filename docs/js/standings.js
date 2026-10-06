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
  const ordered = sortLeagueCodes(covered);
  fillCompetitionSelect(sel, ordered, { keepFirst: false });
  _clasifLeague = ordered.includes(prev) ? prev : (ordered.find(c => !APP.leagues?.[c]?.competition) || ordered[0]);
  sel.value = _clasifLeague;
  mountCompetitionChips(sel, ordered);  // re-sincroniza el chip activo
}

function renderDisabledState(message) {
  const chip = null;
  const tableRoot = document.getElementById("clasif-table-root");
  const scorersRoot = document.getElementById("clasif-scorers-root");
  const html = `<div class="fx-empty">${escHtml(message)}</div>`;
  if (tableRoot) tableRoot.innerHTML = html;
  if (scorersRoot) scorersRoot.innerHTML = "";
}

// Zonas orientativas por liga (posiciones 1-based). Pueden variar por
// coeficientes UEFA o ganadores de copa: se etiqueta como "orientativo".
const CLASIF_ZONES = {
  SP1: { ucl: [1, 4], uel: [5, 5], uecl: [6, 6], rel: [18, 20] },
  E0:  { ucl: [1, 4], uel: [5, 5], uecl: [6, 6], rel: [18, 20] },
  I1:  { ucl: [1, 4], uel: [5, 5], uecl: [6, 6], rel: [18, 20] },
  D1:  { ucl: [1, 4], uel: [5, 5], uecl: [6, 6], po: [16, 16], rel: [17, 18] },
  F1:  { ucl: [1, 4], uel: [5, 5], uecl: [6, 6], po: [16, 16], rel: [17, 18] },
  N1:  { ucl: [1, 2], uel: [3, 3], uecl: [4, 4], po: [16, 16], rel: [17, 18] },
  E1:  { promo: [1, 2], po: [3, 6], rel: [22, 24] },
};
const CLASIF_ZONE_LABELS = {
  ucl: "Champions League", uclq: "Previa de Champions", uel: "Europa League", uecl: "Conference League",
  promo: "Ascenso directo", po: "Playoff de ascenso", relpo: "Playoff de descenso", rel: "Descenso",
  r16: "Octavos de final", kopo: "Playoff de eliminatorias", out: "Eliminado",
};

// Zona: primero la que trae el dato (ESPN, por fila); si no, la tabla fija.
function clasifZone(code, pos, total, row) {
  if (row && typeof row.zone === "string" && CLASIF_ZONE_LABELS[row.zone]) return row.zone;
  if (row && row.zone === "" && APP.standings?.leagues?.[code]?.table?.some(r => r.zone)) return "";
  const zones = CLASIF_ZONES[code] || { rel: [total - 2, total] };
  for (const [zone, [from, to]] of Object.entries(zones)) {
    if (pos >= from && pos <= to) return zone;
  }
  return "";
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
  const table = league.table || [];
  const total = table.length;
  const maxPts = Math.max(...table.map(r => Number(r.points) || 0), 1);
  const played = table.map(r => Math.max(1, Number(r.played) || 1));
  const rankGF = kdxRanker(table.map((r, i) => r.goals_for / played[i]));
  const rankGA = kdxRanker(table.map((r, i) => r.goals_against / played[i]));
  // Solo partidos de ESTA competición (si no, la forma de LaLiga mezclaría la Champions).
  const fixtureLists = [APP.fixtures?.calendar, APP.fixtures?.recent]
    .map(list => (list || []).filter(f => f.league === _clasifLeague));

  const zonesUsed = new Set();
  let prevZone = null;
  const rows = table.map((row, i) => {
    const pos = i + 1;
    const zone = clasifZone(_clasifLeague, pos, total, row);
    if (zone) zonesUsed.add(zone);
    const cut = i > 0 && zone !== prevZone;
    prevZone = zone;
    return standingsRow(row, i, {
      zone, cut, maxPts, fixtureLists,
      gfClass: kdxHeatClass(rankGF(row.goals_for / played[i]), "good"),
      gaClass: kdxHeatClass(rankGA(row.goals_against / played[i]), "risk"),
    });
  }).join("");

  const legend = [...zonesUsed].map(z =>
    `<span><i style="background:var(--zone-${z})"></i>${CLASIF_ZONE_LABELS[z]}</span>`).join("");

  root.innerHTML = `
  <div class="disclaimer" style="margin-bottom:12px;">
    Jornada ${league.matchday ?? "—"} · actualizado ${updated} · ${escHtml(data.note || "")}
  </div>
  <div class="table-wrap">
    <table class="ktable" id="clasifTable">
      <thead>
        <tr>
          <th data-nosort class="ctr">#</th>
          <th>Equipo</th>
          <th class="num" title="Partidos jugados">PJ</th>
          <th class="num hide-xs" title="Ganados">G</th>
          <th class="num hide-xs" title="Empatados">E</th>
          <th class="num hide-xs" title="Perdidos">P</th>
          <th class="num hide-sm" title="Goles a favor (color: ataque relativo por partido)">GF</th>
          <th class="num hide-sm" title="Goles en contra (rojo: defensa más débil)">GC</th>
          <th class="num" title="Diferencia de goles">DG</th>
          <th title="Puntos">Pts</th>
          <th data-nosort class="hide-sm" title="Últimos 5 partidos registrados (antiguo → reciente)">Forma</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  </div>
  <div class="klegend">${legend}<span class="muted">Zonas según la fuente; pueden cambiar por copas o coeficientes UEFA.${league.source === "espn" ? " Clasificación: ESPN." : ""}</span></div>`;
  setTimeout(() => initAllTables(root), 50);
}

function standingsRow(row, index, o = {}) {
  const media = typeof entityMedia === "function" ? entityMedia("team", row.team) : "";
  const name = typeof teamDisplayName === "function" ? teamDisplayName(row.team) : row.team;
  // Posición por orden de la tabla (ya viene ordenada de football-data.org);
  // `row.position` puede empatar a inicio de temporada sin desempate aplicado.
  const pos = Number.isInteger(index) ? index + 1 : row.position;

  // Forma: primero desde fixtures.json (orden conocido); si no hay, la de la API.
  let form = typeof kdxTeamForm === "function" ? kdxTeamForm(o.fixtureLists, row.team, 5) : [];
  let formHtml;
  if (form.length) {
    formHtml = kdxFormPills(form.map(f => f.res), form.map(f => f.title));
  } else if (row.form) {
    formHtml = kdxFormPills(String(row.form).split(",").map(x => x.trim()).filter(Boolean).slice(-5));
  } else {
    formHtml = kdxFormPills([]);
  }

  const gd = Number(row.goal_diff) || 0;
  return `
  <tr${o.zone ? ` data-zone="${o.zone}" title="${CLASIF_ZONE_LABELS[o.zone]}"` : ""}${o.cut ? ' class="zone-cut"' : ""}>
    <td class="ctr" data-sort="${pos}"><span class="krank">${pos}</span></td>
    <td><span class="fx-team">${media}<b>${escHtml(name)}</b></span></td>
    <td class="num muted">${row.played}</td>
    <td class="num hide-xs">${row.won}</td>
    <td class="num hide-xs">${row.draw}</td>
    <td class="num hide-xs">${row.lost}</td>
    <td class="num hide-sm ${o.gfClass || ""}" data-sort="${row.goals_for}">${row.goals_for}</td>
    <td class="num hide-sm ${o.gaClass || ""}" data-sort="${row.goals_against}">${row.goals_against}</td>
    <td class="num" data-sort="${gd}">${typeof kdxDiff === "function" ? kdxDiff(gd, 0, false) : gd}</td>
    <td data-sort="${row.points}"><span class="kcell-bar"><span class="kpts">${row.points}</span>${typeof kdxBar === "function" ? kdxBar(row.points, o.maxPts || row.points, "brand") : ""}</span></td>
    <td class="hide-sm">${formHtml}</td>
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
  const list = league.scorers;
  const maxGoals = Math.max(...list.map(r => Number(r.goals) || 0), 1);
  const rankGpm = kdxRanker(list.map(r => r.played_matches ? r.goals / r.played_matches : null));
  root.innerHTML = `
  <div class="table-wrap">
    <table class="ktable">
      <thead>
        <tr>
          <th data-nosort class="ctr">#</th>
          <th>Jugador</th>
          <th class="hide-xs">Equipo</th>
          <th title="Goles">Goles</th>
          <th class="num hide-sm" title="Asistencias">Asist.</th>
          <th class="num" title="Partidos jugados">PJ</th>
          <th class="num" title="Goles por partido">Goles/p</th>
          <th class="num hide-sm" title="De penalti">Pen.</th>
        </tr>
      </thead>
      <tbody>
        ${list.map((row, i) => scorerRow(row, i, maxGoals, rankGpm)).join("")}
      </tbody>
    </table>
  </div>`;
  setTimeout(() => initAllTables(root), 50);
}

function scorerRow(row, index = 0, maxGoals = 1, rankGpm = () => null) {
  const teamName = typeof teamDisplayName === "function" ? teamDisplayName(row.team) : row.team;
  const crest = typeof entityMedia === "function" ? entityMedia("team", row.team) : "";
  const photo = typeof entityMedia === "function" ? entityMedia("player", row.player, row.team) : "";
  const gpm = row.played_matches ? row.goals / row.played_matches : null;
  const rank = Number(row.rank) || index + 1;
  return `
  <tr>
    <td class="ctr" data-sort="${rank}"><span class="krank ${rank <= 3 ? `krank--${rank}` : ""}">${rank}</span></td>
    <td><span class="player-cell">${photo}<b style="font-family:var(--font-ui)">${escHtml(row.player || "—")}</b></span></td>
    <td class="hide-xs"><span class="fx-team">${crest}<span class="muted">${escHtml(teamName)}</span></span></td>
    <td data-sort="${row.goals}"><span class="kcell-bar"><span class="kpts">${row.goals}</span>${kdxBar(row.goals, maxGoals, "gold")}</span></td>
    <td class="num hide-sm">${row.assists ?? "—"}</td>
    <td class="num muted">${row.played_matches ?? "—"}</td>
    <td class="num ${kdxHeatClass(rankGpm(gpm), "good")}" data-sort="${gpm ?? -1}">${gpm == null ? "—" : gpm.toFixed(2)}</td>
    <td class="num hide-sm muted">${row.penalties ?? "—"}</td>
  </tr>`;
}
