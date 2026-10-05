/**
 * blocks/h2h.js — Bloque H2H: envuelve buildH2HHTML de js/h2h.js.
 * NO modifica js/h2h.js — solo lo llama.
 *
 * buildBlockH2H(homeTeam, awayTeam, ctx)
 *   ctx.h2h — dict completo de h2h.json (APP.h2h / state.h2h)
 */
"use strict";

function buildBlockH2H(homeTeam, awayTeam, ctx) {
  const h2h = ctx.h2h || {};
  const h2hData = _blkGetH2H(homeTeam, awayTeam, h2h);

  if (!h2hData || !h2hData.summary) {
    const hn = typeof teamDisplayName === "function" ? teamDisplayName(homeTeam) : homeTeam;
    const an = typeof teamDisplayName === "function" ? teamDisplayName(awayTeam) : awayTeam;
    return `<div class="blk-empty"><p class="muted">Sin historial H2H suficiente entre ${_blkEsc(hn)} y ${_blkEsc(an)}.</p></div>`;
  }

  if (typeof buildH2HHTML !== "function") {
    return `<div class="blk-empty"><p class="muted">Módulo H2H no cargado — asegúrate de incluir js/h2h.js.</p></div>`;
  }

  // h2h.json guarda los equipos en orden alfabético; se muestra local → visitante.
  if (h2hData.team2 === homeTeam && h2hData.team1 === awayTeam) {
    const s = h2hData.summary;
    return buildH2HHTML(homeTeam, awayTeam, { ...h2hData, team1: homeTeam, team2: awayTeam, summary: { ...s, wins1: s.wins2, wins2: s.wins1 } });
  }
  return buildH2HHTML(h2hData.team1, h2hData.team2, h2hData);
}
