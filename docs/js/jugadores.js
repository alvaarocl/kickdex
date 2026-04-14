/**
 * jugadores.js — Tab "Jugadores": per-player stats, sparklines, detail table
 */

"use strict";

let sparkCharts = {};

function initJugadores() {
  document.getElementById("jug-run").addEventListener("click", runJugadores);

  document.getElementById("jug-team").addEventListener("change", () => {
    populatePlayerSelect();
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

function runJugadores() {
  const team   = document.getElementById("jug-team").value;
  const player = document.getElementById("jug-player").value;
  const box    = document.getElementById("jug-result");

  if (!team) {
    box.innerHTML = `<div class="state-box"><div class="icon">⚠️</div><p>Selecciona un equipo</p></div>`;
    return;
  }

  // Destroy old sparklines
  Object.values(sparkCharts).forEach(c => c.destroy());
  sparkCharts = {};

  if (player) {
    // Single player detail
    const detail = APP.playersDetail[team]?.[player];
    if (!detail || detail.length === 0) {
      box.innerHTML = `<div class="state-box"><div class="icon">📭</div><p>Sin datos para este jugador</p></div>`;
      return;
    }
    box.innerHTML = buildPlayerDetail(team, player, detail);
    setTimeout(() => drawPlayerSparklines(player, detail), 50);
  } else {
    // All players summary
    const players = APP.players[team];
    if (!players || players.length === 0) {
      box.innerHTML = `<div class="state-box"><div class="icon">📭</div><p>Sin datos de jugadores para este equipo</p></div>`;
      return;
    }
    box.innerHTML = buildTeamPlayersHTML(team, players);
    setTimeout(() => drawTeamSparklines(team), 50);
  }
}

// ── Team overview ──────────────────────────────────────────────────────────

function buildTeamPlayersHTML(team, players) {
  return `
  <div class="section-title" style="margin-bottom:16px;">
    👤 ${team} — ${players.length} jugadores (temporada actual)
  </div>
  <div class="table-wrap">
    <table id="playersTable">
      <thead>
        <tr>
          <th>Jugador</th>
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
    <td><b>${p.player}</b></td>
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
  const players = APP.players[team];
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
  return `
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">👤 ${player} <small>${team}</small></div>
    <div class="grid-4" style="margin-bottom:16px;">
      ${miniCard("Disparos/p",   fmt(avg.sh, 1), "var(--blue)")}
      ${miniCard("SoT/p",        fmt(avg.sot, 1), "var(--green)")}
      ${miniCard("Goles/p",      fmt(avg.gls, 2), "var(--green)")}
      ${miniCard("Asist/p",      fmt(avg.ast, 2), "var(--purple)")}
    </div>
    <div class="grid-4">
      ${miniCard("Faltas/p",     fmt(avg.fls, 1), "var(--orange)")}
      ${miniCard("Tarj. Am./p",  fmt(avg.crdy, 2), "var(--yellow)")}
      ${miniCard("Partidos",     detail.length, "var(--muted)")}
      ${miniCard("Minutas +90",  detail.filter(d => d.gls > 0).length + " con goles", "var(--text)")}
    </div>
  </div>

  <!-- Sparkline charts -->
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="chart-box">
      <div class="section-title">⚽ Goles por partido</div>
      <canvas id="sparkGls" height="120"></canvas>
    </div>
    <div class="chart-box">
      <div class="section-title">🎯 Disparos a puerta</div>
      <canvas id="sparkSot" height="120"></canvas>
    </div>
  </div>

  <!-- Per-game table -->
  <div class="section-title">📋 Detalle por partido (últimos ${detail.length})</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Goles</th>
          <th>Asist</th>
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
          <td>${d.sh ?? "—"}</td>
          <td>${d.sot ?? "—"}</td>
          <td>${d.fls ?? "—"}</td>
          <td>${d.crdy > 0 ? `<b style="color:var(--yellow)">${d.crdy}</b>` : d.crdy ?? "—"}</td>
        </tr>`).join("")}
      </tbody>
    </table>
  </div>`;
}

function drawPlayerSparklines(player, detail) {
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
    fls:  sum("fls")  / n,
    crdy: sum("crdy") / n,
  };
}

function miniCard(label, value, color) {
  return `
  <div class="card" style="text-align:center;padding:12px;">
    <div class="card-title">${label}</div>
    <div class="card-value" style="color:${color}">${value}</div>
  </div>`;
}

function sanitizeId(str) {
  return str.replace(/[^a-z0-9]/gi, "_");
}
