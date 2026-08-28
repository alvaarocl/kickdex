/**
 * blocks/hit_rates.js — Panel de frecuencias de apuesta con selector de ventana.
 * NUEVO en Fase 2 — lee team_stats[equipo].hit_rates[venue][window].
 * Cada línea muestra: etiqueta + barra + rate% (hits/total).
 * REGLA INNEGOCIABLE: nunca mostrar % solo, siempre con (n/N).
 *
 * buildBlockHitRates(homeTeam, awayTeam, ctx)
 *   ctx.homeVenue  — 'home'|'away'|'all'
 *   ctx.awayVenue  — 'home'|'away'|'all'
 *   ctx.window     — 'l5'|'l10'|'l20'|'all' (ventana activa)
 *   ctx.teamStats  — APP.teamStats / state.teamStats
 *
 * hitRatesSetWindow(btn, win) — llamado por los botones de ventana (onclick).
 */
"use strict";

const _HR_METRICS = [
  { key: "goals_over_05",  label: "Goles +0.5"         },
  { key: "goals_over_15",  label: "Goles +1.5"         },
  { key: "goals_over_25",  label: "Goles +2.5"         },
  { key: "goals_over_35",  label: "Goles +3.5"         },
  { key: "btts",           label: "BTTS (ambos marcan)" },
  { key: "clean_sheet",    label: "Portería a cero"     },
  { key: "team_no_score",  label: "Equipo no marca"     },
  { key: "team_over_05",   label: "Equipo +0.5 goles"  },
  { key: "team_over_15",   label: "Equipo +1.5 goles"  },
  { key: "corners_over_85",label: "Córners +8.5"        },
  { key: "corners_over_95",label: "Córners +9.5"        },
  { key: "cards_over_35",  label: "Tarjetas +3.5"       },
  { key: "cards_over_45",  label: "Tarjetas +4.5"       },
  { key: "fouls_over_205", label: "Faltas +20.5"        },
  { key: "fouls_over_245", label: "Faltas +24.5"        },
];

const _HR_WINDOWS = [
  { key: "l5",  label: "L5"   },
  { key: "l10", label: "L10"  },
  { key: "l20", label: "L20"  },
  { key: "all", label: "Todo" },
];

function buildBlockHitRates(homeTeam, awayTeam, ctx) {
  const homeVenue = ctx.homeVenue || "home";
  const awayVenue = ctx.awayVenue || "away";
  const win = ctx.window || "l20";
  const ts = ctx.teamStats || {};

  const homeHR = ts[homeTeam] && ts[homeTeam].hit_rates && ts[homeTeam].hit_rates[homeVenue];
  const awayHR = ts[awayTeam] && ts[awayTeam].hit_rates && ts[awayTeam].hit_rates[awayVenue];

  if (!homeHR && !awayHR) {
    return `<div class="blk-empty"><p class="muted">Sin datos de frecuencias — necesita build con hit_rates activado.</p></div>`;
  }

  const winBtns = _HR_WINDOWS.map(o =>
    `<button class="blk-hr-win-btn${o.key === win ? " active" : ""}" onclick="hitRatesSetWindow(this,'${o.key}')">${_blkEsc(o.label)}</button>`
  ).join("");

  return `
    <div class="blk-hit-rates" data-home="${_blkEsc(homeTeam)}" data-away="${_blkEsc(awayTeam)}" data-hv="${_blkEsc(homeVenue)}" data-av="${_blkEsc(awayVenue)}">
      <div class="blk-hr-controls">
        <span class="blk-hr-label">Ventana</span>
        ${winBtns}
      </div>
      <div class="blk-hr-body">
        ${_buildHRBody(homeTeam, awayTeam, homeHR, awayHR, win)}
      </div>
    </div>`;
}

function _buildHRBody(homeTeam, awayTeam, homeHR, awayHR, win) {
  const hW = homeHR && homeHR[win] ? homeHR[win] : {};
  const aW = awayHR && awayHR[win] ? awayHR[win] : {};
  const hName = typeof teamShortLabel === "function" ? teamShortLabel(homeTeam) : homeTeam;
  const aName = typeof teamShortLabel === "function" ? teamShortLabel(awayTeam) : awayTeam;

  const rows = _HR_METRICS.map(m => {
    const hd = hW[m.key];
    const ad = aW[m.key];
    const hValid = hd && hd.total > 0;
    const aValid = ad && ad.total > 0;

    const hBar = hValid ? Math.min(hd.rate * 100, 100) : 0;
    const aBar = aValid ? Math.min(ad.rate * 100, 100) : 0;

    // REGLA INNEGOCIABLE: siempre (hits/total), nunca % solo
    const hText = hValid ? `${_blkPct(hd.rate)} (${hd.hits}/${hd.total})` : "—";
    const aText = aValid ? `${_blkPct(ad.rate)} (${ad.hits}/${ad.total})` : "—";

    const hBetter = hValid && aValid && hd.rate > ad.rate;
    const aBetter = hValid && aValid && ad.rate > hd.rate;

    return `
      <div class="blk-hr-row">
        <div class="blk-hr-metric">${_blkEsc(m.label)}</div>
        <div class="blk-hr-side blk-hr-side--home">
          <span class="blk-hr-val${hBetter ? " leading" : ""}">${hText}</span>
          <div class="blk-hr-bar-wrap"><div class="blk-hr-bar blk-hr-bar--home" style="width:${hBar.toFixed(1)}%"></div></div>
        </div>
        <div class="blk-hr-side blk-hr-side--away">
          <div class="blk-hr-bar-wrap blk-hr-bar-wrap--away"><div class="blk-hr-bar blk-hr-bar--away" style="width:${aBar.toFixed(1)}%"></div></div>
          <span class="blk-hr-val${aBetter ? " leading" : ""}">${aText}</span>
        </div>
      </div>`;
  }).join("");

  return `
    <div class="blk-hr-header">
      <div class="blk-hr-metric"></div>
      <div class="blk-hr-side blk-hr-side--home"><span class="blk-hr-team-label">${_blkEsc(hName)}</span></div>
      <div class="blk-hr-side blk-hr-side--away"><span class="blk-hr-team-label">${_blkEsc(aName)}</span></div>
    </div>
    ${rows}`;
}

/**
 * Cambia la ventana activa del panel hit-rates sin re-renderizar toda la página.
 * Llamado por los botones de ventana vía onclick.
 */
function hitRatesSetWindow(btn, win) {
  const container = btn.closest(".blk-hit-rates");
  if (!container) return;

  const homeTeam  = container.dataset.home;
  const awayTeam  = container.dataset.away;
  const homeVenue = container.dataset.hv || "home";
  const awayVenue = container.dataset.av || "away";

  // Actualizar botón activo
  container.querySelectorAll(".blk-hr-win-btn").forEach(b => b.classList.toggle("active", b === btn));

  // Obtener teamStats del contexto global disponible
  const ts = (typeof APP !== "undefined" && APP.teamStats)
    || (typeof state !== "undefined" && state.teamStats)
    || {};

  const homeHR = ts[homeTeam] && ts[homeTeam].hit_rates && ts[homeTeam].hit_rates[homeVenue];
  const awayHR = ts[awayTeam] && ts[awayTeam].hit_rates && ts[awayTeam].hit_rates[awayVenue];

  container.querySelector(".blk-hr-body").innerHTML = _buildHRBody(homeTeam, awayTeam, homeHR, awayHR, win);
}
