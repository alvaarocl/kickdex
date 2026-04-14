/**
 * valor.js — Tab "Value Bets": EV calculator + historical patterns table
 */

"use strict";

function initValor() {
  document.getElementById("val-run").addEventListener("click", runValor);
  // Patterns load automatically after data is ready (called from app.js)
}

function runValor() {
  const home = document.getElementById("val-home").value;
  const away = document.getElementById("val-away").value;
  const o1   = parseFloat(document.getElementById("val-o1").value);
  const ox   = parseFloat(document.getElementById("val-ox").value);
  const o2   = parseFloat(document.getElementById("val-o2").value);
  const ov   = parseFloat(document.getElementById("val-ov").value);
  const box  = document.getElementById("val-result");

  if (!home || !away) {
    box.innerHTML = `<div class="state-box"><div class="icon">⚠️</div><p>Selecciona ambos equipos primero</p></div>`;
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

  const h2hData    = getH2H(home, away);
  const h2hSummary = h2hData?.summary || null;
  const probs      = calcProbabilities(homeData, awayData, h2hSummary);

  if (!probs) {
    box.innerHTML = `<div class="state-box"><div class="icon">📭</div><p>No se pudieron calcular probabilidades</p></div>`;
    return;
  }

  // Build results
  const markets = [];

  if (isValidOdds(o1)) {
    markets.push(evaluateMarket("1 — Victoria local", probs.home, o1, home, away));
  }
  if (isValidOdds(ox)) {
    markets.push(evaluateMarket("X — Empate", probs.draw, ox, home, away));
  }
  if (isValidOdds(o2)) {
    markets.push(evaluateMarket("2 — Victoria visitante", probs.away, o2, home, away));
  }
  if (isValidOdds(ov)) {
    markets.push(evaluateMarket("Over 2.5 goles", probs.over25, ov, home, away));
  }

  if (markets.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">⚠️</div><p>Introduce al menos una cuota válida (> 1.00)</p></div>`;
    return;
  }

  box.innerHTML = buildValorHTML(home, away, probs, markets);
}

function isValidOdds(o) {
  return !isNaN(o) && o > 1.0;
}

function evaluateMarket(name, modelProb, odds, home, away) {
  const impliedProb = 1 / odds;
  const ev          = (modelProb * odds) - 1;
  const edge        = modelProb - impliedProb;

  let verdict, cls;
  if (ev >= 0.08) {
    verdict = "Valor ALTO";
    cls = "green";
  } else if (ev >= 0.03) {
    verdict = "Valor moderado";
    cls = "green";
  } else if (ev <= -0.05) {
    verdict = "Sin valor — cuota baja";
    cls = "red";
  } else {
    verdict = "Cuota justa";
    cls = "grey";
  }

  return { name, modelProb, odds, impliedProb, ev, edge, verdict, cls };
}

function buildValorHTML(home, away, probs, markets) {
  const sorted = [...markets].sort((a, b) => b.ev - a.ev);

  return `
  <!-- Header -->
  <div class="match-header" style="margin-bottom:24px;">
    <div class="teams">${home} <span class="vs">vs</span> ${away}</div>
    <div class="subtitle">lambda local: ${fmt(probs.lambda_h)} · lambda visitante: ${fmt(probs.lambda_a)}</div>
  </div>

  <!-- Probability reference -->
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">🎯 Probabilidades del modelo</div>
    <div class="grid-4">
      ${smallStatCard("Victoria local",    pct(probs.home),    "var(--green)")}
      ${smallStatCard("Empate",            pct(probs.draw),    "var(--yellow)")}
      ${smallStatCard("Victoria visit.",   pct(probs.away),    "var(--red)")}
      ${smallStatCard("Over 2.5",          pct(probs.over25),  "var(--blue)")}
    </div>
  </div>

  <!-- Value markets -->
  <div class="section-title">💎 Análisis de mercados</div>
  <div style="margin-bottom:20px;">
    ${sorted.map(m => buildValueRow(m)).join("")}
  </div>

  <!-- Legend -->
  <div class="card" style="font-size:.75rem;color:var(--muted);">
    <b style="color:var(--text)">Cómo leer:</b>
    EV = (probabilidad_modelo × cuota) – 1. Un EV ≥ 0.05 indica valor positivo esperado.
    La probabilidad del modelo es una estimación basada en forma reciente y Poisson bivariante.
    No constituye asesoramiento de apuestas.
  </div>`;
}

function buildValueRow(m) {
  const evSign   = m.ev >= 0 ? "+" : "";
  const evColor  = m.ev >= 0.03 ? "var(--green)" : m.ev <= -0.05 ? "var(--red)" : "var(--muted)";
  const badge    = m.ev >= 0.03
    ? `<span class="badge-value">VALUE ${(m.ev * 100).toFixed(1)}%</span>`
    : m.ev <= -0.05
    ? `<span class="badge-over">SIN VALOR</span>`
    : `<span class="badge-fair">JUSTO</span>`;

  return `
  <div class="value-row ${m.cls}">
    <div>
      <div class="value-market">${m.name}</div>
      <div class="value-meta">
        <span>Prob. modelo: <b>${pct(m.modelProb)}</b></span>
        <span>Prob. implícita: <b>${pct(m.impliedProb)}</b></span>
        <span>Edge: <b style="color:${evColor}">${evSign}${(m.edge * 100).toFixed(1)}%</b></span>
        <span>EV: <b style="color:${evColor}">${evSign}${(m.ev * 100).toFixed(1)}%</b></span>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
      <span style="font-size:1.1rem;font-weight:800;color:var(--text);">${m.odds}</span>
      ${badge}
    </div>
  </div>`;
}

// ── Historical patterns ────────────────────────────────────────────────────

function renderPatterns() {
  const box = document.getElementById("patterns-result");
  if (!box) return;

  const patterns = APP.valuePatterns;

  if (!patterns || patterns.length === 0) {
    box.innerHTML = `<div class="state-box"><div class="icon">📭</div><p>Sin patrones de valor histórico disponibles</p></div>`;
    return;
  }

  box.innerHTML = `
  <div class="section-title" style="margin-bottom:16px;">
    📊 Patrones de valor histórico <small>${patterns.length} patrones detectados</small>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Equipo</th>
          <th>Mercado</th>
          <th>Precisión</th>
          <th>Muestras</th>
          <th>Cuota media</th>
          <th>EV medio</th>
        </tr>
      </thead>
      <tbody>
        ${patterns.map(p => buildPatternRow(p)).join("")}
      </tbody>
    </table>
  </div>
  <div class="disclaimer" style="margin-top:14px;">
    Los patrones históricos se calculan sobre los últimos años de datos.
    El rendimiento pasado no garantiza resultados futuros.
  </div>`;
}

function buildPatternRow(p) {
  const evVal  = p.ev_mean != null ? p.ev_mean : p.avg_ev;
  const evDisp = evVal != null ? `${evVal >= 0 ? "+" : ""}${(evVal * 100).toFixed(1)}%` : "—";
  const evColor = evVal >= 0.03 ? "var(--green)" : evVal <= -0.05 ? "var(--red)" : "var(--muted)";

  const acc   = p.accuracy != null ? pct(p.accuracy) : "—";
  const n     = p.n_matches ?? p.samples ?? "—";
  const odds  = p.avg_odds != null ? fmt(p.avg_odds) : "—";

  return `
  <tr>
    <td><b>${p.team || p.HomeTeam || "—"}</b></td>
    <td>${p.market || p.pattern || "—"}</td>
    <td style="color:var(--green)">${acc}</td>
    <td class="muted">${n}</td>
    <td class="muted">${odds}</td>
    <td style="color:${evColor};font-weight:700">${evDisp}</td>
  </tr>`;
}

// ── Utilities ──────────────────────────────────────────────────────────────

function smallStatCard(label, value, color) {
  return `
  <div class="card" style="text-align:center;padding:12px;">
    <div class="card-title">${label}</div>
    <div class="card-value" style="color:${color};font-size:1.2rem;">${value}</div>
  </div>`;
}
