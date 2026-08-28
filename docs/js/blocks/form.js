/**
 * blocks/form.js — Forma: puntos de forma + log de últimos partidos.
 * Comparte lógica con match.js (teamFormBlock) y comparador.js (buildFormDots + buildMatchLog).
 *
 * buildBlockForm(homeTeam, awayTeam, ctx)
 *   ctx.homeVenue  — 'home'|'away'|'all'
 *   ctx.awayVenue  — 'home'|'away'|'all'
 *   ctx.teamStats  — APP.teamStats / state.teamStats
 */
"use strict";

function buildBlockForm(homeTeam, awayTeam, ctx) {
  const hStats = _blkGetVenueStats((ctx.teamStats || {})[homeTeam], ctx.homeVenue || "home");
  const aStats = _blkGetVenueStats((ctx.teamStats || {})[awayTeam], ctx.awayVenue || "away");

  return `
    <div class="match-form-grid">
      ${_formPanel(homeTeam, ctx.homeVenue || "home", hStats)}
      ${_formPanel(awayTeam, ctx.awayVenue || "away", aStats)}
    </div>`;
}

function _formPanel(team, venue, stats) {
  const name = typeof teamDisplayName === "function" ? teamDisplayName(team) : team;
  const label = _blkVenueLabel(venue);

  if (!stats || !stats.matches_analyzed) {
    return `
      <div class="match-team-form">
        <h3>${_blkEsc(name)} <small>${_blkEsc(label)}</small></h3>
        <p class="muted">Sin datos suficientes.</p>
      </div>`;
  }

  const log = (stats.match_log || []).slice(0, 8);

  // Form dots
  const dots = log.map(m => {
    const r = (m.result || "").toUpperCase();
    const cls = r === "W" ? "w" : r === "D" ? "d" : "l";
    return `<span class="form-dot ${cls}" title="${r === "W" ? "Victoria" : r === "D" ? "Empate" : "Derrota"}"></span>`;
  }).join("");

  // Match log rows
  const logRows = log.map(m => {
    const r = (m.result || "").toUpperCase();
    let wdl;
    if (typeof wdlTag === "function") {
      wdl = wdlTag(m.result);
    } else {
      const cls = r === "W" ? "w" : r === "D" ? "d" : "l";
      const lbl = r === "W" ? "V" : r === "D" ? "E" : "D";
      wdl = `<span class="tag tag-${cls}">${lbl}</span>`;
    }
    const opp = m.opponent
      ? (typeof teamDisplayName === "function" ? teamDisplayName(m.opponent) : m.opponent)
      : "";
    return `
      <div class="match-row">
        ${wdl}
        <b>${_blkEsc(opp)}</b>
        <span class="score">${_blkEsc(m.score || "")}</span>
        <span class="muted-sm">${_blkEsc(m.date || "")}</span>
      </div>`;
  }).join("");

  return `
    <div class="match-team-form">
      <h3>${_blkEsc(name)} <small>${_blkEsc(label)}</small></h3>
      <div class="form-dots">${dots}</div>
      <div class="match-mini-grid compact">
        <div><span>PJ</span><strong>${stats.matches_analyzed}</strong></div>
        <div><span>Goles</span><strong>${_blkFmt(stats.avg_goals, 2)}</strong></div>
        <div><span>Contra</span><strong>${_blkFmt(stats.avg_goals_against, 2)}</strong></div>
        <div><span>Tarj.</span><strong>${_blkFmt(stats.avg_cards, 2)}</strong></div>
      </div>
      <div class="match-log">${logRows || '<p class="muted">Sin partidos en el log.</p>'}</div>
    </div>`;
}
