/**
 * match.js - standalone match intelligence page.
 */

"use strict";

const DATA_BASE = "./data/";

const state = {
  fixtures: { recent: [], upcoming: [], calendar: [] },
  leagues: {},
  teamStats: {},
  h2h: {},
  edges: { items: [], top: null },
  trends: { teams: {} },
  players: {},
  referees: [],
  suspensions: { by_team: {}, items: [], totals: {} },
  discipline: { by_team: {}, top: [] },
  teamAssets: { teams: {} },
  playerAssets: { players: {} },
};

document.addEventListener("DOMContentLoaded", initMatchPage);

async function initMatchPage() {
  try {
    const [fixtures, leagues, teamStats, h2h, edges, trends, players, referees, suspensions, discipline, teamAssets, playerAssets] = await Promise.all([
      fetchJSON("fixtures.json"),
      fetchJSON("leagues.json").catch(() => ({})),
      fetchJSON("team_stats.json").catch(() => ({})),
      fetchJSON("h2h.json").catch(() => ({})),
      fetchJSON("edges.json").catch(() => ({ items: [], top: null })),
      fetchJSON("trends.json").catch(() => ({ teams: {} })),
      fetchJSON("players.json").catch(() => ({})),
      fetchJSON("referees.json").catch(() => []),
      fetchJSON("suspensions.json").catch(() => ({ by_team: {}, items: [], totals: {} })),
      fetchJSON("discipline_watch.json").catch(() => ({ by_team: {}, top: [] })),
      fetchJSON("team_assets.json").catch(() => ({ teams: {} })),
      fetchJSON("player_assets.json").catch(() => ({ players: {} })),
    ]);
    Object.assign(state, { fixtures, leagues, teamStats, h2h, edges, trends, players, referees, suspensions, discipline, teamAssets, playerAssets });
    window.KDXEntities?.configure(teamAssets, playerAssets);
    renderMatch();
  } catch (err) {
    document.getElementById("match-root").innerHTML = `
      <div class="state-box"><div class="icon">!</div><p>No se pudo cargar la ficha del partido.</p></div>`;
    console.error(err);
  }
}

async function fetchJSON(file) {
  const res = await fetch(`${DATA_BASE}${file}?v=20260823a`);
  if (!res.ok) throw new Error(`HTTP ${res.status} loading ${file}`);
  return res.json();
}

function renderMatch() {
  const root = document.getElementById("match-root");
  const fixture = findRequestedFixture();
  if (!fixture) {
    root.innerHTML = `
      <div class="state-box">
        <div class="icon">?</div>
        <p>No encontramos ese partido. Vuelve al calendario y abre la ficha desde alli.</p>
        <p><a class="btn btn-primary btn-sm" href="index.html">Volver al calendario</a></p>
      </div>`;
    return;
  }

  const homeStats = state.teamStats[fixture.home] || {};
  const awayStats = state.teamStats[fixture.away] || {};
  const h2hData = getH2H(fixture.home, fixture.away);
  const probs = calcProbabilities(homeStats, awayStats, h2hData?.summary || null);
  const matchEdges = getFixtureEdges(fixture);
  const topEdge = matchEdges[0] || null;
  const referee = getAssignedReferee(fixture);
  const leagueRefs = getLeagueRefereeContext(fixture.league);

  document.title = `${fixture.home} vs ${fixture.away} - KICKDEX`;
  root.innerHTML = `
    ${buildHero(fixture, topEdge, probs)}
    <div class="match-layout">
      <section class="match-main">
        ${buildProbabilitySection(fixture, probs, topEdge)}
        ${buildTrendsSection(fixture)}
        ${buildFormSection(fixture, homeStats, awayStats)}
        ${buildH2HSection(fixture, h2hData)}
        ${buildApercibidosSection(fixture)}
        ${buildPlayersSection(fixture)}
      </section>
      <aside class="match-side">
        ${buildMatchFacts(fixture, referee)}
        ${buildRefereeSection(fixture, referee, leagueRefs)}
        ${buildDataQuality(fixture, topEdge)}
      </aside>
    </div>
  `;
}

function buildApercibidosSection(f) {
  const home = officialSuspensionsForTeam(f.home);
  const away = officialSuspensionsForTeam(f.away);
  const total = home.length + away.length;
  if (!total) {
    return sectionCard("Apercibidos oficiales", `
      <p class="muted">Sin apercibidos o sancionados oficiales publicados para estos equipos en el feed actual.</p>
      <p class="match-note">Este bloque solo muestra jugadores confirmados por una fuente oficial o cargados como verificados. No usa el modelo de riesgo disciplinario.</p>
    `);
  }

  return sectionCard("Apercibidos oficiales del partido", `
    <div class="match-form-grid">
      ${apercibidosBlock(f.home, home)}
      ${apercibidosBlock(f.away, away)}
    </div>
    <div class="apercibidos-note">
      <strong>Fuente verificada.</strong> KICKDEX no inventa apercibidos: si una competicion no publica datos estructurados, el bloque queda vacio hasta validacion manual u oficial.
      <a href="apercibidos.html?league=${encodeURIComponent(f.league || "")}">Ver feed completo</a>
    </div>
  `);
}

function officialSuspensionsForTeam(team) {
  const block = state.suspensions?.by_team?.[team] || {};
  return [...(block.suspended || []), ...(block.at_risk || [])].slice(0, 8);
}

function apercibidosBlock(team, items) {
  const rows = items.map(item => `
    <tr>
      <td><a href="${playerHref(team, item.player)}"><b>${esc(item.player)}</b></a></td>
      <td>${statusBadge(item)}</td>
      <td>${cardCount(item)}</td>
      <td>${sourceLink(item)}</td>
    </tr>`).join("");
  return `
    <div class="match-team-form apercibidos-card">
      <h3>${esc(team)}</h3>
      <div class="table-wrap match-table">
        <table>
          <thead><tr><th>Jugador</th><th>Estado</th><th>Tarjetas</th><th>Fuente</th></tr></thead>
          <tbody>${rows || `<tr><td colspan="4">Sin registros oficiales</td></tr>`}</tbody>
        </table>
      </div>
    </div>`;
}

function statusBadge(item) {
  const status = item.status === "suspended" ? "sancionado" : "apercibido";
  return `<span class="apercibido-badge apercibido-badge--${esc(status)}">${esc(item.status_label || status)}</span>`;
}

function cardCount(item) {
  const cards = item.cards ?? null;
  const threshold = item.threshold ?? null;
  if (cards !== null && threshold !== null) return `${esc(cards)}/${esc(threshold)}`;
  if (cards !== null) return esc(cards);
  return "-";
}

function sourceLink(item) {
  const label = item.official ? "Oficial" : "Verificado";
  if (item.source_url) {
    return `<a href="${esc(item.source_url)}" target="_blank" rel="noopener">${label}</a>`;
  }
  return label;
}

function buildDisciplineSection(f) {
  const home = state.discipline?.by_team?.[f.home] || [];
  const away = state.discipline?.by_team?.[f.away] || [];
  if (!home.length && !away.length) {
    return sectionCard("Tendencia de tarjetas", `<p class="muted">No hay jugadores con tendencia alta de tarjetas para estos equipos.</p>`);
  }
  return sectionCard("Tendencia de tarjetas", `
    <div class="match-form-grid">
      ${disciplineBlock(f.home, home)}
      ${disciplineBlock(f.away, away)}
    </div>
    <p class="match-note">Tendencia estadistica por amarillas y minutos. Este bloque no confirma apercibidos ni sanciones oficiales.</p>
  `);
}

function disciplineBlock(team, items) {
  const rows = items.slice(0, 6).map(item => `
    <tr>
      <td><a href="${playerHref(team, item.player)}">${esc(item.player)}</a></td>
      <td>${fmt(item.yellow_cards_per_match, 2)}</td>
      <td>${fmt(item.yellow_cards_p90, 2)}</td>
      <td><span class="discipline-risk discipline-risk--${esc(item.risk)}">${esc(item.risk)}</span></td>
    </tr>`).join("");
  return `
    <div class="match-team-form">
      <h3>${esc(team)}</h3>
      <div class="table-wrap match-table">
        <table>
          <thead><tr><th>Jugador</th><th>TA/p</th><th>TA P90</th><th>Riesgo</th></tr></thead>
          <tbody>${rows || `<tr><td colspan="4">Sin alertas</td></tr>`}</tbody>
        </table>
      </div>
    </div>`;
}

function findRequestedFixture() {
  const params = new URLSearchParams(window.location.search);
  const all = (state.fixtures.calendar || []).length
    ? state.fixtures.calendar
    : [...(state.fixtures.upcoming || []), ...(state.fixtures.recent || [])];
  const league = params.get("league");
  const date = params.get("date");
  const home = params.get("home");
  const away = params.get("away");
  if (league && date && home && away) {
    return all.find(f =>
      f.league === league &&
      f.date === date &&
      f.home === home &&
      f.away === away
    );
  }
  return all[0] || null;
}

function buildHero(f, edge, probs) {
  const isResult = f.home_score !== undefined && f.away_score !== undefined;
  const score = isResult
    ? `<div class="match-score">${f.home_score}<span>-</span>${f.away_score}</div>`
    : `<div class="match-score match-score--vs">VS</div>`;
  const status = isResult ? "Finalizado" : "Proximo partido";
  const edgeHtml = edge
    ? `<div class="match-edge-chip">${formatSigned(edge.edge_pct)} EDGE <span>${esc(edge.selection)} @ ${esc(edge.odds)}</span></div>`
    : `<div class="match-edge-chip match-edge-chip--muted">Sin edge con cuota disponible</div>`;
  const probLine = probs
    ? `${pct(probs.home)} local · ${pct(probs.draw)} empate · ${pct(probs.away)} visitante`
    : "Probabilidades no disponibles";

  return `
    <section class="match-hero card">
      <div class="match-kicker">
        <span>${esc(state.leagues[f.league]?.name || f.league || "Liga")}</span>
        <span>${esc(status)}</span>
        <span>${formatDate(f.date, f.time)}</span>
      </div>
      <div class="match-title-row">
        <div class="match-team-title">${window.KDXEntities?.media("team", f.home, "", "entity-media--hero") || ""}<h1>${esc(f.home)}</h1></div>
        ${score}
        <div class="match-team-title match-team-title--away">${window.KDXEntities?.media("team", f.away, "", "entity-media--hero") || ""}<h1>${esc(f.away)}</h1></div>
      </div>
      <div class="match-subline">
        <span>${esc(f.venue || "Estadio no publicado")}</span>
        <span>${probLine}</span>
      </div>
      ${edgeHtml}
    </section>
  `;
}

function buildProbabilitySection(f, probs, edge) {
  if (!probs) return sectionCard("Modelo KICKDEX", `<p class="muted">Sin muestra suficiente para calcular probabilidades.</p>`);
  const edgeNote = edge
    ? `<p class="match-note">El edge compara la probabilidad KICKDEX con la probabilidad implicita de la cuota disponible.</p>`
    : `<p class="match-note">No hay cuota enlazada a este partido en el feed actual. El modelo sigue mostrando probabilidad estimada.</p>`;
  return sectionCard("Modelo KICKDEX", `
    <div class="match-prob-grid">
      ${probCard(f.home, probs.home)}
      ${probCard("Empate", probs.draw)}
      ${probCard(f.away, probs.away)}
    </div>
    <div class="match-mini-grid">
      <div><span>Over 2.5</span><strong>${pct(probs.over25)}</strong></div>
      <div><span>BTTS</span><strong>${pct(probs.btts)}</strong></div>
      <div><span>xG proxy</span><strong>${fmt(probs.lambda_h, 2)} - ${fmt(probs.lambda_a, 2)}</strong></div>
    </div>
    ${edgeNote}
  `);
}

function probCard(label, value) {
  const width = Math.max(2, Math.min(100, value * 100));
  return `
    <div class="match-prob-card">
      <span>${esc(label)}</span>
      <strong>${pct(value)}</strong>
      <div class="match-prob-track"><i style="width:${width.toFixed(1)}%"></i></div>
    </div>`;
}

function buildFormSection(f, homeStats, awayStats) {
  const home = homeStats.home || {};
  const away = awayStats.away || {};
  return sectionCard("Forma local/visitante", `
    <div class="match-form-grid">
      ${teamFormBlock(f.home, "En casa", home)}
      ${teamFormBlock(f.away, "Fuera", away)}
    </div>
  `);
}

function buildTrendsSection(f) {
  const home = state.trends?.teams?.[f.home] || {};
  const away = state.trends?.teams?.[f.away] || {};
  const groups = [
    { title: `${f.home} en casa`, items: home.home || [] },
    { title: `${f.away} fuera`, items: away.away || [] },
    { title: "Globales", items: [...(home.all || []).slice(0, 4), ...(away.all || []).slice(0, 4)] },
  ];
  const hasAny = groups.some(group => group.items.length);
  if (!hasAny) return sectionCard("Tendencias", `<p class="muted">Aun no hay tendencias fuertes para este partido.</p>`);

  return sectionCard("Tendencias", `
    <div class="match-trends-grid">
      ${groups.map(group => `
        <div class="match-trend-group">
          <h3>${esc(group.title)}</h3>
          <ul>
            ${(group.items || []).slice(0, 6).map(item => `
              <li>
                <span>${esc(item.category || "trend")}</span>
                <strong>${esc(item.text)}</strong>
                <small>${esc((item.sequence || []).map(v => v ? "1" : "0").join("-"))}</small>
              </li>`).join("") || `<li class="muted">Sin tendencia fuerte</li>`}
          </ul>
        </div>
      `).join("")}
    </div>
  `);
}

function teamFormBlock(team, label, stats) {
  if (!stats || !stats.matches_analyzed) {
    return `<div class="match-team-form"><h3>${esc(team)}</h3><p class="muted">Sin datos suficientes.</p></div>`;
  }
  const log = (stats.match_log || []).slice(0, 6).map(m => `
    <li><span class="tag tag-${resultClass(m.result)}">${resultLabel(m.result)}</span><span>${esc(m.date)} · ${esc(m.opponent || "")}</span><strong>${esc(m.score || "")}</strong></li>
  `).join("");
  return `
    <div class="match-team-form">
      <h3>${esc(team)} <small>${label}</small></h3>
      <div class="match-mini-grid compact">
        <div><span>PJ</span><strong>${stats.matches_analyzed}</strong></div>
        <div><span>Goles</span><strong>${fmt(stats.avg_goals, 2)}</strong></div>
        <div><span>Contra</span><strong>${fmt(stats.avg_goals_against, 2)}</strong></div>
        <div><span>Tarjetas</span><strong>${fmt(stats.avg_cards, 2)}</strong></div>
      </div>
      <ul class="match-log">${log}</ul>
    </div>`;
}

function buildH2HSection(f, h2hData) {
  if (!h2hData) return sectionCard("H2H", `<p class="muted">No hay enfrentamientos directos suficientes en la base actual.</p>`);
  const s = h2hData.summary || {};
  const rows = (h2hData.matches || []).slice(0, 8).map(m => `
    <tr><td>${esc(m.date)}</td><td>${esc(m.result)}</td><td>${esc(m.league || "")}</td></tr>
  `).join("");
  return sectionCard("H2H", `
    <div class="match-mini-grid">
      <div><span>Total</span><strong>${s.total || 0}</strong></div>
      <div><span>${esc(h2hData.team1)}</span><strong>${s.wins1 || 0}</strong></div>
      <div><span>Empates</span><strong>${s.draws || 0}</strong></div>
      <div><span>${esc(h2hData.team2)}</span><strong>${s.wins2 || 0}</strong></div>
      <div><span>Media goles</span><strong>${fmt(s.avg_goals, 2)}</strong></div>
      <div><span>BTTS</span><strong>${pct(s.btts_rate)}</strong></div>
    </div>
    <div class="table-wrap match-table"><table><thead><tr><th>Fecha</th><th>Resultado</th><th>Liga</th></tr></thead><tbody>${rows}</tbody></table></div>
  `);
}

function buildPlayersSection(f) {
  const home = topPlayers(f.home);
  const away = topPlayers(f.away);
  if (!home.length && !away.length) {
    return sectionCard("Jugadores", `<p class="muted">No hay datos de jugadores para estos equipos.</p>`);
  }
  return sectionCard("Jugadores destacados", `
    <div class="match-form-grid">
      ${playersBlock(f.home, home)}
      ${playersBlock(f.away, away)}
    </div>
  `);
}

function playersBlock(team, players) {
  const rows = players.map(p => `
    <tr>
      <td>${esc(p.player)}</td>
      <td>${fmt(p.gls, 2)}</td>
      <td>${fmt(p.ast, 2)}</td>
      <td>${fmt(p.sh, 2)}</td>
      <td>${fmt(p.sot, 2)}</td>
      <td>${fmt(p.crdy, 2)}</td>
    </tr>`).join("");
  return `
    <div class="match-team-form">
      <h3>${esc(team)}</h3>
      <div class="table-wrap match-table">
        <table>
          <thead><tr><th>Jugador</th><th>G</th><th>A</th><th>Sh</th><th>SoT</th><th>TA</th></tr></thead>
          <tbody>${rows || `<tr><td colspan="6">Sin datos</td></tr>`}</tbody>
        </table>
      </div>
    </div>`;
}

function buildMatchFacts(f, referee) {
  const isResult = f.home_score !== undefined && f.away_score !== undefined;
  return sectionCard("Ficha", `
    <dl class="match-facts">
      <dt>Liga</dt><dd>${esc(state.leagues[f.league]?.name || f.league || "-")}</dd>
      <dt>Fecha</dt><dd>${formatDate(f.date, f.time)}</dd>
      <dt>Estado</dt><dd>${isResult ? "Finalizado" : "Previo"}</dd>
      <dt>Jornada</dt><dd>${esc(f.round || "-")}</dd>
      <dt>Estadio</dt><dd>${esc(f.venue || "-")}</dd>
      <dt>Arbitro</dt><dd>${referee ? esc(referee.name) : "No publicado"}</dd>
    </dl>
  `);
}

function buildRefereeSection(f, referee, leagueRefs) {
  if (referee) {
    return sectionCard("Arbitro", `
      <div class="match-ref-card">
        <h3>${esc(referee.name)}</h3>
        <div class="match-mini-grid compact">
          <div><span>Partidos</span><strong>${referee.matches || 0}</strong></div>
          <div><span>Amarillas</span><strong>${fmt(referee.yellows_per_match, 2)}</strong></div>
          <div><span>Rojas</span><strong>${fmt(referee.reds_per_match, 2)}</strong></div>
          <div><span>Faltas</span><strong>${fmt(referee.fouls_per_match, 2)}</strong></div>
        </div>
      </div>
    `);
  }
  return sectionCard("Contexto arbitral", `
    <p class="muted">Arbitro asignado no publicado en el calendario actual.</p>
    <div class="match-mini-grid compact">
      <div><span>Arbitros liga</span><strong>${leagueRefs.count}</strong></div>
      <div><span>TA media</span><strong>${fmt(leagueRefs.yellows, 2)}</strong></div>
      <div><span>TR media</span><strong>${fmt(leagueRefs.reds, 2)}</strong></div>
    </div>
  `);
}

function buildDataQuality(f, edge) {
  return sectionCard("Cobertura", `
    <ul class="match-coverage">
      <li><strong>Forma:</strong> ${state.teamStats[f.home] && state.teamStats[f.away] ? "disponible" : "parcial"}</li>
      <li><strong>H2H:</strong> ${getH2H(f.home, f.away) ? "disponible" : "sin muestra"}</li>
      <li><strong>Jugadores:</strong> ${(state.players[f.home] || state.players[f.away]) ? "disponible" : "parcial/no disponible"}</li>
      <li><strong>Edge:</strong> ${edge ? "con cuota enlazada" : "sin cuota futura enlazada"}</li>
    </ul>
  `);
}

function sectionCard(title, body) {
  return `<section class="card match-section"><h2>${title}</h2>${body}</section>`;
}

function getFixtureEdges(f) {
  return (state.edges.items || [])
    .filter(e => e.league === f.league && e.date === f.date && e.home === f.home && e.away === f.away)
    .sort((a, b) => (b.edge_pct || 0) - (a.edge_pct || 0));
}

function getH2H(a, b) {
  return state.h2h[`${a}|${b}`] || state.h2h[`${b}|${a}`] || null;
}

function getAssignedReferee(f) {
  const name = f.referee || f.Referee;
  if (!name) return null;
  return state.referees.find(r => norm(r.name) === norm(name)) || { name };
}

function getLeagueRefereeContext(league) {
  const refs = (state.referees || []).filter(r => r.league === league);
  const avg = (key) => {
    const vals = refs.map(r => Number(r[key])).filter(Number.isFinite);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  };
  return { count: refs.length, yellows: avg("yellows_per_match"), reds: avg("reds_per_match") };
}

function playerHref(team, player) {
  const params = new URLSearchParams({ team: team || "", player: player || "" });
  return `player.html?${params.toString()}`;
}

function topPlayers(team) {
  return (state.players[team] || [])
    .slice()
    .sort((a, b) => ((b.gls || 0) * 3 + (b.sot || 0) + (b.sh || 0) * 0.25) - ((a.gls || 0) * 3 + (a.sot || 0) + (a.sh || 0) * 0.25))
    .slice(0, 8);
}

function calcProbabilities(homeStats, awayStats, h2hSummary) {
  const hHome = homeStats?.home;
  const aAway = awayStats?.away;
  if (!hHome || !aAway) return null;
  let lambdaH = (hHome.avg_goals ?? 1.5) * 0.7 + (aAway.avg_goals_against ?? 1.2) * 0.3;
  let lambdaA = (aAway.avg_goals ?? 1.2) * 0.7 + (hHome.avg_goals_against ?? 1.3) * 0.3;
  if (h2hSummary && h2hSummary.total >= 3) {
    const h2hGoals = h2hSummary.avg_goals ?? (lambdaH + lambdaA);
    lambdaH = lambdaH * 0.88 + (h2hGoals * 0.48) * 0.12;
    lambdaA = lambdaA * 0.88 + (h2hGoals * 0.52) * 0.12;
  }
  lambdaH = clamp(lambdaH, 0.3, 5);
  lambdaA = clamp(lambdaA, 0.3, 5);
  let home = 0, draw = 0, away = 0, over25 = 0, btts = 0;
  for (let i = 0; i <= 8; i++) {
    for (let j = 0; j <= 8; j++) {
      const p = poisson(i, lambdaH) * poisson(j, lambdaA);
      if (i > j) home += p;
      else if (i === j) draw += p;
      else away += p;
      if (i + j > 2) over25 += p;
      if (i > 0 && j > 0) btts += p;
    }
  }
  const total = home + draw + away;
  return { home: home / total, draw: draw / total, away: away / total, over25, btts, lambda_h: lambdaH, lambda_a: lambdaA };
}

function poisson(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  let log = -lambda + k * Math.log(lambda);
  for (let i = 1; i <= k; i++) log -= Math.log(i);
  return Math.exp(log);
}

function formatDate(date, time) {
  if (!date) return "-";
  const d = new Date(`${date}T12:00:00`);
  const label = d.toLocaleDateString("es-ES", { weekday: "short", day: "numeric", month: "short" });
  return `${label}${time ? ` · ${time}` : ""}`;
}

function resultClass(r) {
  const v = String(r || "").toUpperCase();
  return v === "W" ? "w" : v === "D" ? "d" : "l";
}

function resultLabel(r) {
  const v = String(r || "").toUpperCase();
  return v === "W" ? "V" : v === "D" ? "E" : "D";
}

function fmt(v, dec = 2) {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(dec) : "-";
}

function pct(v, dec = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? `${(n * 100).toFixed(dec)}%` : "-";
}

function formatSigned(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "-";
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function norm(s) {
  return String(s || "").trim().toLowerCase();
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
