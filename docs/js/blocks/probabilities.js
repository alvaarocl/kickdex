/**
 * blocks/probabilities.js — Panel de probabilidades compartido.
 * 1X2 + Over/BTTS + marcadores más probables (mini-heatmap) + líneas O/U.
 *
 * buildBlockProbabilities(homeTeam, awayTeam, ctx)
 *   ctx.probs       — objeto ya calculado por calcProbabilities()
 *                     Si es null, lo calcula internamente.
 *   ctx.teamStats   — APP.teamStats / state.teamStats
 *   ctx.h2h         — dict completo de h2h.json
 *   ctx.modelConfig — model_config.json
 */
"use strict";

function buildBlockProbabilities(homeTeam, awayTeam, ctx) {
  let probs = ctx.probs;
  if (!probs && ctx.teamStats && typeof calcProbabilities === "function") {
    const homeData = ctx.teamStats[homeTeam] || {};
    const awayData = ctx.teamStats[awayTeam] || {};
    const h2dData = _blkGetH2H(homeTeam, awayTeam, ctx.h2h || {});
    probs = calcProbabilities(homeData, awayData, h2dData?.summary || null, ctx.modelConfig || null);
  }
  if (!probs) {
    return '<div class="blk-empty"><p class="muted">Sin muestra suficiente para calcular probabilidades.</p></div>';
  }

  const maxP = Math.max(probs.home, probs.draw, probs.away);
  const hName = typeof teamDisplayName === "function" ? teamDisplayName(homeTeam) : homeTeam;
  const aName = typeof teamDisplayName === "function" ? teamDisplayName(awayTeam) : awayTeam;

  return `
    <div class="blk-probs">
      <div class="blk-prob-1x2">
        ${_probBoxHtml("1", hName, probs.home, probs.home === maxP)}
        ${_probBoxHtml("X", "Empate", probs.draw, probs.draw === maxP)}
        ${_probBoxHtml("2", aName, probs.away, probs.away === maxP)}
      </div>
      <div class="blk-prob-extra">
        ${_probExtraRow("Over 2.5", probs.over25)}
        ${_probExtraRow("BTTS (ambos marcan)", probs.btts)}
        <div class="blk-prob-extra-row">
          <span>xG proxy (local – vis)</span>
          <strong>${_blkFmt(probs.lambda_h, 2)} – ${_blkFmt(probs.lambda_a, 2)}</strong>
        </div>
      </div>
      ${_buildTopScoresHtml(probs.topScores || [])}
      ${_buildOULinesHtml(probs.ouLines || {})}
    </div>`;
}

function _probBoxHtml(code, name, prob, isWinner) {
  const pctVal = (prob * 100).toFixed(1);
  const barW = Math.max(2, Math.min(100, prob * 100)).toFixed(1);
  return `
    <div class="blk-prob-box${isWinner ? " blk-prob-box--winner" : ""}">
      <div class="blk-prob-code">${_blkEsc(code)}</div>
      <div class="blk-prob-name">${_blkEsc(name)}</div>
      <div class="blk-prob-pct">${pctVal}%</div>
      <div class="blk-prob-track"><div class="blk-prob-fill" style="width:${barW}%"></div></div>
    </div>`;
}

function _probExtraRow(label, val) {
  return `
    <div class="blk-prob-extra-row">
      <span>${_blkEsc(label)}</span>
      <strong>${_blkPct(val)}</strong>
    </div>`;
}

function _buildTopScoresHtml(topScores) {
  if (!topScores.length) return "";
  const maxProb = topScores[0]?.prob || 0.001;
  const cells = topScores.slice(0, 8).map(s => {
    const opacity = Math.max(0.08, Math.min(1, s.prob / maxProb));
    return `
      <div class="blk-score-cell" style="--score-op:${opacity.toFixed(3)}" title="${_blkEsc(s.score)} · ${_blkPct(s.prob, 1)}">
        <div class="blk-score-label">${_blkEsc(s.score)}</div>
        <div class="blk-score-pct">${_blkPct(s.prob, 1)}</div>
      </div>`;
  }).join("");
  return `
    <div class="blk-scores-section">
      <div class="blk-section-label">Marcadores más probables</div>
      <div class="blk-score-heatmap">${cells}</div>
    </div>`;
}

function _buildOULinesHtml(ouLines) {
  const lines = ["0.5", "1.5", "2.5", "3.5", "4.5"];
  const rows = lines.map(l => {
    const o = ouLines[l];
    if (!o) return "";
    return `
      <tr>
        <td>O/U ${_blkEsc(l)}</td>
        <td class="blk-ou-over">${_blkPct(o.over, 1)}</td>
        <td class="blk-ou-under">${_blkPct(o.under, 1)}</td>
      </tr>`;
  }).join("");
  if (!rows.trim()) return "";
  return `
    <div class="blk-ou-section">
      <div class="blk-section-label">Líneas Over/Under</div>
      <div class="table-wrap">
        <table class="blk-ou-table">
          <thead><tr><th>Línea</th><th>Over</th><th>Under</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}
