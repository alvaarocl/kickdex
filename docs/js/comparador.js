/**
 * comparador.js — Tab "Comparador": fixture header, stat-duel, form dots, radar, alerts, players, calculator
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
    + buildPlayerComparison(home, away)
    + buildMasterCalculatorJS(home, away);

  setTimeout(() => {
    drawRadar(home, away, homeData, awayData);
    if (typeof initAllTables === "function") initAllTables(box);
    if (typeof triggerAnimations === "function") triggerAnimations(box);
    initAllTables(box);
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
      <div class="fixture-team-info">
        <div class="fixture-team-name">${home}</div>
        <div class="fixture-team-sub">${homeWinRate}</div>
      </div>
    </div>
    <div class="fixture-vs">
      <div class="fixture-vs-badge">VS</div>
      <div class="fixture-sub-text">KICKDEX</div>
    </div>
    <div class="fixture-team away">
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

  const header = `
  <div class="duel-header">
    <div style="text-align:right;font-size:.62rem;text-transform:uppercase;letter-spacing:1px;color:var(--brand);font-weight:800;">${home.split(" ")[0]}</div>
    <div></div><div></div><div></div>
    <div style="text-align:left;font-size:.62rem;text-transform:uppercase;letter-spacing:1px;color:#fb7185;font-weight:800;">${away.split(" ")[0]}</div>
  </div>`;

  const rowsHtml = rows.map(r => {
    const hv = r.hv ?? 0; const av = r.av ?? 0; const max = r.max || 1;
    const hBar = Math.min(r.invert ? (max - hv) / max : hv / max, 1) * 100;
    const aBar = Math.min(r.invert ? (max - av) / max : av / max, 1) * 100;
    const hDisp = r.pct ? pct(hv) : fmt(hv, r.dec ?? 1);
    const aDisp = r.pct ? pct(av) : fmt(av, r.dec ?? 1);
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

function buildFormDots(stats) {
  const log = stats.match_log;
  if (!log || log.length === 0) return "";
  const dots = log.slice(0, 10).map(m => {
    const r = (m.result || "").toUpperCase();
    const cls = r === "W" ? "w" : r === "D" ? "d" : "l";
    return `<span class="form-dot ${cls}"></span>`;
  }).join("");
  return `<div class="form-dots">${dots}</div>`;
}

function buildMatchLog(log) {
  if (!log || log.length === 0) return "";
  const items = log.slice(0, 6).map(m => `
    <div class="match-row">
      ${wdlTag(m.result)}
      <b>${m.opponent}</b>
      <span class="score">${m.score || ""}</span>
    </div>`).join("");
  return `<hr/><div class="match-log" style="margin-top:8px;">${items}</div>`;
}

function buildProbSection(home, away, probs) {
  const impliedH = probs.home > 0 ? (1 / probs.home).toFixed(2) : "—";
  const impliedD = probs.draw > 0 ? (1 / probs.draw).toFixed(2) : "—";
  const impliedA = probs.away > 0 ? (1 / probs.away).toFixed(2) : "—";
  const maxP = Math.max(probs.home, probs.draw, probs.away);
  const homeWin = probs.home === maxP ? "winner" : "";
  const drawWin = probs.draw === maxP ? "winner" : "";
  const awayWin = probs.away === maxP ? "winner" : "";

  return `
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">Probabilidades KICKDEX</div>
    <div class="prob-1x2">
      <div class="prob-1x2-box ${homeWin}"><div class="prob-1x2-label">1</div><div class="prob-1x2-pct">${(probs.home*100).toFixed(1)}%</div><div class="prob-1x2-odds">≈ ${impliedH}</div></div>
      <div class="prob-1x2-box ${drawWin}"><div class="prob-1x2-label">X</div><div class="prob-1x2-pct">${(probs.draw*100).toFixed(1)}%</div><div class="prob-1x2-odds">≈ ${impliedD}</div></div>
      <div class="prob-1x2-box ${awayWin}"><div class="prob-1x2-label">2</div><div class="prob-1x2-pct">${(probs.away*100).toFixed(1)}%</div><div class="prob-1x2-odds">≈ ${impliedA}</div></div>
    </div>
    <div style="border-top:1px solid var(--border);padding-top:16px;">
      ${probRow("Over 2.5 goles", probs.over25, "var(--blue)")}
      ${probRow("BTTS — Ambos marcan", probs.btts, "var(--purple)")}
    </div>
  </div>`;
}

function buildAlertsHTML(alerts) {
  if (!alerts || alerts.length === 0) return `<div class="muted">No hay alertas</div>`;
  return `<div class="alerts-list">${alerts.map(a => `<div class="alert-card ${a.strength.toLowerCase()}">${a.text}</div>`).join("")}</div>`;
}

function buildH2HMiniSection(summary) {
  return `
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">Resumen H2H <small>${summary.total} partidos</small></div>
    <div class="h2h-summary">
      <div class="h2h-box"><div class="val" style="color:var(--green)">${summary.wins1}</div><div class="lbl">V Local</div></div>
      <div class="h2h-box"><div class="val" style="color:var(--yellow)">${summary.draws}</div><div class="lbl">Empates</div></div>
      <div class="h2h-box"><div class="val" style="color:var(--red)">${summary.wins2}</div><div class="lbl">V Vis.</div></div>
      <div class="h2h-box"><div class="val">${fmt(summary.avg_goals)}</div><div class="lbl">Goles/p</div></div>
      <div class="h2h-box"><div class="val">${pct(summary.over25_rate)}</div><div class="lbl">O2.5</div></div>
    </div>
  </div>`;
}

function drawRadar(home, away, homeData, awayData) {
  const ctx = document.getElementById("radarChart"); if (!ctx) return;
  if (radarChart) { radarChart.destroy(); }
  const hH = homeData.home || {}; const aA = awayData.away || {};
  const normalize = (v, m) => v != null ? Math.min(v / m, 1) * 100 : 0;
  radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels: ["Goles", "Victorias", "Tiros", "xG", "Over 2.5", "BTTS", "Defensa"],
      datasets: [
        { label: home, data: [normalize(hH.avg_goals, 3), normalize(hH.win_rate, 1), normalize(hH.avg_shots, 20), normalize(hH.avg_xg_proxy, 2.5), normalize(hH.over25_rate, 1), normalize(hH.btts_rate, 1), normalize(1-hH.avg_goals_against/3, 1)], borderColor: "rgba(0,212,170,1)", backgroundColor: "rgba(0,212,170,0.1)" },
        { label: away, data: [normalize(aA.avg_goals, 3), normalize(aA.win_rate, 1), normalize(aA.avg_shots, 20), normalize(aA.avg_xg_proxy, 2.5), normalize(aA.over25_rate, 1), normalize(aA.btts_rate, 1), normalize(1-aA.avg_goals_against/3, 1)], borderColor: "#fb7185", backgroundColor: "rgba(251,113,133,0.1)" }
      ]
    },
    options: { scales: { r: { min: 0, max: 100, ticks: { display: false }, grid: { color: "rgba(255,255,255,0.05)" } } }, plugins: { legend: { labels: { color: "#8b9ab0" } } } }
  });
}

// ── Player comparison ─────────────────────────────────────

function buildPlayerComparison(home, away) {
  const homePlayers = (APP.players || {})[home] || [];
  const awayPlayers = (APP.players || {})[away] || [];

  if (!homePlayers.length && !awayPlayers.length) return "";

  function playerTable(players, teamName) {
    if (!players.length) {
      return `<div class="players-col-title">${teamName}</div>
              <p style="color:var(--muted);font-size:.82rem;">Sin datos</p>`;
    }
    const rows = players.map(p => `
      <tr>
        <td>${p.player}</td>
        <td class="mono">${fmt(p.sh, 1)}</td>
        <td class="mono">${fmt(p.sot, 1)}</td>
        <td class="mono">${fmt(p.gls, 1)}</td>
        <td class="mono">${fmt(p.ast, 1)}</td>
        <td class="mono">${p.fls ? fmt(p.fls, 1) : "—"}</td>
      </tr>`).join("");

    return `
    <div class="players-col-title">${teamName}</div>
    <div class="table-wrap" style="overflow-x:auto; max-height:450px; overflow-y:auto;">
      <table>
        <thead><tr><th>Jugador</th><th>Sh</th><th>SoT</th><th>Gls</th><th>Ast</th><th>Fls</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  return `
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">📊 Comparativa de Jugadores Pro</div>
    <div class="players-comparison">
      <div>${playerTable(homePlayers, home)}</div>
      <div>${playerTable(awayPlayers, away)}</div>
    </div>
  </div>`;
}

// ── Master Calculator (JS Version) ────────────────────────

function buildMasterCalculatorJS(home, away) {
  return `
  <div class="card stagger-item" style="margin-bottom:40px; border: 1px solid var(--brand-dim);">
    <div class="section-title">🔍 KICKDEX Terminal — Calculadora Multidimensional</div>
    <p class="muted" style="margin-bottom:20px;">Análisis profundo por equipo y jugador (Versión Web Ligera)</p>
    
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
      <div class="calc-box" style="background:rgba(255,255,255,0.02); padding:15px; border-radius:8px;">
        <h4 style="color:var(--brand); font-size:0.85rem; margin-top:0;">ANÁLISIS EQUIPO: ${home}</h4>
        <div id="calc-result-home">Selecciona métrica para calcular...</div>
      </div>
      <div class="calc-box" style="background:rgba(255,255,255,0.02); padding:15px; border-radius:8px;">
        <h4 style="color:#fb7185; font-size:0.85rem; margin-top:0;">ANÁLISIS EQUIPO: ${away}</h4>
        <div id="calc-result-away">Selecciona métrica para calcular...</div>
      </div>
    </div>
  </div>`;
}
