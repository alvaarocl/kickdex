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
  const ob   = parseFloat(document.getElementById("val-ob").value);
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
  if (isValidOdds(ob)) {
    markets.push(evaluateMarket("BTTS — Ambos marcan", probs.btts, ob, home, away));
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
  // Kelly criterion: f* = (p·b - q) / b  where b = odds-1, q = 1-p
  const b     = odds - 1;
  const kelly = b > 0 ? Math.max(0, (modelProb * b - (1 - modelProb)) / b) : 0;
  // Half-Kelly for safer stake recommendation
  const halfKelly = kelly / 2;

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

  return { name, modelProb, odds, impliedProb, ev, edge, kelly, halfKelly, verdict, cls };
}

function buildValorHTML(home, away, probs, markets) {
  const sorted = [...markets].sort((a, b) => b.ev - a.ev);
  const valueMkts = sorted.filter(m => m.ev >= 0.03).length;

  const svgProb   = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`;
  const svgTrend  = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`;

  return `
  <!-- Header -->
  <div class="match-header" style="margin-bottom:24px;">
    <div class="teams">${home} <span class="vs">VS</span> ${away}</div>
    <div class="subtitle">Poisson bivariante · λ local: ${fmt(probs.lambda_h)} · λ visitante: ${fmt(probs.lambda_a)}${valueMkts > 0 ? ` · <span style="color:var(--gold);font-weight:700;">${valueMkts} mercado${valueMkts > 1 ? "s" : ""} con valor</span>` : ""}</div>
  </div>

  <!-- Probability KPI grid -->
  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">${svgProb} Probabilidades del modelo</div>
    <div class="grid-4">
      ${smallStatCard("Victoria local",   pct(probs.home),    "var(--green)")}
      ${smallStatCard("Empate",           pct(probs.draw),    "var(--yellow)")}
      ${smallStatCard("Victoria visit.",  pct(probs.away),    "var(--red)")}
      ${smallStatCard("Over 2.5",         pct(probs.over25),  "var(--blue)")}
      ${smallStatCard("BTTS",             pct(probs.btts),    "var(--purple)")}
      ${smallStatCard("λ Local",          fmt(probs.lambda_h),"var(--muted2)")}
      ${smallStatCard("λ Visitante",      fmt(probs.lambda_a),"var(--muted2)")}
    </div>
  </div>

  <!-- Value markets -->
  <div class="section-title">${svgTrend} Análisis de mercados</div>
  <div style="margin-bottom:20px;">
    ${sorted.map(m => buildValueRow(m)).join("")}
  </div>

  <!-- Legend -->
  <div class="card" style="font-size:.74rem;color:var(--muted);line-height:1.7;">
    <span style="color:var(--text2);font-weight:600;">Cómo leer:</span>
    EV = (probabilidad_modelo × cuota) &minus; 1. EV &ge; 0.05 indica valor positivo esperado.
    Las probabilidades son estimaciones matemáticas · No constituye asesoramiento de apuestas.
  </div>`;
}

function buildValueRow(m) {
  const evSign  = m.ev >= 0 ? "+" : "";
  const isValue = m.ev >= 0.03;
  const isOver  = m.ev <= -0.05;
  const evColor = isValue ? "var(--gold)" : isOver ? "var(--red)" : "var(--muted2)";

  const badge = isValue
    ? `<span class="badge-value">VALUE +${(m.ev * 100).toFixed(1)}%</span>`
    : isOver
    ? `<span class="badge-over">SIN VALOR</span>`
    : `<span class="badge-fair">CUOTA JUSTA</span>`;

  return `
  <div class="value-row ${m.cls}">
    <div style="flex:1;min-width:0;">
      <div class="value-market">${m.name}</div>
      <div class="value-meta">
        <span>Prob. modelo: <b>${pct(m.modelProb)}</b></span>
        <span>Prob. implícita: <b>${pct(m.impliedProb)}</b></span>
        <span>Edge: <b style="color:${evColor}">${evSign}${(m.edge * 100).toFixed(1)}%</b></span>
        <span>EV: <b style="color:${evColor};font-size:.88rem;">${evSign}${(m.ev * 100).toFixed(1)}%</b></span>
        ${m.halfKelly > 0 ? `<span title="½ Kelly — stake recomendado sobre bankroll (criterio conservador)">½ Kelly: <b style="color:var(--brand)">${(m.halfKelly * 100).toFixed(1)}%</b></span>` : ""}
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:7px;margin-left:16px;flex-shrink:0;">
      <span class="value-odds">${m.odds}</span>
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

  const svgBar = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;

  box.innerHTML = `
  <div class="section-title" style="margin-bottom:16px;">
    ${svgBar} Patrones de valor histórico <small>${patterns.length} patrones detectados</small>
  </div>
  <div class="table-wrap">
    <table id="patternsTable">
      <thead>
        <tr>
          <th>Condición</th>
          <th>Evento</th>
          <th>Prob. real</th>
          <th>Muestras</th>
          <th>Cuota media</th>
          <th>EV</th>
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
  setTimeout(() => initAllTables(box), 50);
}

function buildPatternRow(p) {
  // Support both Spanish keys (from build_data.py) and English keys
  const evRaw  = p["EV"] ?? p.ev_mean ?? p.avg_ev;
  const evDisp = evRaw != null
    ? (p["EV %"] ?? `${evRaw >= 0 ? "+" : ""}${(evRaw * 100).toFixed(1)}%`)
    : "—";
  const evColor = (evRaw ?? 0) >= 0.03 ? "var(--green)" : (evRaw ?? 0) <= -0.05 ? "var(--red)" : "var(--muted)";

  const cond  = p["Condición"] || p.market || p.pattern || "—";
  const event = p["Evento"]    || p.team   || p.HomeTeam || "—";
  const n     = p["Partidos (n)"] ?? p.n_matches ?? p.samples ?? "—";
  const aciertos = p["Aciertos"] != null ? p["Aciertos"] : null;
  const probReal = p["Prob. Real"] ?? (aciertos != null && n ? `${((aciertos / n) * 100).toFixed(1)}%` : "—");
  const odds  = p["Cuota Media"] ?? p.avg_odds;
  const oddsDisp = odds != null ? fmt(odds) : "—";

  return `
  <tr>
    <td><b>${event}</b></td>
    <td>${cond}</td>
    <td style="color:var(--green)">${probReal}</td>
    <td class="muted">${n}</td>
    <td class="muted">${oddsDisp}</td>
    <td style="color:${evColor};font-weight:700">${evDisp}</td>
  </tr>`;
}

// ── Utilities ──────────────────────────────────────────────────────────────

function smallStatCard(label, value, color) {
  return `
  <div class="card" style="text-align:center;padding:14px 10px;">
    <div class="card-title">${label}</div>
    <div class="card-value" style="color:${color};font-size:1.25rem;">${value}</div>
  </div>`;
}
