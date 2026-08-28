/**
 * comparador.js — Tab "Comparador": compara dos equipos cualesquiera.
 *
 * Fase 2: los bloques de análisis (duelo, probabilidades, forma, H2H,
 * jugadores, alertas, frecuencias) viven en js/blocks/*.js y se comparten
 * con la ficha de partido (match.js). Aquí solo quedan lo propio del
 * Comparador: la cabecera de enfrentamiento, el radar y el Match Report.
 */

"use strict";

let radarChart = null;

function emptyTeamStats(team) {
  return { team, home: null, away: null, sample_scope: 'none', season_matches: 0, historical_matches: 0 };
}

// matches_analyzed = partidos reales incluidos; effective_matches = tamaño de
// muestra "efectivo" tras el decaimiento por antigüedad (get_weighted_form).
function sampleLabel(data, venue) {
  const block = data?.[venue];
  const count = Number(block?.matches_analyzed || 0);
  if (!count) return 'sin historial';
  const suffix = count === 1 ? ' partido' : ' partidos';
  const effective = block?.effective_matches;
  const weightNote = Number.isFinite(effective) ? ` (peso efectivo ≈${Math.round(effective * 10) / 10})` : '';
  return count + suffix + weightNote;
}

function hasThinSample(homeData, awayData) {
  const homeEff = Number(homeData?.home?.effective_matches ?? Infinity);
  const awayEff = Number(awayData?.away?.effective_matches ?? Infinity);
  return Math.min(homeEff, awayEff) < 3;
}

function statsForVenue(data, venue) {
  return data?.[venue] || data?.[venue === 'home' ? 'away' : 'home'] || {};
}

function initComparador() {
  document.getElementById("cmp-run").addEventListener("click", runComparador);
}

// Contexto que consumen los bloques compartidos (js/blocks/*.js).
function buildComparadorCtx(home, away, probs) {
  return {
    homeVenue:   "home",
    awayVenue:   "away",
    window:      "l20",
    teamStats:   APP.teamStats,
    h2h:         APP.h2h,
    modelConfig: APP.modelConfig,
    alerts:      APP.alerts,
    probs,
    // El Comparador no analiza un fixture concreto: sin league/date, el bloque
    // de alertas cae al generateAlerts() en vivo (fallback previsto).
    league: null,
    date:   null,
  };
}

function runComparador() {
  const home = document.getElementById("cmp-home").value;
  const away = document.getElementById("cmp-away").value;
  const box  = document.getElementById("cmp-result");

  if (!home || !away) {
    box.innerHTML = `<div class="state-box"><div class="icon">!</div><p>Selecciona ambos equipos</p></div>`;
    return;
  }
  if (home === away) {
    box.innerHTML = `<div class="state-box"><div class="icon">!</div><p>Selecciona equipos diferentes</p></div>`;
    return;
  }

  const homeData = APP.teamStats[home] || emptyTeamStats(home);
  const awayData = APP.teamStats[away] || emptyTeamStats(away);

  const h2hData    = getH2H(home, away);
  const h2hSummary = h2hData?.summary || null;
  const probs      = calcProbabilities(homeData, awayData, h2hSummary, APP.modelConfig);
  const ctx        = buildComparadorCtx(home, away, probs);

  box.innerHTML =
      buildComparadorHTML(home, away, homeData, awayData, ctx, h2hData, h2hSummary)
    + buildExportReport(home, away, probs);

  setTimeout(() => {
    drawRadar(home, away, homeData, awayData);
    if (h2hData?.matches?.length && typeof drawH2HChart === "function") {
      drawH2HChart(h2hData.team1, h2hData.team2, h2hData.matches);
    }
    if (typeof triggerAnimations === "function") triggerAnimations(box);
    initAllTables(box);
  }, 50);
}

// ── Main HTML builder ──────────────────────────────────────

function buildComparadorHTML(home, away, homeData, awayData, ctx, h2hData, h2hSummary) {
  const hH = statsForVenue(homeData, 'home');
  const aA = statsForVenue(awayData, 'away');

  const svgRadar = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="2" x2="12" y2="22"/><path d="M2 8.5h20M2 15.5h20"/></svg>`;
  const svgAlert = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`;

  const homeWinRate = hH.win_rate != null ? pct(hH.win_rate) + " casa" : "Local";
  const awayWinRate = aA.win_rate != null ? pct(aA.win_rate) + " fuera" : "Visitante";

  return `
  <div class="fixture-header stagger-item">
    <div class="fixture-team">
      ${typeof entityMedia === "function" ? entityMedia("team", home, "", "entity-media--hero") : ""}
      <div class="fixture-team-info">
        <div class="fixture-team-name">${teamDisplayName(home)}</div>
        <div class="fixture-team-sub">${homeWinRate}</div>
      </div>
    </div>
    <div class="fixture-vs">
      <div class="fixture-vs-badge">VS</div>
      <div class="fixture-sub-text">KICKDEX</div>
    </div>
    <div class="fixture-team away">
      ${typeof entityMedia === "function" ? entityMedia("team", away, "", "entity-media--hero") : ""}
      <div class="fixture-team-info">
        <div class="fixture-team-name">${teamDisplayName(away)}</div>
        <div class="fixture-team-sub">${awayWinRate}</div>
      </div>
    </div>
  </div>

  <div class='cmp-sample-note'>Muestra disponible: ${sampleLabel(homeData, 'home')} · ${sampleLabel(awayData, 'away')}. Ponderado por antigüedad — los partidos recientes pesan más.${hasThinSample(homeData, awayData) ? ' Peso efectivo bajo: el análisis es orientativo.' : ''}</div>

  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">Comparativa de estadísticas <small>local vs visitante</small></div>
    ${buildBlockStatDuel(home, away, ctx)}
  </div>

  ${ctx.probs ? `
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">Modelo KICKDEX</div>
    ${buildBlockProbabilities(home, away, ctx)}
  </div>` : ""}

  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">Frecuencias de apuesta <small>con muestra</small></div>
    ${buildBlockHitRates(home, away, ctx)}
  </div>

  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">Forma reciente</div>
    ${buildBlockForm(home, away, ctx)}
  </div>

  <div class="grid-2 stagger-item" style="margin-bottom:20px;">
    <div class="chart-box">
      <div class="section-title">${svgRadar} Radar comparativo</div>
      <canvas id="radarChart" height="270"></canvas>
    </div>
    <div class="card">
      <div class="section-title">${svgAlert} Alertas inteligentes</div>
      ${buildBlockAlerts(home, away, ctx)}
    </div>
  </div>

  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">Jugadores destacados <span class="jug-sort-hint">⇧+clic en cabecera para ordenar por varias</span></div>
    ${buildBlockPlayers(home, away, ctx)}
  </div>

  ${buildH2HIntegratedSection(home, away, h2hData, h2hSummary, ctx)}
  `;
}

function buildH2HIntegratedSection(home, away, h2hData, h2hSummary, ctx) {
  if (h2hData?.matches?.length || h2hSummary) {
    return `
    <div class="stagger-item" style="margin-bottom:20px;">
      <div class="section-title">H2H completo <small>integrado en el comparador</small></div>
      ${buildBlockH2H(home, away, ctx)}
    </div>`;
  }
  return `
  <div class="card stagger-item" style="margin-bottom:20px;">
    <div class="section-title">H2H completo</div>
    <p class="muted" style="font-size:.85rem;">Sin historial disponible entre ${teamDisplayName(home)} y ${teamDisplayName(away)}.</p>
  </div>`;
}

function drawRadar(home, away, homeData, awayData) {
  const ctx = document.getElementById("radarChart"); if (!ctx) return;
  if (radarChart) { radarChart.destroy(); }
  const hH = statsForVenue(homeData, 'home'); const aA = statsForVenue(awayData, 'away');
  const normalize = (v, m) => v != null ? Math.min(v / m, 1) * 100 : 0;
  radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels: ["Goles", "Victorias", "Tiros", "xG", "Over 2.5", "BTTS", "Defensa"],
      datasets: [
        { label: teamDisplayName(home), data: [normalize(hH.avg_goals, 3), normalize(hH.win_rate, 1), normalize(hH.avg_shots, 20), normalize(hH.avg_xg_proxy, 2.5), normalize(hH.over25_rate, 1), normalize(hH.btts_rate, 1), normalize(1-hH.avg_goals_against/3, 1)], borderColor: "rgba(46,230,166,1)", backgroundColor: "rgba(46,230,166,0.1)" },
        { label: teamDisplayName(away), data: [normalize(aA.avg_goals, 3), normalize(aA.win_rate, 1), normalize(aA.avg_shots, 20), normalize(aA.avg_xg_proxy, 2.5), normalize(aA.over25_rate, 1), normalize(aA.btts_rate, 1), normalize(1-aA.avg_goals_against/3, 1)], borderColor: "#F5B93C", backgroundColor: "rgba(245,185,60,0.1)" }
      ]
    },
    options: { scales: { r: { min: 0, max: 100, ticks: { display: false }, grid: { color: "rgba(255,255,255,0.05)" } } }, plugins: { legend: { labels: { color: "#8A94AB" } } } }
  });
}

// ── Export report ──────────────────────────────────────────

function buildExportReport(home, away, probs) {
  const homeLabel = teamDisplayName(home);
  const awayLabel = teamDisplayName(away);
  const params = new URLSearchParams({
    home: homeLabel,
    away: awayLabel,
    homeKey: home,
    awayKey: away,
    league: "KICKDEX analysis",
  });
  const url = `report.html?${params.toString()}`;
  return `
  <div class="card stagger-item" style="margin-bottom:40px; text-align:center; padding:28px 24px;">
    <div class="section-title" style="justify-content:center;">Match Report</div>
    <p style="color:var(--muted);font-size:.85rem;margin-bottom:16px;line-height:1.55;">
      Genera un report en una página (light mode) con el análisis del partido. Compartible en WhatsApp, X o como PDF.
    </p>
    <a href="${url}" target="_blank" rel="noopener"
       class="btn btn-primary"
       style="display:inline-flex;align-items:center;gap:8px;text-decoration:none;font-family:var(--font-data);">
      &gt; export report_
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3h7v7"/><path d="M10 14L21 3"/><path d="M21 14v7H3V3h7"/></svg>
    </a>
  </div>`;
}
