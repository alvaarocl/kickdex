/**
 * blocks/alerts.js — Panel de alertas inteligentes.
 * Lee APP.alerts (ctx.alerts) por clave partido; si no hay JSON de alertas,
 * cae al generateAlerts() de app.js (disponible en index.html pero no en match.html).
 *
 * buildBlockAlerts(homeTeam, awayTeam, ctx)
 *   ctx.alerts  — APP.alerts (o null si no está cargado)
 *   ctx.league  — código de liga (para la clave de partido)
 *   ctx.date    — fecha del partido (para la clave)
 *   ctx.teamStats, ctx.h2h — usados como fallback para generateAlerts()
 */
"use strict";

function buildBlockAlerts(homeTeam, awayTeam, ctx) {
  let alerts = null;

  // 1. Intentar leer de alerts.json (clave canónica: {league}|{date}|{home}|{away})
  if (ctx.alerts && ctx.league && ctx.date) {
    const key = ctx.league + "|" + ctx.date + "|" + homeTeam + "|" + awayTeam;
    const found = ctx.alerts.matches && ctx.alerts.matches[key];
    if (found && found.length) alerts = found;
  }

  // 2. Fallback a generateAlerts() de app.js (solo disponible en index.html)
  if (!alerts && typeof generateAlerts === "function" && ctx.teamStats) {
    const homeData = Object.assign({}, (ctx.teamStats || {})[homeTeam] || {});
    const awayData = Object.assign({}, (ctx.teamStats || {})[awayTeam] || {});
    homeData._name = homeTeam;
    awayData._name = awayTeam;
    const h2dData = _blkGetH2H(homeTeam, awayTeam, ctx.h2h || {});
    alerts = generateAlerts(homeData, awayData, h2dData ? h2dData.summary || null : null);
  }

  if (!alerts || !alerts.length) {
    return `<div class="blk-empty"><p class="muted">Sin alertas para este partido.</p></div>`;
  }

  const items = alerts.map(a => {
    const cls = (a.strength || "").toLowerCase();
    return `<div class="alert-card ${_blkEsc(cls)}">${_blkEsc(a.text || "")}</div>`;
  }).join("");

  return `<div class="alerts-list">${items}</div>`;
}
