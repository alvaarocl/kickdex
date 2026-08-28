/**
 * blocks/players.js — Comparativa de jugadores.
 * Extraído de comparador.js (buildPlayerComparison).
 * Accede a los jugadores vía _blkPlayers() — funciona en APP y state.
 *
 * buildBlockPlayers(homeTeam, awayTeam, ctx)
 *   ctx.teamStats — no usado directamente, pero sí el accessor _blkPlayers()
 */
"use strict";

function buildBlockPlayers(homeTeam, awayTeam, ctx) {
  const allPlayers = _blkPlayers();
  const sortFn = (a, b) =>
    ((b.gls || 0) * 3 + (b.sot || 0) + (b.sh || 0) * 0.25) -
    ((a.gls || 0) * 3 + (a.sot || 0) + (a.sh || 0) * 0.25);

  const homePlayers = (allPlayers[homeTeam] || []).slice().sort(sortFn).slice(0, 8);
  const awayPlayers = (allPlayers[awayTeam] || []).slice().sort(sortFn).slice(0, 8);

  if (!homePlayers.length && !awayPlayers.length) {
    return `
      <div class="blk-empty">
        <p class="muted">Sin datos de jugadores para estos equipos.</p>
        <p class="muted" style="font-size:.8rem;">La cobertura depende de FBref/soccerdata — no todas las ligas están incluidas.
        Consulta <a href="coverage.html" style="color:var(--brand)">cobertura de datos</a>.</p>
      </div>`;
  }

  return `
    <p class="match-note">Promedios por partido de la temporada — los datos disponibles no incluyen estadísticas partido a partido.</p>
    <div class="players-comparison">
      ${_playerTable(homeTeam, homePlayers)}
      ${_playerTable(awayTeam, awayPlayers)}
    </div>`;
}

function _playerTable(team, players) {
  const label = typeof teamDisplayName === "function" ? teamDisplayName(team) : team;
  if (!players.length) {
    return `
      <div class="players-team-panel">
        <div class="players-col-title">${_blkEsc(label)}</div>
        <p class="muted">Sin datos</p>
      </div>`;
  }

  const rows = players.map(p => {
    const photo = typeof entityMedia === "function"
      ? entityMedia("player", p.player, team)
      : "";
    return `
      <tr>
        <td><span class="player-cell">${photo}<b>${_blkEsc(p.player)}</b></span></td>
        <td class="mono">${_blkFmt(p.sh, 1)}</td>
        <td class="mono">${_blkFmt(p.sot, 1)}</td>
        <td class="mono">${_blkFmt(p.gls, 1)}</td>
        <td class="mono">${_blkFmt(p.ast, 1)}</td>
        <td class="mono">${p.crdy != null ? _blkFmt(p.crdy, 2) : "—"}</td>
      </tr>`;
  }).join("");

  return `
    <div class="players-team-panel">
      <div class="players-col-title">${_blkEsc(label)}</div>
      <div class="table-wrap players-table-wrap" style="overflow-x:auto;max-height:420px;overflow-y:auto;">
        <table>
          <thead><tr><th>Jugador</th><th>Sh</th><th>SoT</th><th>Gls</th><th>Ast</th><th>TA</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}
