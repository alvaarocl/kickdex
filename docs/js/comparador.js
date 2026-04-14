/**
 * comparador.js — Tab "Comparador": form, probability bars, radar chart, alerts
 */

"use strict";

let radarChart = null;

function initComparador() {
  document.getElementById("cmp-run").addEventListener("click", runComparador);
}

function runComparador() {
  const home   = document.getElementById("cmp-home").value;
  const away   = document.getElementById("cmp-away").value;
  const window_ = parseInt(document.getElementById("cmp-window").value) || 10;

  const box = document.getElementById("cmp-result");

  if (!home || !away) {
    box.innerHTML = `<div class="state-box"><div class="icon">⚠️</div><p>Selecciona ambos equipos</p></div>`;
    return;
  }
  if (home === away) {
    box.innerHTML = `<div class="state-box"><div class="icon">⚠️</div><p>Selecciona equipos diferentes</p></div>`;
    return;
  }

  const homeData = APP.teamStats[home];
  const awayData = APP.teamStats[away];

  if (!homeData || !awayData) {
    box.innerHTML = `<div class="state-box"><div class="icon">📭</div><p>Sin datos suficientes para estos equipos</p></div>`;
    return;
  }

  // Attach names for alert generation
  homeData._name = home;
  awayData._name = away;

  const h2hData = getH2H(home, away);
  const h2hSummary = h2hData?.summary || null;

  const probs = calcProbabilities(homeData, awayData, h2hSummary);
  const alerts = generateAlerts(homeData, awayData, h2hSummary);

  box.innerHTML = buildComparadorHTML(home, away, homeData, awayData, probs, alerts, h2hSummary);

  // Draw radar after DOM is inserted
  setTimeout(() => drawRadar(home, away, homeData, awayData), 50);
}

function buildComparadorHTML(home, away, homeData, awayData, probs, alerts, h2hSummary) {
  const hH = homeData.home || {};
  const aA = awayData.away || {};

  return `
  <!-- Match header -->
  <div class="card" style="margin-bottom:20px;text-align:center;">
    <div style="font-size:1.1rem;font-weight:800;color:var(--text);margin-bottom:4px;">
      ${home} <span style="color:var(--muted);font-weight:400">vs</span> ${away}
    </div>
    <div style="color:var(--muted);font-size:.78rem;">Análisis basado en últimas jornadas · forma casa/visitante</div>
  </div>

  <div class="grid-2" style="margin-bottom:20px;">
    <!-- LOCAL stats -->
    <div class="card">
      <div class="section-title">🏠 ${home} <small>en casa</small></div>
      ${buildFormStats(hH)}
      ${buildMatchLog(hH.match_log)}
    </div>

    <!-- VISITANTE stats -->
    <div class="card">
      <div class="section-title">✈️ ${away} <small>fuera</small></div>
      ${buildFormStats(aA)}
      ${buildMatchLog(aA.match_log)}
    </div>
  </div>

  <!-- Probabilities -->
  ${probs ? buildProbSection(home, away, probs) : ""}

  <!-- Radar + Alerts -->
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="chart-box">
      <div class="section-title">📊 Radar comparativo</div>
      <canvas id="radarChart" height="260"></canvas>
    </div>
    <div class="card">
      <div class="section-title">🚨 Alertas inteligentes</div>
      ${buildAlertsHTML(alerts)}
    </div>
  </div>

  ${h2hSummary ? buildH2HMiniSection(h2hSummary) : ""}
  `;
}

function buildFormStats(stats) {
  if (!stats || Object.keys(stats).length === 0) {
    return `<div style="color:var(--muted);font-size:.8rem;">Sin datos</div>`;
  }
  return `
  <div>
    ${statRow("Partidos",           stats.n ?? "—")}
    ${statRow("Victorias",          pct(stats.win_rate))}
    ${statRow("Goles marcados/p",   fmt(stats.avg_goals))}
    ${statRow("Goles encajados/p",  fmt(stats.avg_goals_against))}
    ${statRow("Over 2.5",           pct(stats.over25_rate))}
    ${statRow("Ambos marcan",       pct(stats.btts_rate))}
  </div>`;
}

function buildMatchLog(log) {
  if (!log || log.length === 0) return "";
  const items = log.slice(0, 6).map(m => `
    <div class="match-row">
      ${wdlTag(m.result)}
      <span class="venue-icon">${m.venue === "Home" ? "🏠" : "✈️"}</span>
      <b>${m.opponent}</b>
      <span style="margin-left:auto">${m.score || ""}</span>
    </div>`).join("");
  return `<hr/><div class="match-log" style="margin-top:8px;">${items}</div>`;
}

function buildProbSection(home, away, probs) {
  const impliedH = probs.home > 0 ? (1 / probs.home).toFixed(2) : "—";
  const impliedD = probs.draw > 0 ? (1 / probs.draw).toFixed(2) : "—";
  const impliedA = probs.away > 0 ? (1 / probs.away).toFixed(2) : "—";

  return `
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">🎯 Probabilidades Poisson <small>λ local: ${fmt(probs.lambda_h,2)} · λ visitante: ${fmt(probs.lambda_a,2)}</small></div>
    ${probRow(`🏠 ${home}`,  probs.home,  "var(--green)")}
    ${probRow("🤝 Empate",   probs.draw,  "var(--yellow)")}
    ${probRow(`✈️ ${away}`,  probs.away,  "var(--red)")}
    <hr/>
    ${probRow("⚽ Over 2.5", probs.over25, "var(--blue)")}
    ${probRow("🎯 BTTS",     probs.btts,  "var(--purple)")}
    <div style="margin-top:12px;font-size:.75rem;color:var(--muted);">
      Cuotas justas estimadas: 1 → ${impliedH} · X → ${impliedD} · 2 → ${impliedA}
    </div>
  </div>`;
}

function buildAlertsHTML(alerts) {
  if (!alerts || alerts.length === 0) {
    return `<div style="color:var(--muted);font-size:.82rem;">No hay alertas significativas</div>`;
  }
  return `<div class="alerts-list">${alerts.map(a => {
    const cls = a.strength === "HIGH" ? "" : a.strength === "MEDIUM" ? "medium" : "low";
    return `<div class="alert-card ${cls}">${a.text}</div>`;
  }).join("")}</div>`;
}

function buildH2HMiniSection(summary) {
  return `
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">⚔️ Resumen H2H <small>${summary.total} partidos</small></div>
    <div class="h2h-summary">
      <div class="h2h-box"><div class="val" style="color:var(--green)">${summary.wins1}</div><div class="lbl">V equipo 1</div></div>
      <div class="h2h-box"><div class="val" style="color:var(--yellow)">${summary.draws}</div><div class="lbl">Empates</div></div>
      <div class="h2h-box"><div class="val" style="color:var(--red)">${summary.wins2}</div><div class="lbl">V equipo 2</div></div>
      <div class="h2h-box"><div class="val">${fmt(summary.avg_goals)}</div><div class="lbl">Goles/p</div></div>
      <div class="h2h-box"><div class="val">${pct(summary.over25_rate)}</div><div class="lbl">Over 2.5</div></div>
    </div>
  </div>`;
}

function drawRadar(home, away, homeData, awayData) {
  const ctx = document.getElementById("radarChart");
  if (!ctx) return;

  if (radarChart) { radarChart.destroy(); radarChart = null; }

  const hH = homeData.home || {};
  const aA = awayData.away  || {};

  const normalize = (val, max) => val != null ? Math.min(val / max, 1) * 100 : 0;

  const labels = ["Goles/p", "Victorias", "Over 2.5", "BTTS", "xDefensa"];
  const dataHome = [
    normalize(hH.avg_goals,        3.5),
    normalize(hH.win_rate,         1.0),
    normalize(hH.over25_rate,      1.0),
    normalize(hH.btts_rate,        1.0),
    normalize(1 - (hH.avg_goals_against ?? 1) / 3.5, 1.0),
  ];
  const dataAway = [
    normalize(aA.avg_goals,        3.5),
    normalize(aA.win_rate,         1.0),
    normalize(aA.over25_rate,      1.0),
    normalize(aA.btts_rate,        1.0),
    normalize(1 - (aA.avg_goals_against ?? 1) / 3.5, 1.0),
  ];

  radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: home,
          data: dataHome,
          borderColor: "rgba(0,212,170,.9)",
          backgroundColor: "rgba(0,212,170,.15)",
          pointBackgroundColor: "rgba(0,212,170,1)",
          pointRadius: 4,
        },
        {
          label: away,
          data: dataAway,
          borderColor: "rgba(255,75,75,.9)",
          backgroundColor: "rgba(255,75,75,.12)",
          pointBackgroundColor: "rgba(255,75,75,1)",
          pointRadius: 4,
        },
      ],
    },
    options: {
      scales: {
        r: {
          min: 0, max: 100,
          ticks: { display: false },
          grid:  { color: "rgba(255,255,255,.08)" },
          pointLabels: { color: "#8b9ab0", font: { size: 11 } },
          angleLines: { color: "rgba(255,255,255,.08)" },
        },
      },
      plugins: {
        legend: { labels: { color: "#e8eaf6", font: { size: 12 } } },
      },
    },
  });
}
