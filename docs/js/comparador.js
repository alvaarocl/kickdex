/**
 * comparador.js — Tab "Comparador": fixture header, stat-duel, form dots, radar, alerts
 */

"use strict";

let radarChart = null;

function initComparador() {
  document.getElementById("cmp-run").addEventListener("click", runComparador);
}

function runComparador() {
  const home    = document.getElementById("cmp-home").value;
  const away    = document.getElementById("cmp-away").value;
  const window_ = parseInt(document.getElementById("cmp-window").value) || 10;
  const box     = document.getElementById("cmp-result");

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

  homeData._name = home;
  awayData._name = away;

  const h2hData    = getH2H(home, away);
  const h2hSummary = h2hData?.summary || null;
  const probs      = calcProbabilities(homeData, awayData, h2hSummary);
  const alerts     = generateAlerts(homeData, awayData, h2hSummary);

  box.innerHTML = buildComparadorHTML(home, away, homeData, awayData, probs, alerts, h2hSummary)
    + buildPlayerComparison(home, away);

  setTimeout(() => {
    drawRadar(home, away, homeData, awayData);
    if (typeof triggerAnimations === "function") triggerAnimations(box);
  }, 50);
}

// ── Main HTML builder ──────────────────────────────────────

function buildComparadorHTML(home, away, homeData, awayData, probs, alerts, h2hSummary) {
  const hH = homeData.home || {};
  const aA = awayData.away || {};

  const svgDuel  = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;
  const svgHome  = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`;
  const svgAway  = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7 4.8 5.2a1 1 0 0 0-.8.3L2.7 7.7a.5.5 0 0 0 .1.7L7 11l-2 3H2l-1 1 3 2 2 3 1-1v-3l3-2 3.3 4.2a.5.5 0 0 0 .7.1l2.2-1.4a1 1 0 0 0 .3-.8z"/></svg>`;
  const svgRadar = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="2" x2="12" y2="22"/><path d="M2 8.5h20M2 15.5h20"/></svg>`;
  const svgAlert = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--yellow)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`;

  const homeWinRate = hH.win_rate != null ? pct(hH.win_rate) + " casa" : "Local";
  const awayWinRate = aA.win_rate != null ? pct(aA.win_rate) + " fuera" : "Visitante";

  return `
  <!-- ── Fixture header ── -->
  <div class="fixture-header stagger-item">
    <div class="fixture-team">
      ${typeof teamBadge === "function" ? teamBadge(home, 52) : ""}
      <div class="fixture-team-info">
        <div class="fixture-team-name">${home}</div>
        <div class="fixture-team-sub">${homeWinRate}</div>
      </div>
    </div>
    <div class="fixture-vs">
      <div class="fixture-vs-badge">VS</div>
      <div class="fixture-sub-text">Poisson</div>
    </div>
    <div class="fixture-team away">
      ${typeof teamBadge === "function" ? teamBadge(away, 52) : ""}
      <div class="fixture-team-info">
        <div class="fixture-team-name">${away}</div>
        <div class="fixture-team-sub">${awayWinRate}</div>
      </div>
    </div>
  </div>

  <!-- ── Stat duel comparison ── -->
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">${svgDuel} Comparativa de estadísticas <small>local vs visitante</small></div>
    ${buildStatDuel(home, away, hH, aA)}
  </div>

  <!-- ── Form logs ── -->
  <div class="grid-2 stagger-item" style="margin-bottom:20px;">
    <div class="card">
      <div class="section-title">${svgHome} ${home} <small>en casa</small></div>
      ${buildFormDots(hH)}
      ${buildMatchLog(hH.match_log)}
    </div>
    <div class="card">
      <div class="section-title">${svgAway} ${away} <small>fuera</small></div>
      ${buildFormDots(aA)}
      ${buildMatchLog(aA.match_log)}
    </div>
  </div>

  <!-- ── Probabilities ── -->
  ${probs ? buildProbSection(home, away, probs) : ""}

  <!-- ── Radar + Alerts ── -->
  <div class="grid-2 stagger-item" style="margin-bottom:20px;">
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

// ── Stat Duel (ValueStats-style) ──────────────────────────

function buildStatDuel(home, away, hStats, aStats) {
  const rows = [
    { label: "Victorias",    hv: hStats.win_rate,             av: aStats.win_rate,             max: 1,    pct: true                 },
    { label: "Goles/p",      hv: hStats.avg_goals,            av: aStats.avg_goals,            max: 3.5,  dec: 2                    },
    { label: "Gc enc./p",    hv: hStats.avg_goals_against,    av: aStats.avg_goals_against,    max: 3.5,  dec: 2,  invert: true     },
    { label: "xG proxy",     hv: hStats.avg_xg_proxy,         av: aStats.avg_xg_proxy,         max: 3.0,  dec: 2                    },
    { label: "Tiros/p",      hv: hStats.avg_shots,            av: aStats.avg_shots,            max: 22,   dec: 1                    },
    { label: "SoT/p",        hv: hStats.avg_shots_on,         av: aStats.avg_shots_on,         max: 10,   dec: 1                    },
    { label: "Córners/p",    hv: hStats.avg_corners,          av: aStats.avg_corners,          max: 14,   dec: 1                    },
    { label: "Over 2.5",     hv: hStats.over25_rate,          av: aStats.over25_rate,          max: 1,    pct: true                 },
    { label: "BTTS",         hv: hStats.btts_rate,            av: aStats.btts_rate,            max: 1,    pct: true                 },
    { label: "P. a cero",    hv: hStats.clean_sheet_rate,     av: aStats.clean_sheet_rate,     max: 1,    pct: true                 },
  ];

  // Column header row
  const header = `
  <div class="duel-header">
    <div style="text-align:right;font-size:.62rem;text-transform:uppercase;letter-spacing:1px;color:var(--brand);font-weight:800;">${home.split(" ")[0]}</div>
    <div></div>
    <div></div>
    <div></div>
    <div style="text-align:left;font-size:.62rem;text-transform:uppercase;letter-spacing:1px;color:#fb7185;font-weight:800;">${away.split(" ")[0]}</div>
  </div>`;

  const rowsHtml = rows.map(r => {
    const hv  = r.hv ?? 0;
    const av  = r.av ?? 0;
    const max = r.max || 1;

    // Bar width (0–100%) — higher is better for home (invert if lower is better, e.g. goals against)
    const hBar = Math.min(r.invert ? (max - hv) / max : hv / max, 1) * 100;
    const aBar = Math.min(r.invert ? (max - av) / max : av / max, 1) * 100;

    // Display value
    const hDisp = r.pct ? pct(hv) : fmt(hv, r.dec ?? 1);
    const aDisp = r.pct ? pct(av) : fmt(av, r.dec ?? 1);

    // Leading team highlight (considering direction)
    const hBetter = r.invert ? (hv < av) : (hv > av);
    const aBetter = r.invert ? (av < hv) : (av > hv);

    return `
    <div class="duel-row">
      <div class="duel-val-home${hBetter ? " leading" : ""}">${hDisp}</div>
      <div class="duel-track-home"><div class="duel-bar-home" style="width:${hBar.toFixed(1)}%"></div></div>
      <div class="duel-label">${r.label}</div>
      <div class="duel-track-away"><div class="duel-bar-away" style="width:${aBar.toFixed(1)}%"></div></div>
      <div class="duel-val-away${aBetter ? " leading" : ""}">${aDisp}</div>
    </div>`;
  }).join("");

  return `${header}<div class="stat-duel">${rowsHtml}</div>`;
}

// ── Form dots ─────────────────────────────────────────────

function buildFormDots(stats) {
  const log = stats.match_log;
  if (!log || log.length === 0) return "";
  const dots = log.slice(0, 10).map(m => {
    const r   = (m.result || "").toUpperCase();
    const cls = r === "W" ? "w" : r === "D" ? "d" : "l";
    const lbl = r === "W" ? "V" : r === "D" ? "E" : "D";
    return `<span class="form-dot ${cls}" title="${lbl}: ${m.opponent || ""} ${m.score || ""}"></span>`;
  }).join("");
  return `<div class="form-dots">${dots}</div>`;
}

// ── Match log ─────────────────────────────────────────────

function buildMatchLog(log) {
  if (!log || log.length === 0) return "";

  const venueIconHome = `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--brand);opacity:.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`;
  const venueIconAway = `<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--muted);opacity:.7"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7 4.8 5.2a1 1 0 0 0-.8.3L2.7 7.7a.5.5 0 0 0 .1.7L7 11l-2 3H2l-1 1 3 2 2 3 1-1v-3l3-2 3.3 4.2a.5.5 0 0 0 .7.1l2.2-1.4a1 1 0 0 0 .3-.8z"/></svg>`;

  const items = log.slice(0, 6).map(m => `
    <div class="match-row">
      ${wdlTag(m.result)}
      <span class="venue-icon" title="${m.venue === "C" || m.venue === "Home" ? "Local" : "Visitante"}">${m.venue === "C" || m.venue === "Home" ? venueIconHome : venueIconAway}</span>
      <b>${m.opponent}</b>
      <span class="score">${m.score || ""}</span>
    </div>`).join("");

  return `<hr/><div class="match-log" style="margin-top:8px;">${items}</div>`;
}

// ── Probability section ───────────────────────────────────

function buildProbSection(home, away, probs) {
  const impliedH = probs.home > 0 ? (1 / probs.home).toFixed(2) : "—";
  const impliedD = probs.draw > 0 ? (1 / probs.draw).toFixed(2) : "—";
  const impliedA = probs.away > 0 ? (1 / probs.away).toFixed(2) : "—";

  const maxP    = Math.max(probs.home, probs.draw, probs.away);
  const homeWin = probs.home === maxP ? "winner" : "";
  const drawWin = probs.draw === maxP ? "winner" : "";
  const awayWin = probs.away === maxP ? "winner" : "";

  return `
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Probabilidades Poisson
      <small>λ local: ${fmt(probs.lambda_h,2)} · λ visitante: ${fmt(probs.lambda_a,2)}</small>
    </div>

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

    <div style="border-top:1px solid var(--border);padding-top:16px;">
      ${probRow("Over 2.5 goles", probs.over25, "var(--blue)")}
      ${probRow("BTTS — Ambos marcan", probs.btts, "var(--purple)")}
    </div>
  </div>`;
}

// ── Alerts ────────────────────────────────────────────────

function buildAlertsHTML(alerts) {
  if (!alerts || alerts.length === 0) {
    return `<div style="color:var(--muted);font-size:.82rem;padding:8px 0;">No hay alertas significativas para este partido</div>`;
  }
  return `<div class="alerts-list">${alerts.map(a => {
    const cls = a.strength === "HIGH" ? "" : a.strength === "MEDIUM" ? "medium" : "low";
    return `<div class="alert-card ${cls}" title="Fuerza: ${a.strength}">${a.text}</div>`;
  }).join("")}</div>`;
}

// ── H2H mini section ──────────────────────────────────────

function buildH2HMiniSection(summary) {
  return `
  <div class="card stagger-item" style="margin-bottom:20px;">
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

// ── Radar chart ───────────────────────────────────────────

function drawRadar(home, away, homeData, awayData) {
  const ctx = document.getElementById("radarChart");
  if (!ctx) return;

  if (radarChart) { radarChart.destroy(); radarChart = null; }

  const hH = homeData.home || {};
  const aA = awayData.away  || {};

  const normalize = (val, max) => val != null ? Math.min(val / max, 1) * 100 : 0;

  const labels   = ["Goles/p", "Victorias", "Tiros/p", "xG proxy", "Over 2.5", "BTTS", "xDefensa"];
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

// ── Player comparison ─────────────────────────────────────

function buildPlayerComparison(home, away) {
  const homePlayers = (APP.players || {})[home] || [];
  const awayPlayers = (APP.players || {})[away] || [];

  const svgUsers = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`;

  if (!homePlayers.length && !awayPlayers.length) {
    return `
    <div class="card stagger-item" style="margin-bottom:20px;">
      <div class="section-title">${svgUsers} ${t("cmp_players_title")}</div>
      <p style="color:var(--muted);font-size:.85rem;">${t("cmp_players_none")}</p>
    </div>`;
  }

  function playerTable(players, teamName) {
    if (!players.length) {
      return `<div class="players-col-title">${teamName}</div>
              <p style="color:var(--muted);font-size:.82rem;">Sin datos</p>`;
    }
    const rows = players.slice(0, 8).map(p => `
      <tr>
        <td>${p.player}</td>
        <td class="mono">${fmt(p.sh, 1)}</td>
        <td class="mono">${fmt(p.sot, 1)}</td>
        <td class="mono">${fmt(p.gls, 2)}</td>
        <td class="mono">${fmt(p.ast, 2)}</td>
        <td class="mono">${p.fls != null ? fmt(p.fls, 1) : "—"}</td>
      </tr>`).join("");

    return `
    <div class="players-col-title">${teamName}</div>
    <div class="table-wrap" style="overflow-x:auto;">
      <table>
        <thead>
          <tr>
            <th>${t("player")}</th>
            <th title="${t("shots")}">${t("shots")}</th>
            <th title="${t("shots_on")}">${t("shots_on")}</th>
            <th title="${t("goals")}">${t("goals")}</th>
            <th title="${t("assists")}">${t("assists")}</th>
            <th>Faltas</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  return `
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">${svgUsers} ${t("cmp_players_title")} <small>últimos 10 partidos / jugador</small></div>
    <div class="players-comparison">
      <div>${playerTable(homePlayers, home)}</div>
      <div>${playerTable(awayPlayers, away)}</div>
    </div>
  </div>`;
}

// ── Legacy buildFormStats (kept for optional use) ─────────

function buildFormStats(stats) {
  if (!stats || Object.keys(stats).length === 0) {
    return `<div style="color:var(--muted);font-size:.8rem;">Sin datos</div>`;
  }
  const sv = (val, cls) => `<span class="stat-value ${cls || ""}">${val}</span>`;
  const winCls  = (v) => v >= .55 ? "good" : v <= .30 ? "bad" : "warn";
  const goalCls = (v) => v >= 1.8 ? "good" : v <= 0.9 ? "bad" : "";
  const gcCls   = (v) => v <= 0.9 ? "good" : v >= 2.0 ? "bad" : "warn";
  const rateCls = (v) => v >= .60 ? "warn" : v <= .25 ? "good" : "";
  const csCls   = (v) => v >= .35 ? "good" : v <= .10 ? "bad" : "";
  const xgCls   = (v) => v >= 1.4 ? "good" : v <= 0.7 ? "bad" : "";

  const wr = stats.win_rate ?? 0;
  const gf = stats.avg_goals ?? 0;
  const ga = stats.avg_goals_against ?? 0;
  const xg = stats.avg_xg_proxy ?? 0;
  const ov = stats.over25_rate ?? 0;
  const bt = stats.btts_rate ?? 0;
  const cs = stats.clean_sheet_rate ?? 0;

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
    <div class="stat-row"><span class="stat-label">Over 2.5</span>${sv(pct(ov), rateCls(ov))}</div>
    <div class="stat-row"><span class="stat-label">BTTS</span>${sv(pct(bt), rateCls(bt))}</div>
    <div class="stat-row"><span class="stat-label">Portería a cero</span>${sv(pct(cs), csCls(cs))}</div>
  </div>`;
}
