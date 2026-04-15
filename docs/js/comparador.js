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

  const svgHome = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`;
  const svgAway = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7 4.8 5.2a1 1 0 0 0-.8.3L2.7 7.7a.5.5 0 0 0 .1.7L7 11l-2 3H2l-1 1 3 2 2 3 1-1v-3l3-2 3.3 4.2a.5.5 0 0 0 .7.1l2.2-1.4a1 1 0 0 0 .3-.8z"/></svg>`;
  const svgRadar = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="2" x2="12" y2="22"/><path d="M2 8.5h20M2 15.5h20"/></svg>`;
  const svgAlert = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--yellow)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`;

  return `
  <!-- Match header -->
  <div class="match-header" style="margin-bottom:24px;">
    <div class="teams">${home} <span class="vs">VS</span> ${away}</div>
    <div class="subtitle">Análisis Poisson · forma casa/visitante · últimas jornadas</div>
  </div>

  <div class="grid-2" style="margin-bottom:20px;">
    <!-- LOCAL stats -->
    <div class="card">
      <div class="section-title">${svgHome} ${home} <small>en casa</small></div>
      ${buildFormStats(hH)}
      ${buildMatchLog(hH.match_log)}
    </div>

    <!-- VISITANTE stats -->
    <div class="card">
      <div class="section-title">${svgAway} ${away} <small>fuera</small></div>
      ${buildFormStats(aA)}
      ${buildMatchLog(aA.match_log)}
    </div>
  </div>

  <!-- Probabilities -->
  ${probs ? buildProbSection(home, away, probs) : ""}

  <!-- Radar + Alerts -->
  <div class="grid-2" style="margin-bottom:20px;">
    <div class="chart-box">
      <div class="section-title">${svgRadar} Radar comparativo</div>
      <canvas id="radarChart" height="270"></canvas>
    </div>
    <div class="card">
      <div class="section-title">${svgAlert} Alertas inteligentes</div>
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

  // Helper: color-coded stat value
  const sv = (val, cls) => `<span class="stat-value ${cls || ""}">${val}</span>`;
  const winCls  = (v) => v >= .55 ? "good" : v <= .30 ? "bad" : "warn";
  const goalCls = (v) => v >= 1.8 ? "good" : v <= 0.9 ? "bad" : "";
  const gcCls   = (v) => v <= 0.9 ? "good" : v >= 2.0 ? "bad" : "warn";
  const rateCls = (v) => v >= .60 ? "warn" : v <= .25 ? "good" : "";
  const csCls   = (v) => v >= .35 ? "good" : v <= .10 ? "bad" : "";
  const xgCls   = (v) => v >= 1.4 ? "good" : v <= 0.7 ? "bad" : "";

  const wr  = stats.win_rate ?? 0;
  const gf  = stats.avg_goals ?? 0;
  const ga  = stats.avg_goals_against ?? 0;
  const xg  = stats.avg_xg_proxy ?? 0;
  const ov  = stats.over25_rate ?? 0;
  const bt  = stats.btts_rate ?? 0;
  const cs  = stats.clean_sheet_rate ?? 0;

  return `
  <div>
    <div class="stat-row"><span class="stat-label">Partidos</span>${sv(stats.matches_analyzed ?? stats.n ?? "—")}</div>
    <div class="stat-row"><span class="stat-label">Victorias</span>${sv(pct(wr), winCls(wr))}</div>
    <div class="stat-row"><span class="stat-label">Goles marcados/p</span>${sv(fmt(gf), goalCls(gf))}</div>
    <div class="stat-row"><span class="stat-label">Goles encajados/p</span>${sv(fmt(ga), gcCls(ga))}</div>
    <div class="stat-row"><span class="stat-label">xG proxy/p</span>${sv(fmt(xg), xgCls(xg))}</div>
    <div class="stat-row"><span class="stat-label">Tiros/p</span>${sv(fmt(stats.avg_shots, 1))}</div>
    <div class="stat-row"><span class="stat-label">Tiros a puerta/p</span>${sv(fmt(stats.avg_shots_on, 1))}</div>
    <div class="stat-row"><span class="stat-label">Córners/p</span>${sv(fmt(stats.avg_corners, 1))}</div>
    <div class="stat-row"><span class="stat-label">Tarjetas/p</span>${sv(fmt(stats.avg_cards, 1))}</div>
    <div class="stat-row"><span class="stat-label">Over 2.5</span>${sv(pct(ov), rateCls(ov))}</div>
    <div class="stat-row"><span class="stat-label">Ambos marcan</span>${sv(pct(bt), rateCls(bt))}</div>
    <div class="stat-row"><span class="stat-label">Portería a cero</span>${sv(pct(cs), csCls(cs))}</div>
  </div>`;
}

function buildMatchLog(log) {
  if (!log || log.length === 0) return "";

  const venueIconHome = `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--brand);opacity:.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`;
  const venueIconAway = `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--muted);opacity:.8"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7 4.8 5.2a1 1 0 0 0-.8.3L2.7 7.7a.5.5 0 0 0 .1.7L7 11l-2 3H2l-1 1 3 2 2 3 1-1v-3l3-2 3.3 4.2a.5.5 0 0 0 .7.1l2.2-1.4a1 1 0 0 0 .3-.8z"/></svg>`;

  const items = log.slice(0, 6).map(m => `
    <div class="match-row">
      ${wdlTag(m.result)}
      <span class="venue-icon" title="${m.venue === "C" || m.venue === "Home" ? "Local" : "Visitante"}">${m.venue === "C" || m.venue === "Home" ? venueIconHome : venueIconAway}</span>
      <b>${m.opponent}</b>
      <span class="score">${m.score || ""}</span>
    </div>`).join("");
  return `<hr/><div class="match-log" style="margin-top:8px;">${items}</div>`;
}

function buildProbSection(home, away, probs) {
  const impliedH = probs.home > 0 ? (1 / probs.home).toFixed(2) : "—";
  const impliedD = probs.draw > 0 ? (1 / probs.draw).toFixed(2) : "—";
  const impliedA = probs.away > 0 ? (1 / probs.away).toFixed(2) : "—";

  // Determine winner for highlight
  const maxP = Math.max(probs.home, probs.draw, probs.away);
  const homeWin = probs.home === maxP ? "winner" : "";
  const drawWin = probs.draw === maxP ? "winner" : "";
  const awayWin = probs.away === maxP ? "winner" : "";

  return `
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Probabilidades Poisson
      <small>λ local: ${fmt(probs.lambda_h,2)} · λ visitante: ${fmt(probs.lambda_a,2)}</small>
    </div>

    <!-- 1X2 Big display -->
    <div class="prob-1x2" style="margin-bottom:18px;">
      <div class="prob-1x2-box ${homeWin}">
        <div class="prob-1x2-label">1 — Local</div>
        <div class="prob-1x2-pct" style="color:${homeWin ? "var(--brand)" : "var(--text)"}">${(probs.home*100).toFixed(1)}%</div>
        <div class="prob-1x2-odds">≈ ${impliedH}</div>
      </div>
      <div class="prob-1x2-box ${drawWin}">
        <div class="prob-1x2-label">X — Empate</div>
        <div class="prob-1x2-pct" style="color:${drawWin ? "var(--brand)" : "var(--text)"}">${(probs.draw*100).toFixed(1)}%</div>
        <div class="prob-1x2-odds">≈ ${impliedD}</div>
      </div>
      <div class="prob-1x2-box ${awayWin}">
        <div class="prob-1x2-label">2 — Visitante</div>
        <div class="prob-1x2-pct" style="color:${awayWin ? "var(--brand)" : "var(--text)"}">${(probs.away*100).toFixed(1)}%</div>
        <div class="prob-1x2-odds">≈ ${impliedA}</div>
      </div>
    </div>

    <!-- Over/BTTS bars -->
    <div style="border-top:1px solid var(--border);padding-top:16px;">
      ${probRow("Over 2.5 goles", probs.over25, "var(--blue)")}
      ${probRow("BTTS — Ambos marcan", probs.btts, "var(--purple)")}
    </div>
  </div>`;
}

function buildAlertsHTML(alerts) {
  if (!alerts || alerts.length === 0) {
    return `<div style="color:var(--muted);font-size:.82rem;padding:8px 0;">No hay alertas significativas para este partido</div>`;
  }
  return `<div class="alerts-list">${alerts.map(a => {
    const cls = a.strength === "HIGH" ? "" : a.strength === "MEDIUM" ? "medium" : "low";
    return `<div class="alert-card ${cls}" title="Fuerza: ${a.strength}">${a.text}</div>`;
  }).join("")}</div>`;
}

function buildH2HMiniSection(summary) {
  return `
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M11 18H8a2 2 0 0 1-2-2V9"/></svg>
      Resumen H2H
      <small>${summary.total} partidos históricos</small>
    </div>
    <div class="h2h-summary">
      <div class="h2h-box"><div class="val" style="color:var(--green)">${summary.wins1}</div><div class="lbl">V equipo 1</div></div>
      <div class="h2h-box"><div class="val" style="color:var(--yellow)">${summary.draws}</div><div class="lbl">Empates</div></div>
      <div class="h2h-box"><div class="val" style="color:var(--red)">${summary.wins2}</div><div class="lbl">V equipo 2</div></div>
      <div class="h2h-box"><div class="val">${fmt(summary.avg_goals)}</div><div class="lbl">Goles/p</div></div>
      <div class="h2h-box"><div class="val">${pct(summary.over25_rate)}</div><div class="lbl">Over 2.5</div></div>
      <div class="h2h-box"><div class="val">${pct(summary.btts_rate ?? 0)}</div><div class="lbl">BTTS</div></div>
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

  const labels = ["Goles/p", "Victorias", "Tiros/p", "xG proxy", "Over 2.5", "BTTS", "xDefensa"];
  const dataHome = [
    normalize(hH.avg_goals,        3.5),
    normalize(hH.win_rate,         1.0),
    normalize(hH.avg_shots,        22),
    normalize(hH.avg_xg_proxy,     3.0),
    normalize(hH.over25_rate,      1.0),
    normalize(hH.btts_rate,        1.0),
    normalize(1 - (hH.avg_goals_against ?? 1) / 3.5, 1.0),
  ];
  const dataAway = [
    normalize(aA.avg_goals,        3.5),
    normalize(aA.win_rate,         1.0),
    normalize(aA.avg_shots,        22),
    normalize(aA.avg_xg_proxy,     3.0),
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
