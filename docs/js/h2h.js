/**
 * h2h.js — Tab "H2H": head-to-head history, summary stats, goals chart
 *
 * Fase 0.6: usa los campos separados home/away/home_score/away_score de
 * h2h.json en vez de parsear la cadena "result". initH2H/runH2H eliminados
 * (buscaban #h2h-run, #h2h-t1, #h2h-t2, #h2h-result que no existen en
 * ninguna página). parseResult eliminado.
 */

"use strict";

let h2hGoalsChart = null;

function buildH2HHTML(team1, team2, data) {
  const s = data.summary;
  const svgGoals = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/><path d="M12 2a14.5 14.5 0 0 0 0 20A14.5 14.5 0 0 0 12 2z"/><path d="M2 12h20"/></svg>`;
  const svgStats = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;
  const svgList  = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`;

  return `
  <!-- Title -->
  <div class="match-header" style="margin-bottom:24px;">
    <div class="teams">${teamDisplayName(team1)} <span class="vs">VS</span> ${teamDisplayName(team2)}</div>
    <div class="subtitle">${s.total} enfrentamientos históricos en la base de datos</div>
  </div>

  <!-- Summary boxes -->
  <div class="h2h-summary" style="margin-bottom:20px;">
    <div class="h2h-box">
      <div class="val" style="color:var(--green)">${s.wins1}</div>
      <div class="lbl">${teamShortLabel(team1)}</div>
    </div>
    <div class="h2h-box">
      <div class="val" style="color:var(--yellow)">${s.draws}</div>
      <div class="lbl">Empates</div>
    </div>
    <div class="h2h-box">
      <div class="val" style="color:var(--red)">${s.wins2}</div>
      <div class="lbl">${teamShortLabel(team2)}</div>
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
    if (m.home_score == null || m.away_score == null) return;
    const t1IsHome = m.home === team1;
    const t1g = t1IsHome ? m.home_score : m.away_score;
    const t2g = t1IsHome ? m.away_score : m.home_score;
    const tg = m.home_score + m.away_score;
    if (tg > 3) goalsOver3++;
    if (tg === 0) goalsExact0++;
    if (t1g > t2g) t1wins++;
    else if (t1g < t2g) t2wins++;
    else draws++;
  });

  return `
  <div>
    ${statRow("Partidos analizados",         total)}
    ${statRow(`Victorias ${teamShortLabel(team1)}`, t1wins + ` (${pct(t1wins/total)})`)}
    ${statRow("Empates",                      draws + ` (${pct(draws/total)})`)}
    ${statRow(`Victorias ${teamShortLabel(team2)}`, t2wins + ` (${pct(t2wins/total)})`)}
    ${statRow("Over 3 goles",                goalsOver3 + ` (${pct(goalsOver3/total)})`)}
    ${statRow("0-0 / Sin goles",             goalsExact0 + ` (${pct(goalsExact0/total)})`)}
  </div>`;
}

function buildH2HTable(team1, team2, matches) {
  const rows = matches.map(m => {
    let scoreStr;
    let winnerClass = "tag-d";

    if (m.home_score != null && m.away_score != null) {
      const homeDisplay = teamDisplayName(m.home || "");
      const awayDisplay = teamDisplayName(m.away || "");
      scoreStr = `${homeDisplay} ${m.home_score}-${m.away_score} ${awayDisplay}`;
      const t1IsHome = m.home === team1;
      const t1g = t1IsHome ? m.home_score : m.away_score;
      const t2g = t1IsHome ? m.away_score : m.home_score;
      if (t1g > t2g) winnerClass = "tag-w";
      else if (t1g < t2g) winnerClass = "tag-l";
    } else {
      // Fallback al campo result (retrocompat)
      scoreStr = m.result || "?-?";
    }

    return `
    <tr>
      <td class="muted">${m.date || "—"}</td>
      <td><span class="tag ${winnerClass}">${scoreStr}</span></td>
      <td class="muted">${m.league || "—"}</td>
    </tr>`;
  }).join("");

  return `
  <table>
    <thead>
      <tr>
        <th>Fecha</th>
        <th>Resultado</th>
        <th>Liga</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function drawH2HChart(team1, team2, matches) {
  const ctx = document.getElementById("h2hGoalsChart");
  if (!ctx) return;
  if (h2hGoalsChart) { h2hGoalsChart.destroy(); h2hGoalsChart = null; }

  const labels = [];
  const goalsH = [];
  const goalsA = [];

  matches.slice().reverse().forEach(m => {
    if (m.home_score == null || m.away_score == null) return;
    const t1IsHome = m.home === team1;
    const t1g = t1IsHome ? m.home_score : m.away_score;
    const t2g = t1IsHome ? m.away_score : m.home_score;
    labels.push(m.date ? m.date.slice(0, 7) : "—");
    goalsH.push(t1g);
    goalsA.push(t2g);
  });

  h2hGoalsChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: teamDisplayName(team1),
          data: goalsH,
          backgroundColor: "rgba(0,212,170,.7)",
          borderRadius: 3,
        },
        {
          label: teamDisplayName(team2),
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
