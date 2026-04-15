/**
 * h2h.js — Tab "H2H": head-to-head history, summary stats, goals chart
 */

"use strict";

let h2hGoalsChart = null;

function initH2H() {
  document.getElementById("h2h-run").addEventListener("click", runH2H);
}

function runH2H() {
  const t1 = document.getElementById("h2h-t1").value;
  const t2 = document.getElementById("h2h-t2").value;
  const box = document.getElementById("h2h-result");

  if (!t1 || !t2) {
    box.innerHTML = `<div class="state-box"><div class="icon">⚠️</div><p>Selecciona ambos equipos</p></div>`;
    return;
  }
  if (t1 === t2) {
    box.innerHTML = `<div class="state-box"><div class="icon">⚠️</div><p>Selecciona equipos diferentes</p></div>`;
    return;
  }

  const data = getH2H(t1, t2);
  if (!data || !data.matches || data.matches.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">📭</div><p>Sin historial disponible entre estos equipos</p></div>`;
    return;
  }

  // Determine canonical order from data
  const team1 = data.team1;
  const team2 = data.team2;

  box.innerHTML = buildH2HHTML(team1, team2, data);
  setTimeout(() => {
    drawH2HChart(team1, team2, data.matches);
    initAllTables(box);
  }, 50);
}

function buildH2HHTML(team1, team2, data) {
  const s = data.summary;
  const svgGoals = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/><path d="M12 2a14.5 14.5 0 0 0 0 20A14.5 14.5 0 0 0 12 2z"/><path d="M2 12h20"/></svg>`;
  const svgStats = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;
  const svgList  = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`;

  return `
  <!-- Title -->
  <div class="match-header" style="margin-bottom:24px;">
    <div class="teams">${team1} <span class="vs">VS</span> ${team2}</div>
    <div class="subtitle">${s.total} enfrentamientos históricos en la base de datos</div>
  </div>

  <!-- Summary boxes -->
  <div class="h2h-summary" style="margin-bottom:20px;">
    <div class="h2h-box">
      <div class="val" style="color:var(--green)">${s.wins1}</div>
      <div class="lbl">${team1.split(" ")[0]}</div>
    </div>
    <div class="h2h-box">
      <div class="val" style="color:var(--yellow)">${s.draws}</div>
      <div class="lbl">Empates</div>
    </div>
    <div class="h2h-box">
      <div class="val" style="color:var(--red)">${s.wins2}</div>
      <div class="lbl">${team2.split(" ")[0]}</div>
    </div>
    <div class="h2h-box">
      <div class="val">${fmt(s.avg_goals)}</div>
      <div class="lbl">Goles/p</div>
    </div>
    <div class="h2h-box">
      <div class="val">${pct(s.over25_rate)}</div>
      <div class="lbl">Over 2.5</div>
    </div>
    <div class="h2h-box">
      <div class="val">${pct(s.btts_rate)}</div>
      <div class="lbl">BTTS</div>
    </div>
  </div>

  <!-- Chart + table grid -->
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="chart-box">
      <div class="section-title">${svgGoals} Goles por partido</div>
      <canvas id="h2hGoalsChart" height="220"></canvas>
    </div>
    <div class="card">
      <div class="section-title">${svgStats} Estadísticas detalladas</div>
      ${buildH2HDetailStats(team1, team2, data.matches)}
    </div>
  </div>

  <!-- Full match table -->
  <div class="section-title">${svgList} Historial completo</div>
  <div class="table-wrap">
    ${buildH2HTable(team1, team2, data.matches)}
  </div>
  `;
}

function buildH2HDetailStats(team1, team2, matches) {
  const total = matches.length;
  if (total === 0) return "";

  let goalsOver3 = 0, goalsExact0 = 0;
  let t1wins = 0, t2wins = 0, draws = 0;

  matches.forEach(m => {
    const res = parseResult(m.result, team1, team2);
    if (!res) return;
    const tg = res.hg + res.ag;
    if (tg > 3) goalsOver3++;
    if (tg === 0) goalsExact0++;
    if (res.winner === "t1") t1wins++;
    else if (res.winner === "t2") t2wins++;
    else draws++;
  });

  return `
  <div>
    ${statRow("Partidos analizados",         total)}
    ${statRow(`Victorias ${team1.split(" ")[0]}`, t1wins + ` (${pct(t1wins/total)})`)}
    ${statRow("Empates",                      draws + ` (${pct(draws/total)})`)}
    ${statRow(`Victorias ${team2.split(" ")[0]}`, t2wins + ` (${pct(t2wins/total)})`)}
    ${statRow("Over 3 goles",                goalsOver3 + ` (${pct(goalsOver3/total)})`)}
    ${statRow("0-0 / Sin goles",             goalsExact0 + ` (${pct(goalsExact0/total)})`)}
  </div>`;
}

function buildH2HTable(team1, team2, matches) {
  const rows = matches.map(m => {
    const res = parseResult(m.result, team1, team2);
    const resultTag = !res ? `<span class="tag tag-d">${m.result}</span>` :
      res.winner === "t1" ? `<span class="tag tag-w">${m.result}</span>` :
      res.winner === "t2" ? `<span class="tag tag-l">${m.result}</span>` :
      `<span class="tag tag-d">${m.result}</span>`;

    const odds = [m.b365h, m.b365d, m.b365a].filter(Boolean).map(o => `<span class="badge-fair">${o}</span>`).join(" ");

    return `
    <tr>
      <td class="muted">${m.date || "—"}</td>
      <td>${resultTag}</td>
      <td class="muted">${m.league || "—"}</td>
      <td>${odds || `<span class="muted">—</span>`}</td>
    </tr>`;
  }).join("");

  return `
  <table>
    <thead>
      <tr>
        <th>Fecha</th>
        <th>Resultado</th>
        <th>Liga</th>
        <th>Cuotas B365</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;
}

/**
 * Parse "2-1 (HomeTeam)" or "HomeTeam 2-1 AwayTeam" style results.
 * Returns { hg, ag, winner: "t1"|"t2"|"draw" } or null.
 */
function parseResult(result, team1, team2) {
  if (!result) return null;
  const m = result.match(/(\d+)[–\-](\d+)/);
  if (!m) return null;
  const hg = parseInt(m[1]);
  const ag = parseInt(m[2]);
  let winner;
  if (hg > ag) winner = "t1";
  else if (hg < ag) winner = "t2";
  else winner = "draw";
  return { hg, ag, winner };
}

function drawH2HChart(team1, team2, matches) {
  const ctx = document.getElementById("h2hGoalsChart");
  if (!ctx) return;
  if (h2hGoalsChart) { h2hGoalsChart.destroy(); h2hGoalsChart = null; }

  const labels = [];
  const goalsH = [];
  const goalsA = [];

  matches.slice().reverse().forEach(m => {
    const r = parseResult(m.result, team1, team2);
    if (!r) return;
    labels.push(m.date ? m.date.slice(0, 7) : "—");
    goalsH.push(r.hg);
    goalsA.push(r.ag);
  });

  h2hGoalsChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: team1,
          data: goalsH,
          backgroundColor: "rgba(0,212,170,.7)",
          borderRadius: 3,
        },
        {
          label: team2,
          data: goalsA,
          backgroundColor: "rgba(255,75,75,.6)",
          borderRadius: 3,
        },
      ],
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
        legend: { labels: { color: "#e8eaf6", font: { size: 11 } } },
      },
    },
  });
}
