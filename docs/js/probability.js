/**
 * probability.js — motor de probabilidad compartido (Poisson + Dixon-Coles).
 *
 * Réplica exacta de app/engine/probability.py, para que el Comparador
 * (app.js/comparador.js) y la ficha de partido (match.js) no calculen
 * números distintos entre sí ni distintos de docs/data/edges.json.
 *
 * Cargado por index.html y match.html ANTES de app.js/match.js. No depende
 * de APP/state — recibe el modelConfig como parámetro explícito (con un
 * fallback si el fetch de model_config.json falla o aún no ha llegado).
 */

"use strict";

const DEFAULT_MODEL_CONFIG = {
  home_advantage: 1.15,
  league_avg_goals: 2.52,
  dixon_coles_rho: -0.12,
  h2h_weight: 0.30,
  h2h_min_total: 5,
  over25_weights: { base_poisson: 0.4, home_rate: 0.25, away_rate: 0.25, h2h_rate: 0.10 },
  btts_weights: { home_rate: 0.35, away_rate: 0.35, h2h_rate: 0.30 },
};

function poissonPMF(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  let log_p = -lambda + k * Math.log(lambda);
  for (let i = 1; i <= k; i++) log_p -= Math.log(i);
  return Math.exp(log_p);
}

function _dixonColesAdjustment(hg, ag, lamH, lamA, rho) {
  if (rho === 0) return 1.0;
  if (hg === 0 && ag === 0) return 1 - (lamH * lamA * rho);
  if (hg === 1 && ag === 0) return 1 + (lamA * rho);
  if (hg === 0 && ag === 1) return 1 + (lamH * rho);
  if (hg === 1 && ag === 1) return 1 - rho;
  return 1.0;
}

function _estimateLambda(teamAvgGoals, oppAvgConceded, leagueAvg, advantageFactor) {
  const attack  = leagueAvg > 0 ? teamAvgGoals / leagueAvg : 1.0;
  const defense = leagueAvg > 0 ? oppAvgConceded / leagueAvg : 1.0;
  return Math.max(0.1, attack * defense * leagueAvg * advantageFactor);
}

/**
 * @param homeStats  Objeto de team_stats.json para el equipo local (con
 *                    sub-claves .home/.away, como los devuelve build_team_stats).
 * @param awayStats  Igual para el visitante.
 * @param h2hSummary Objeto "summary" de h2h.json (opcional).
 * @param modelConfig Constantes del modelo (docs/data/model_config.json);
 *                    si se omite se usa DEFAULT_MODEL_CONFIG.
 */
function calcProbabilities(homeStats, awayStats, h2hSummary, modelConfig) {
  const hHome = homeStats?.home || homeStats?.away;
  const aAway = awayStats?.away || awayStats?.home;
  if (!hHome || !aAway) return null;

  const cfg = modelConfig || DEFAULT_MODEL_CONFIG;
  const halfAvg = cfg.league_avg_goals / 2;

  const homeAttack = hHome.avg_goals ?? halfAvg;
  const homeDefend = hHome.avg_goals_against ?? halfAvg;
  const awayAttack = aAway.avg_goals ?? halfAvg;
  const awayDefend = aAway.avg_goals_against ?? halfAvg;

  const lambdaH = _estimateLambda(homeAttack, awayDefend, halfAvg, cfg.home_advantage);
  const lambdaA = _estimateLambda(awayAttack, homeDefend, halfAvg, 1.0);

  const MAX_GOALS = 8;
  let home = 0, draw = 0, away = 0;
  // Captura la matriz cruda para derivar marcadores exactos y líneas O/U.
  const matrixRaw = [];
  for (let i = 0; i <= MAX_GOALS; i++) {
    const pH = poissonPMF(i, lambdaH);
    for (let j = 0; j <= MAX_GOALS; j++) {
      const p = pH * poissonPMF(j, lambdaA) * _dixonColesAdjustment(i, j, lambdaH, lambdaA, cfg.dixon_coles_rho);
      matrixRaw.push({ hg: i, ag: j, prob: p });
      if (i > j) home += p;
      else if (i === j) draw += p;
      else away += p;
    }
  }
  const total = home + draw + away || 1;
  home /= total; draw /= total; away /= total;

  // Matriz normalizada (misma normalización que Python)
  const matrixNorm = matrixRaw.map(e => ({ hg: e.hg, ag: e.ag, prob: e.prob / total }));

  // Top 8 marcadores exactos por probabilidad
  const topScores = matrixNorm
    .slice()
    .sort((a, b) => b.prob - a.prob)
    .slice(0, 8)
    .map(e => ({ score: `${e.hg}-${e.ag}`, prob: Math.round(e.prob * 10000) / 10000 }));

  // Líneas O/U derivadas de la misma matriz (paridad con Python)
  const ouLines = {};
  for (const line of [0.5, 1.5, 2.5, 3.5, 4.5]) {
    const over = matrixNorm.reduce((acc, e) => acc + (e.hg + e.ag > line ? e.prob : 0), 0);
    const overR = Math.round(over * 10000) / 10000;
    ouLines[String(line)] = { over: overR, under: Math.round((1 - overR) * 10000) / 10000 };
  }

  // Blend H2H (prefiere tasas ponderadas por antigüedad si el resumen las
  // trae — ver get_weighted_h2h_summary en app/engine/metrics.py).
  if (h2hSummary && h2hSummary.total >= cfg.h2h_min_total) {
    const n = h2hSummary.total;
    const hasWeighted = h2hSummary.weighted_win_rate1 !== undefined;
    const h2hHome = hasWeighted ? h2hSummary.weighted_win_rate1 : h2hSummary.wins_team1 / n;
    const h2hDraw = hasWeighted ? h2hSummary.weighted_draw_rate : h2hSummary.draws / n;
    const h2hAway = hasWeighted ? h2hSummary.weighted_win_rate2 : h2hSummary.wins_team2 / n;
    const w = cfg.h2h_weight;
    home = home * (1 - w) + h2hHome * w;
    draw = draw * (1 - w) + h2hDraw * w;
    away = away * (1 - w) + h2hAway * w;
    const t2 = home + draw + away || 1;
    home /= t2; draw /= t2; away /= t2;
  }

  // Over 2.5: base Poisson + tasas históricas de ambos equipos y H2H.
  let over25Base = 0;
  for (let i = 0; i < 8; i++) {
    for (let j = 0; j < 8; j++) {
      if (i + j > 2) over25Base += poissonPMF(i, lambdaH) * poissonPMF(j, lambdaA);
    }
  }
  const ow = cfg.over25_weights;
  const homeO25 = hHome.over25_rate ?? over25Base;
  const awayO25 = aAway.over25_rate ?? over25Base;
  const h2hO25  = h2hSummary?.over25_rate ?? over25Base;
  const over25 = over25Base * ow.base_poisson + homeO25 * ow.home_rate + awayO25 * ow.away_rate + h2hO25 * ow.h2h_rate;

  // BTTS: promedio ponderado de tasas históricas (sin componente Poisson).
  const bw = cfg.btts_weights;
  const homeBtts = hHome.btts_rate ?? 0.5;
  const awayBtts = aAway.btts_rate ?? 0.5;
  const h2hBtts  = h2hSummary?.btts_rate ?? 0.5;
  const btts = homeBtts * bw.home_rate + awayBtts * bw.away_rate + h2hBtts * bw.h2h_rate;

  const clamp01 = (x) => Math.max(0.01, Math.min(0.99, x));
  return {
    home:      clamp01(home),
    draw:      clamp01(draw),
    away:      clamp01(away),
    over25:    clamp01(over25),
    btts:      clamp01(btts),
    lambda_h:  lambdaH,
    lambda_a:  lambdaA,
    topScores: topScores,
    ouLines:   ouLines,
  };
}
