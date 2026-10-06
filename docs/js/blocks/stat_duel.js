/**
 * blocks/stat_duel.js — Duelo de estadísticas con barras enfrentadas.
 * Sustituye a buildStatDuel() de comparador.js (lógica movida aquí).
 *
 * buildBlockStatDuel(homeTeam, awayTeam, ctx)
 *   ctx.homeVenue  — 'home'|'away'|'all' (para el equipo local)
 *   ctx.awayVenue  — 'home'|'away'|'all' (para el visitante)
 *   ctx.teamStats  — APP.teamStats / state.teamStats
 */
"use strict";

function buildBlockStatDuel(homeTeam, awayTeam, ctx) {
  const hStats = _blkGetVenueStats((ctx.teamStats || {})[homeTeam], ctx.homeVenue || "home");
  const aStats = _blkGetVenueStats((ctx.teamStats || {})[awayTeam], ctx.awayVenue || "away");
  const shortH = typeof teamShortLabel === "function" ? teamShortLabel(homeTeam) : homeTeam.substring(0, 8);
  const shortA = typeof teamShortLabel === "function" ? teamShortLabel(awayTeam) : awayTeam.substring(0, 8);

  const rows = [
    { label: "Victorias",    hv: hStats.win_rate,          av: aStats.win_rate,          max: 1,    pct: true            },
    { label: "Goles/p",      hv: hStats.avg_goals,         av: aStats.avg_goals,         max: 3.5,  dec: 2               },
    { label: "Gc encaj./p",  hv: hStats.avg_goals_against, av: aStats.avg_goals_against, max: 3.5,  dec: 2, invert: true  },
    { label: "xG proxy",     hv: hStats.avg_xg_proxy,      av: aStats.avg_xg_proxy,      max: 3.0,  dec: 2               },
    { label: "Tiros/p",      hv: hStats.avg_shots,         av: aStats.avg_shots,         max: 22,   dec: 1               },
    { label: "SoT/p",        hv: hStats.avg_shots_on,      av: aStats.avg_shots_on,      max: 10,   dec: 1               },
    { label: "Córners/p",    hv: hStats.avg_corners,       av: aStats.avg_corners,       max: 14,   dec: 1               },
    { label: "Faltas/p",     hv: hStats.avg_fouls,         av: aStats.avg_fouls,         max: 30,   dec: 1, invert: true  },
    { label: "Tarjetas/p",   hv: hStats.avg_cards,         av: aStats.avg_cards,         max: 5,    dec: 1, invert: true  },
    { label: "Over 2.5",     hv: hStats.over25_rate,       av: aStats.over25_rate,       max: 1,    pct: true            },
    { label: "BTTS",         hv: hStats.btts_rate,         av: aStats.btts_rate,         max: 1,    pct: true            },
    { label: "P. a cero",    hv: hStats.clean_sheet_rate,  av: aStats.clean_sheet_rate,  max: 1,    pct: true            },
  ];

  const header = `
    <div class="duel-header">
      <div class="duel-hd-home">${_blkEsc(shortH)}</div>
      <div></div><div></div><div></div>
      <div class="duel-hd-away">${_blkEsc(shortA)}</div>
    </div>`;

  const rowsHtml = rows.map(r => {
    // null = la fuente no tiene ese dato para el equipo: "—", sin barra ni "ganador".
    const hOk = r.hv != null && Number.isFinite(Number(r.hv));
    const aOk = r.av != null && Number.isFinite(Number(r.av));
    const hv = hOk ? Number(r.hv) : 0;
    const av = aOk ? Number(r.av) : 0;
    const max = r.max || 1;
    const bar = (ok, v) => ok ? Math.max(0, Math.min(r.invert ? (max - v) / max : v / max, 1)) * 100 : 0;
    const hBar = bar(hOk, hv);
    const aBar = bar(aOk, av);
    const disp = (ok, v) => !ok ? "—" : r.pct ? _blkPct(v) : _blkFmt(v, r.dec != null ? r.dec : 1);
    const hDisp = disp(hOk, hv);
    const aDisp = disp(aOk, av);
    const both = hOk && aOk;
    const hBetter = both && (r.invert ? (hv < av) : (hv > av));
    const aBetter = both && (r.invert ? (av < hv) : (av > hv));
    return `
      <div class="duel-row">
        <div class="duel-val-home${hBetter ? " leading" : ""}">${hDisp}</div>
        <div class="duel-track-home"><div class="duel-bar-home" style="width:${hBar.toFixed(1)}%"></div></div>
        <div class="duel-label">${_blkEsc(r.label)}</div>
        <div class="duel-track-away"><div class="duel-bar-away" style="width:${aBar.toFixed(1)}%"></div></div>
        <div class="duel-val-away${aBetter ? " leading" : ""}">${aDisp}</div>
      </div>`;
  }).join("");

  return `<div class="stat-duel">${header}${rowsHtml}</div>`;
}
