/**
 * jugadores.js — Tab "Jugadores": per-player stats, sparklines, detail table
 */

"use strict";

let sparkCharts = {};
let _jugMetric = "gls";
let _jugInit = false;

// Métricas del ranking (chips). label para cabecera de columna destacada.
const JUG_METRICS = {
  gls:  "Goles/p",
  ast:  "Asist/p",
  sh:   "Disp/p",
  sot:  "SoT/p",
  crdy: "TA/p",
  fls:  "Faltas/p",
  min:  "Min/p",
};

function initJugadores() {
  if (_jugInit) { renderJugadores(); return; }
  _jugInit = true;

  const runBtn = document.getElementById("jug-run");
  if (runBtn) runBtn.addEventListener("click", renderJugadores);

  document.getElementById("jug-team").addEventListener("change", () => {
    populatePlayerSelect();
    updatePlayerSuggestions();
    renderJugadores();
  });

  const leagueSel = document.getElementById("jugLeagueFilter");
  if (leagueSel) leagueSel.addEventListener("change", () => renderJugadores());

  // Chips de métrica → ordenación del ranking.
  document.querySelectorAll(".jug-metric-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      _jugMetric = chip.dataset.metric || "gls";
      document.querySelectorAll(".jug-metric-chip").forEach(c => c.classList.toggle("active", c === chip));
      const sortSel = document.getElementById("jug-sort");
      if (sortSel) sortSel.value = _jugMetric;
      renderJugadores();
    });
  });

  initPlayerSearch();

  const search = document.getElementById("jug-search");
  if (search) {
    search.addEventListener("input", () => {
      updatePlayerSuggestions();
      const team = document.getElementById("jug-team").value;
      const player = document.getElementById("jug-player").value;
      if (team && !player) renderJugadores();
    });
  }

  document.addEventListener("kdx:tab-open", e => {
    if (e.detail?.tab === "jugadores") renderJugadores();
  });

  renderJugadores();
}

// Dispatcher: jugador → ficha; equipo → jugadores del equipo; nada → ranking de liga.
function renderJugadores() {
  const team   = document.getElementById("jug-team")?.value || "";
  const player  = document.getElementById("jug-player")?.value || "";
  if (team) { runJugadores(); return; }

  const box = document.getElementById("jug-result");
  if (!box) return;
  const leagueCode = document.getElementById("jugLeagueFilter")?.value || "all";
  renderLeaderboard(box, leagueCode, _jugMetric);
}

// ── Ranking de liga (vista por defecto) ────────────────────────────────────

function renderLeaderboard(box, leagueCode, metric) {
  const teams = (typeof getPlayerTeamsByLeague === "function")
    ? getPlayerTeamsByLeague(leagueCode)
    : Object.keys(APP.players || {});

  const rows = [];
  teams.forEach(team => {
    (APP.players[team] || []).forEach(p => {
      if ((Number(p.min) || 0) < 1 && (Number(p[metric]) || 0) === 0) return; // descarta ruido
      rows.push({ ...p, _team: team });
    });
  });

  rows.sort((a, b) => (Number(b[metric]) || 0) - (Number(a[metric]) || 0)
                   || (Number(b.gls) || 0) - (Number(a.gls) || 0));

  const top = rows.slice(0, 60);
  const leagueName = leagueCode === "all"
    ? "todas las ligas con datos"
    : (APP.leagues?.[leagueCode]?.name || leagueCode);
  const metricLabel = JUG_METRICS[metric] || metric;

  if (!top.length) {
    box.className = "state-box";
    box.innerHTML = `<div class="icon">·</div><p>Sin datos de jugadores para ${escHtml(leagueName)}.</p>
      <p class="muted" style="font-size:.82rem;">La cobertura depende de FBref/Understat — SP1, E0, I1, D1 y F1 tienen datos; las segundas divisiones no.</p>`;
    return;
  }

  box.className = "";
  box.innerHTML = `
    <div class="section-title" style="margin-bottom:6px;">
      Ranking · ${escHtml(leagueName)}
      <small>top ${top.length} por ${escHtml(metricLabel.replace('/p',' por partido'))} · promedio de temporada</small>
    </div>
    <p class="muted" style="font-size:.78rem;margin-bottom:14px;">
      Promedios por partido de toda la temporada. La fuente no da estadísticas partido a partido, así que no hay ventana de últimos 5/10.
      ${chartHintHtml()}
    </p>
    <div class="table-wrap">
      <table id="jugLeaderTable">
        <thead>
          <tr>
            <th>#</th>
            <th>Jugador</th>
            <th>Equipo</th>
            ${leaderColHeader("gls", "Goles/p", metric)}
            ${leaderColHeader("ast", "Asist/p", metric)}
            ${leaderColHeader("sh", "Disp/p", metric)}
            ${leaderColHeader("sot", "SoT/p", metric)}
            ${metric === "fls" ? '<th class="sorted">Faltas/p</th>' : ''}
            ${leaderColHeader("min", "Min/p", metric)}
            ${leaderColHeader("crdy", "TA/p", metric)}
          </tr>
        </thead>
        <tbody>
          ${top.map((p, i) => `
          <tr data-team="${escAttr(p._team)}" data-player="${escAttr(p.player)}">
            <td class="muted">${i + 1}</td>
            <td><span class="player-cell">${typeof entityMedia === "function" ? entityMedia("player", p.player, p._team) : ""}<b><a href="${playerHref(p._team, p.player)}" onclick="event.stopPropagation()">${escHtml(p.player)}</a></b></span></td>
            <td class="muted">${escHtml(teamDisplayName(p._team))}</td>
            ${leaderCell(p, "gls", metric, 2)}
            ${leaderCell(p, "ast", metric, 2)}
            ${leaderCell(p, "sh", metric, 1)}
            ${leaderCell(p, "sot", metric, 1)}
            ${metric === "fls" ? `<td class="sorted"><b>${fmt(p.fls, 1)}</b></td>` : ''}
            ${leaderCell(p, "min", metric, 0)}
            ${leaderCell(p, "crdy", metric, 2)}
          </tr>`).join("")}
        </tbody>
      </table>
    </div>`;

  setTimeout(() => {
    initAllTables(box);
    box.querySelectorAll("#jugLeaderTable tbody tr").forEach(row => {
      row.style.cursor = "pointer";
      row.addEventListener("click", () => {
        const teamSel = document.getElementById("jug-team");
        const playerSel = document.getElementById("jug-player");
        if (teamSel) teamSel.value = row.dataset.team;
        populatePlayerSelect();
        if (playerSel) playerSel.value = row.dataset.player;
        renderJugadores();
        document.getElementById("tab-jugadores")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }, 50);
}

function jugBackToRanking() {
  const teamSel = document.getElementById("jug-team");
  const playerSel = document.getElementById("jug-player");
  if (teamSel) teamSel.value = "";
  if (playerSel) { while (playerSel.options.length > 1) playerSel.remove(1); playerSel.value = ""; }
  const search = document.getElementById("jug-search");
  if (search) search.value = "";
  renderJugadores();
}

function leaderColHeader(col, label, activeMetric) {
  return `<th class="${col === activeMetric ? "sorted" : ""}">${label}</th>`;
}

function leaderCell(p, col, activeMetric, dec) {
  const v = p[col];
  const disp = v == null ? "—" : fmt(v, dec);
  if (col === activeMetric) {
    return `<td class="sorted"><b>${disp}</b>${pctBadge(p[col + "_pct"])}</td>`;
  }
  return `<td>${disp}</td>`;
}

// Percentil vs la liga (players.json *_pct, de add_player_percentiles).
function pctBadge(pct) {
  if (pct == null) return "";
  const cls = pct >= 80 ? "jug-pct--hi" : pct >= 50 ? "jug-pct--mid" : "jug-pct--lo";
  return ` <span class="jug-pct ${cls}" title="Percentil ${pct} en su liga">P${pct}</span>`;
}

function chartHintHtml() {
  return `<span class="jug-sort-hint">⇧+clic en una cabecera para ordenar por varias columnas</span>`;
}

function initPlayerSearch() {
  const search = document.getElementById("jug-search");
  if (!search) return;

  let box = document.getElementById("jug-search-suggestions");
  if (!box) {
    box = document.createElement("div");
    box.id = "jug-search-suggestions";
    box.className = "player-suggestions";
    search.parentElement?.appendChild(box);
  }

  search.setAttribute("autocomplete", "off");
  search.addEventListener("keydown", e => {
    if (e.key !== "Enter") return;
    const first = box.querySelector(".player-suggestion");
    if (!first) return;
    e.preventDefault();
    selectPlayerSuggestion(first.dataset.team, first.dataset.player);
  });

  document.addEventListener("click", e => {
    if (!box.contains(e.target) && e.target !== search) box.hidden = true;
  });
}

function populatePlayerSelect() {
  const team = document.getElementById("jug-team").value;
  const sel  = document.getElementById("jug-player");
  while (sel.options.length > 1) sel.remove(1);

  if (!team || !APP.playersDetail[team]) return;

  const players = Object.keys(APP.playersDetail[team]).sort();
  players.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p; opt.textContent = p;
    sel.appendChild(opt);
  });
}

function updatePlayerSuggestions() {
  const search = document.getElementById("jug-search");
  const box = document.getElementById("jug-search-suggestions");
  if (!search || !box) return;

  const q = normalizePlayerText(search.value);
  if (q.length < 2) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }

  const candidates = getPlayerSearchCandidates();
  const matches = candidates
    .map(item => ({ ...item, score: scorePlayerMatch(item.player, q) }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score || a.player.localeCompare(b.player, "es"))
    .slice(0, 8);

  if (!matches.length) {
    box.hidden = false;
    box.innerHTML = `<div class="player-suggestion-empty">Sin coincidencias</div>`;
    return;
  }

  box.hidden = false;
  box.innerHTML = matches.map(item => `
    <button type="button" class="player-suggestion" data-team="${escAttr(item.team)}" data-player="${escAttr(item.player)}">
      ${typeof entityMedia === "function" ? entityMedia("player", item.player, item.team) : ""}
      <span><b>${escHtml(item.player)}</b><small>${escHtml(teamDisplayName(item.team))} · ${escHtml(item.league || "Liga")}</small></span>
    </button>
  `).join("");

  box.querySelectorAll(".player-suggestion").forEach(btn => {
    btn.addEventListener("click", () => selectPlayerSuggestion(btn.dataset.team, btn.dataset.player));
  });
}

function getPlayerSearchCandidates() {
  const selectedTeam = document.getElementById("jug-team")?.value || "";
  const leagueFilter = document.getElementById("jugLeagueFilter")?.value || "all";
  const teams = selectedTeam
    ? [selectedTeam]
    : getPlayerTeamsByLeague(leagueFilter);

  const result = [];
  teams.forEach(team => {
    const players = APP.playersDetail?.[team] ? Object.keys(APP.playersDetail[team]) : [];
    const leagueCode = getLeagueForTeam(team);
    const league = APP.leagues?.[leagueCode]?.name || leagueCode || "";
    players.forEach(player => result.push({ team, player, league }));
  });
  return result;
}

function scorePlayerMatch(player, query) {
  const name = normalizePlayerText(player);
  if (!name) return 0;
  if (name === query) return 100;
  if (name.startsWith(query)) return 90;
  if (name.includes(query)) return 70;
  const parts = name.split(" ");
  if (parts.some(part => part.startsWith(query))) return 60;
  return 0;
}

function selectPlayerSuggestion(team, player) {
  if (!team || !player) return;
  const teamSel = document.getElementById("jug-team");
  const playerSel = document.getElementById("jug-player");
  const search = document.getElementById("jug-search");
  const box = document.getElementById("jug-search-suggestions");

  if (teamSel) teamSel.value = team;
  populatePlayerSelect();
  if (playerSel) playerSel.value = player;
  if (search) search.value = player;
  if (box) box.hidden = true;
  runJugadores();
}

function runJugadores() {
  const team   = document.getElementById("jug-team").value;
  const player = document.getElementById("jug-player").value;
  const box    = document.getElementById("jug-result");
  if (!team) { renderJugadores(); return; }

  box.className = "";

  // Destroy old sparklines
  Object.values(sparkCharts).forEach(c => c.destroy());
  sparkCharts = {};

  const backLink = `<button class="jug-back" onclick="jugBackToRanking()">&larr; volver al ranking</button>`;

  if (player) {
    // Single player detail
    const allDetail = APP.playersDetail[team]?.[player];
    if (!allDetail || allDetail.length === 0) {
      box.className = "state-box";
      box.innerHTML = `<div class="icon">·</div><p>Sin datos para este jugador</p>`;
      return;
    }
    const detail = allDetail;
    box.innerHTML = backLink + buildPlayerDetail(team, player, detail);
    setTimeout(() => {
      drawPlayerSparklines(player, detail);
      initAllTables(box);
    }, 50);
  } else {
    // All players summary
    const players = filterAndSortPlayers(APP.players[team] || []);
    if (!players || players.length === 0) {
      box.className = "state-box";
      box.innerHTML = `<div class="icon">·</div><p>Sin datos de jugadores para este equipo</p>`;
      return;
    }
    box.innerHTML = backLink + buildTeamPlayersHTML(team, players);
    setTimeout(() => {
      drawTeamSparklines(team);
      initAllTables(box);
      // Wire row clicks to open player detail
      box.querySelectorAll("#playersTable tbody tr").forEach(row => {
        row.style.cursor = "pointer";
        row.addEventListener("click", () => {
          const playerName = row.cells[0]?.querySelector("b")?.textContent;
          if (!playerName) return;
          const sel = document.getElementById("jug-player");
          if (sel) {
            sel.value = playerName;
            runJugadores();
          }
        });
      });
    }, 50);
  }
}

// ── Team overview ──────────────────────────────────────────────────────────

function buildTeamPlayersHTML(team, players) {
  const svgUser = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`;
  const leagueCode = getLeagueForTeam(team);
  const leagueName = APP.leagues?.[leagueCode]?.name || "Liga";
  const updatedAt = APP.dataStatus?.updated_at ? new Date(APP.dataStatus.updated_at).toLocaleString("es-ES") : "actualizacion diaria";
  return `
  <div class="section-title" style="margin-bottom:16px;">
    ${svgUser} ${teamDisplayName(team)} <small>${leagueName} · ${players.length} jugadores · actualizado ${updatedAt}</small>
  </div>
  ${buildTeamPlayerSummary(players)}
  <div class="table-wrap">
    <table id="playersTable">
      <thead>
        <tr>
          <th>Jugador</th>
          <th title="Minutos por partido">Min/p</th>
          <th title="Disparos">Disp/p</th>
          <th title="Disparos a puerta">SoT/p</th>
          <th title="Goles">Goles/p</th>
          <th title="Asistencias">Ast/p</th>
          <th title="Faltas">Faltas/p</th>
          <th title="Tarjetas amarillas">TA/p</th>
          <th>Tendencia goles</th>
        </tr>
      </thead>
      <tbody>
        ${players.map(p => buildPlayerRow(team, p)).join("")}
      </tbody>
    </table>
  </div>`;
}
function buildPlayerRow(team, p) {
  const sparkId = `spark-${sanitizeId(team)}-${sanitizeId(p.player)}`;
  return `
  <tr>
    <td><span class="player-cell">${typeof entityMedia === "function" ? entityMedia("player", p.player, team) : ""}<b><a href="${playerHref(team, p.player)}" onclick="event.stopPropagation()">${escHtml(p.player)}</a></b></span></td>
    <td>${fmt(p.min, 0)}</td>
    <td>${fmt(p.sh, 1)}</td>
    <td>${fmt(p.sot, 1)}</td>
    <td>${fmt(p.gls, 2)}</td>
    <td>${fmt(p.ast, 2)}</td>
    <td>${fmt(p.fls, 1)}</td>
    <td>${p.crdy != null ? fmt(p.crdy, 2) : "—"}</td>
    <td><canvas id="${sparkId}" width="80" height="30" style="display:block;"></canvas></td>
  </tr>`;
}

function drawTeamSparklines(team) {
  const players = filterAndSortPlayers(APP.players[team] || []);
  if (!players) return;

  players.forEach(p => {
    const detail = APP.playersDetail[team]?.[p.player];
    if (!detail || detail.length === 0) return;

    const id = `spark-${sanitizeId(team)}-${sanitizeId(p.player)}`;
    const ctx = document.getElementById(id);
    if (!ctx) return;

    const data = detail.slice(0, 10).reverse().map(d => d.gls ?? 0);
    sparkCharts[id] = new Chart(ctx, sparklineConfig(data, "rgba(0,212,170,.8)"));
  });
}

// ── Single player detail ───────────────────────────────────────────────────

function buildPlayerDetail(team, player, detail) {
  const avg = aggregatePlayerStats(detail);
  const hasMatchLog = hasPlayerMatchLog(detail);
  const profileUrl = playerHref(team, player);
  const svgUser = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
  const svgGls  = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/><path d="M12 2a14.5 14.5 0 0 0 0 20A14.5 14.5 0 0 0 12 2z"/><path d="M2 12h20"/></svg>`;
  const svgShot = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--blue)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;
  const svgList = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`;
  return `
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">${svgUser} ${player} <small>${teamDisplayName(team)} · <a href="${profileUrl}">abrir perfil completo</a></small></div>
    <div class="grid-4" style="margin-bottom:16px;">
      ${miniCard("Disparos/p",   fmt(avg.sh, 1), "var(--blue)")}
      ${miniCard("SoT/p",        fmt(avg.sot, 1), "var(--green)")}
      ${miniCard("Goles/p",      fmt(avg.gls, 2), "var(--green)")}
      ${miniCard("Asist/p",      fmt(avg.ast, 2), "var(--purple)")}
    </div>
    <div class="grid-4">
      ${miniCard("Min/p",        fmt(avg.min, 0), "var(--text)")}
      ${miniCard("Faltas/p",     fmt(avg.fls, 1), "var(--orange)")}
      ${miniCard("Tarj. Am./p",  fmt(avg.crdy, 2), "var(--yellow)")}
      ${miniCard(hasMatchLog ? "Registros" : "Datos", hasMatchLog ? detail.length : "Prom. temporada", "var(--muted)")}
    </div>
  </div>

  ${hasMatchLog ? `
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="chart-box">
      <div class="section-title">${svgGls} Goles por partido</div>
      <canvas id="sparkGls" height="120"></canvas>
    </div>
    <div class="chart-box">
      <div class="section-title">${svgShot} Disparos a puerta</div>
      <canvas id="sparkSot" height="120"></canvas>
    </div>
  </div>

  <div class="section-title">${svgList} Detalle disponible <small>${detail.length} registros</small></div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Goles</th>
          <th>Asist</th>
          <th>Min</th>
          <th>Disp</th>
          <th>SoT</th>
          <th>Faltas</th>
          <th>T. Am.</th>
        </tr>
      </thead>
      <tbody>
        ${detail.map(d => `
        <tr>
          <td class="muted">${d.date}</td>
          <td>${d.gls > 0 ? `<b style="color:var(--green)">${d.gls}</b>` : d.gls ?? "—"}</td>
          <td>${d.ast > 0 ? `<b style="color:var(--blue)">${d.ast}</b>` : d.ast ?? "—"}</td>
          <td>${d.min ?? "—"}</td>
          <td>${d.sh ?? "—"}</td>
          <td>${d.sot ?? "—"}</td>
          <td>${d.fls ?? "—"}</td>
          <td>${d.crdy > 0 ? `<b style="color:var(--yellow)">${d.crdy}</b>` : d.crdy ?? "—"}</td>
        </tr>`).join("")}
      </tbody>
    </table>
  </div>` : `
  <div class="card player-data-note">
    <div class="section-title">${svgList} Promedios de temporada</div>
    <p>La fuente disponible para este jugador es agregada por temporada, no partido a partido. Por eso no se muestran últimos 5/10 ni una tabla de registros individuales.</p>
  </div>`}`;
}

function drawPlayerSparklines(player, detail) {
  if (!hasPlayerMatchLog(detail)) return;
  const gls  = detail.slice().reverse().map(d => d.gls  ?? 0);
  const sot  = detail.slice().reverse().map(d => d.sot  ?? 0);
  const labels = detail.slice().reverse().map(d => d.date ? d.date.slice(5) : "");

  const glsCtx = document.getElementById("sparkGls");
  const sotCtx = document.getElementById("sparkSot");

  if (glsCtx) sparkCharts["sparkGls"] = new Chart(glsCtx, lineConfig(labels, gls, "rgba(0,212,170,.9)", "Goles"));
  if (sotCtx) sparkCharts["sparkSot"] = new Chart(sotCtx, lineConfig(labels, sot, "rgba(41,182,246,.9)", "SoT"));
}

// ── Chart helpers ──────────────────────────────────────────────────────────

function sparklineConfig(data, color) {
  return {
    type: "bar",
    data: {
      labels: data.map((_, i) => i + 1),
      datasets: [{ data, backgroundColor: color, borderRadius: 2 }],
    },
    options: {
      responsive: false,
      animation: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { display: false },
        y: { display: false, min: 0 },
      },
    },
  };
}

function lineConfig(labels, data, color, label) {
  return {
    type: "line",
    data: {
      labels,
      datasets: [{
        label,
        data,
        borderColor: color,
        backgroundColor: color.replace("0.9", "0.1"),
        tension: 0.3,
        fill: true,
        pointRadius: 3,
        pointHoverRadius: 5,
      }],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          ticks: { color: "#8b9ab0", font: { size: 10 }, maxRotation: 45 },
          grid:  { color: "rgba(255,255,255,.05)" },
        },
        y: {
          ticks: { color: "#8b9ab0", stepSize: 1 },
          grid:  { color: "rgba(255,255,255,.05)" },
          min: 0,
        },
      },
      plugins: {
        legend: { labels: { color: "#e8eaf6", font: { size: 12 } } },
      },
    },
  };
}

// ── Utilities ──────────────────────────────────────────────────────────────

function aggregatePlayerStats(detail) {
  const n = detail.length || 1;
  const sum = key => detail.reduce((acc, d) => acc + (d[key] ?? 0), 0);
  return {
    sh:   sum("sh")   / n,
    sot:  sum("sot")  / n,
    gls:  sum("gls")  / n,
    ast:  sum("ast")  / n,
    min:  sum("min")  / n,
    fls:  sum("fls")  / n,
    crdy: sum("crdy") / n,
  };
}

function miniCard(label, value, color) {
  return `
  <div class="card" style="text-align:center;padding:14px 10px;">
    <div class="card-title">${label}</div>
    <div class="card-value" style="color:${color}">${value}</div>
  </div>`;
}

function sanitizeId(str) {
  return str.replace(/[^a-z0-9]/gi, "_");
}

function filterAndSortPlayers(players) {
  const q = normalizePlayerText(document.getElementById("jug-search")?.value || "");
  const sortKey = document.getElementById("jug-sort")?.value || "sh";
  return (players || [])
    .filter(p => !q || normalizePlayerText(p.player).includes(q))
    .slice()
    .sort((a, b) => (Number(b[sortKey]) || 0) - (Number(a[sortKey]) || 0));
}

function normalizePlayerText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function hasPlayerMatchLog(detail) {
  return (detail || []).some(d => {
    const date = String(d.date || "").trim().toLowerCase();
    return date && date !== "nat" && date !== "nan" && date !== "none";
  });
}

function escAttr(str) {
  return escHtml(str).replace(/'/g, "&#39;");
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function playerHref(team, player) {
  const params = new URLSearchParams({ team: team || "", player: player || "" });
  return `player.html?${params.toString()}`;
}

function getLeagueForTeam(team) {
  for (const [code, data] of Object.entries(APP.leagues || {})) {
    if ((data.teams || []).includes(team)) return code;
  }
  return null;
}

function buildTeamPlayerSummary(players) {
  const topGoals = players.slice().sort((a, b) => (b.gls || 0) - (a.gls || 0))[0];
  const topShots = players.slice().sort((a, b) => (b.sh || 0) - (a.sh || 0))[0];
  const topSot = players.slice().sort((a, b) => (b.sot || 0) - (a.sot || 0))[0];
  return `
  <div class="grid-4" style="margin-bottom:16px;">
    ${miniCard("Jugadores", players.length, "var(--text)")}
    ${miniCard("Goles/p lider", topGoals ? `${topGoals.player} · ${fmt(topGoals.gls, 2)}` : "—", "var(--green)")}
    ${miniCard("Disparos/p lider", topShots ? `${topShots.player} · ${fmt(topShots.sh, 1)}` : "—", "var(--blue)")}
    ${miniCard("SoT/p lider", topSot ? `${topSot.player} · ${fmt(topSot.sot, 1)}` : "—", "var(--purple)")}
  </div>`;
}
