/**
 * player.js - standalone player profile.
 */

"use strict";

const DATA_BASE = "./data/";
const PLAYER = { players: {}, details: {}, leagues: {}, coverage: null, teamAssets: { teams: {} }, playerAssets: { players: {} } };

document.addEventListener("DOMContentLoaded", initPlayerPage);

async function initPlayerPage() {
  try {
    const [players, details, leagues, coverage, teamAssets, playerAssets] = await Promise.all([
      fetchJSON("players.json"),
      fetchJSON("players_detail.json").catch(() => ({})),
      fetchJSON("leagues.json").catch(() => ({})),
      fetchJSON("player_coverage.json").catch(() => null),
      fetchJSON("team_assets.json").catch(() => ({ teams: {} })),
      fetchJSON("player_assets.json").catch(() => ({ players: {} })),
    ]);
    Object.assign(PLAYER, { players, details, leagues, coverage, teamAssets, playerAssets });
    window.KDXEntities?.configure(teamAssets, playerAssets);
    renderPlayer();
  } catch (err) {
    document.getElementById("player-root").innerHTML = `<div class="state-box"><div class="icon">!</div><p>No se pudo cargar el perfil.</p></div>`;
    console.error(err);
  }
}

async function fetchJSON(file) {
  const res = await fetch(`${DATA_BASE}${file}?v=20260823a`);
  if (!res.ok) throw new Error(`HTTP ${res.status} loading ${file}`);
  return res.json();
}

function renderPlayer() {
  const root = document.getElementById("player-root");
  const found = findRequestedPlayer();
  if (!found) {
    root.innerHTML = `
      <div class="state-box">
        <div class="icon">?</div>
        <p>No encontramos ese jugador. Vuelve a la pestana de jugadores.</p>
        <p><a class="btn btn-primary btn-sm" href="index.html">Volver</a></p>
      </div>`;
    return;
  }

  const { team, player, aggregate, detail } = found;
  const leagueCode = getLeagueForTeam(team);
  const league = PLAYER.leagues[leagueCode]?.name || leagueCode || "Liga";
  const matchLog = realMatchLog(detail);
  const avg = aggregate || aggregateStats(detail);
  const teamPlayers = PLAYER.players[team] || [];
  const ranks = buildRanks(teamPlayers, player);
  const profile = playerProfileLabel(avg, ranks);
  document.title = `${player} - Jugador KICKDEX`;

  root.innerHTML = `
    <section class="match-hero card">
      <div class="match-kicker">
        <span>${esc(league)}</span>
        <span>${esc(teamDisplayName(team))}</span>
        <span>${matchLog.length ? `${matchLog.length} registros` : "promedio temporada"}</span>
      </div>
      <div class="referee-hero-row player-hero-row">
        ${window.KDXEntities?.media("player", player, team, "player-avatar player-avatar--hero") || `<div class="ref-avatar player-avatar">${initials(player)}</div>`}
        <div>
          <h1>${esc(player)}</h1>
          <p>${profile} basado en datos disponibles de temporada.</p>
        </div>
      </div>
      <div class="match-edge-chip">Ficha de jugador <span>${esc(teamDisplayName(team))} · ${esc(league)}</span></div>
    </section>

    <div class="match-layout">
      <section class="match-main">
        ${buildCoreMetrics(avg)}
        ${buildPer90Metrics(avg)}
        ${buildRankSection(ranks, teamPlayers.length)}
        ${buildDetailSection(matchLog, detail)}
      </section>
      <aside class="match-side">
        ${buildFacts(player, team, league, avg, matchLog)}
        ${buildCoverage(leagueCode, matchLog)}
        ${buildTeamLeaders(teamPlayers, team)}
      </aside>
    </div>
  `;
}

function findRequestedPlayer() {
  const params = new URLSearchParams(window.location.search);
  const teamParam = params.get("team");
  const playerParam = params.get("player");

  if (!playerParam && !teamParam) return firstPlayer();

  const teams = teamParam && PLAYER.players[teamParam] ? [teamParam] : Object.keys(PLAYER.players);
  for (const team of teams) {
    const row = (PLAYER.players[team] || []).find(p => norm(p.player) === norm(playerParam));
    if (row) return { team, player: row.player, aggregate: row, detail: PLAYER.details[team]?.[row.player] || [] };
  }

  for (const team of Object.keys(PLAYER.details || {})) {
    const key = Object.keys(PLAYER.details[team] || {}).find(name => norm(name) === norm(playerParam));
    if (!key) continue;
    const row = (PLAYER.players[team] || []).find(p => norm(p.player) === norm(key));
    return { team, player: key, aggregate: row || null, detail: PLAYER.details[team]?.[key] || [] };
  }

  return null;
}

function firstPlayer() {
  for (const [team, rows] of Object.entries(PLAYER.players || {})) {
    if (rows && rows[0]) return { team, player: rows[0].player, aggregate: rows[0], detail: PLAYER.details[team]?.[rows[0].player] || [] };
  }
  return null;
}

function buildCoreMetrics(avg) {
  return sectionCard("Medias por partido", `
    <div class="match-mini-grid player-metric-grid">
      ${metric("Min/p", fmt(avg.min, 0))}
      ${metric("Goles/p", fmt(avg.gls, 2), "hot")}
      ${metric("Asist/p", fmt(avg.ast, 2), "blue")}
      ${metric("Disp/p", fmt(avg.sh, 1))}
      ${metric("SoT/p", fmt(avg.sot, 1), "hot")}
      ${metric("TA/p", fmt(avg.crdy, 2), "warn")}
    </div>
  `);
}

function buildPer90Metrics(avg) {
  return sectionCard("Ritmo P90 aproximado", `
    <div class="match-mini-grid player-metric-grid">
      ${metric("Goles P90", fmt(per90(avg.gls, avg.min), 2), "hot")}
      ${metric("Asist P90", fmt(per90(avg.ast, avg.min), 2), "blue")}
      ${metric("Disp P90", fmt(per90(avg.sh, avg.min), 1))}
      ${metric("SoT P90", fmt(per90(avg.sot, avg.min), 1), "hot")}
      ${metric("Faltas P90", fmt(per90(avg.fls, avg.min), 1), "warn")}
      ${metric("TA P90", fmt(per90(avg.crdy, avg.min), 2), "warn")}
    </div>
    <p class="match-note">P90 transforma el promedio por partido a una base de 90 minutos usando los minutos medios del jugador.</p>
  `);
}

function buildRankSection(ranks, total) {
  return sectionCard("Contexto dentro del equipo", `
    <div class="match-mini-grid player-rank-grid">
      ${rankMetric("Disparos", ranks.sh, total)}
      ${rankMetric("SoT", ranks.sot, total)}
      ${rankMetric("Goles", ranks.gls, total)}
      ${rankMetric("Asist.", ranks.ast, total)}
      ${rankMetric("Faltas", ranks.fls, total)}
      ${rankMetric("Tarjetas", ranks.crdy, total)}
    </div>
  `);
}

function buildDetailSection(matchLog, rawDetail) {
  if (!matchLog.length) {
    return sectionCard("Detalle partido a partido", `
      <div class="player-data-note">
        <p>Esta fuente entrega el jugador como agregado de temporada. KICKDEX mantiene la ficha activa y muestra medias, P90 y ranking de equipo, pero no inventa ultimos 5/10 si no hay registros reales por fecha.</p>
        <p class="match-note">Registros brutos disponibles: ${(rawDetail || []).length || 1}.</p>
      </div>
    `);
  }

  return sectionCard("Ultimos registros", `
    <div class="table-wrap match-table">
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Min</th>
            <th>Goles</th>
            <th>Asist</th>
            <th>Disp</th>
            <th>SoT</th>
            <th>Faltas</th>
            <th>TA</th>
          </tr>
        </thead>
        <tbody>
          ${matchLog.slice(0, 12).map(row => `
            <tr>
              <td class="muted">${esc(row.date || "-")}</td>
              <td>${cell(row.min, 0)}</td>
              <td>${cell(row.gls, 0, "hot")}</td>
              <td>${cell(row.ast, 0, "blue")}</td>
              <td>${cell(row.sh, 1)}</td>
              <td>${cell(row.sot, 1)}</td>
              <td>${cell(row.fls, 1)}</td>
              <td>${cell(row.crdy, 0, "warn")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `);
}

function buildFacts(player, team, league, avg, matchLog) {
  return sectionCard("Ficha", `
    <dl class="match-facts">
      <dt>Jugador</dt><dd>${esc(player)}</dd>
      <dt>Equipo</dt><dd>${esc(teamDisplayName(team))}</dd>
      <dt>Liga</dt><dd>${esc(league)}</dd>
      <dt>Min/p</dt><dd>${fmt(avg.min, 0)}</dd>
      <dt>Formato</dt><dd>${matchLog.length ? "partido a partido" : "agregado"}</dd>
    </dl>
  `);
}

function buildCoverage(leagueCode, matchLog) {
  const leagueCoverage = PLAYER.coverage?.by_league?.[leagueCode];
  const updated = PLAYER.coverage?.updated_at ? new Date(PLAYER.coverage.updated_at).toLocaleString("es-ES") : "-";
  return sectionCard("Cobertura", `
    <ul class="match-coverage">
      <li><strong>Actualizado:</strong> ${esc(updated)}</li>
      <li><strong>Equipos con datos:</strong> ${leagueCoverage ? `${leagueCoverage.teams_with_players}/${leagueCoverage.expected_teams}` : "-"}</li>
      <li><strong>Jugadores liga:</strong> ${leagueCoverage?.player_rows ?? "-"}</li>
      <li><strong>Partido a partido:</strong> ${matchLog.length ? "disponible" : "no disponible en esta fuente"}</li>
    </ul>
  `);
}

function buildTeamLeaders(rows, team) {
  const leaders = [
    ["Goles/p", topStat(rows, "gls")],
    ["Disp/p", topStat(rows, "sh")],
    ["SoT/p", topStat(rows, "sot")],
  ];
  return sectionCard(`Lideres ${esc(teamDisplayName(team))}`, `
    <div class="player-leaders">
      ${leaders.map(([label, item]) => `
        <a href="${playerHref(team, item?.player || "")}">
          <span>${esc(label)}</span>
          <strong>${esc(item?.player || "-")}</strong>
          <em>${fmt(item?.value, label === "Disp/p" || label === "SoT/p" ? 1 : 2)}</em>
        </a>
      `).join("")}
    </div>
  `);
}

function buildRanks(rows, player) {
  const rank = key => {
    const sorted = rows
      .filter(r => Number.isFinite(Number(r[key])))
      .slice()
      .sort((a, b) => Number(b[key]) - Number(a[key]));
    const idx = sorted.findIndex(r => norm(r.player) === norm(player));
    return idx >= 0 ? idx + 1 : null;
  };
  return { sh: rank("sh"), sot: rank("sot"), gls: rank("gls"), ast: rank("ast"), fls: rank("fls"), crdy: rank("crdy") };
}

function rankMetric(label, rank, total) {
  const value = rank ? `#${rank}` : "-";
  return `<div><span>${esc(label)}</span><strong>${value}</strong><em class="match-note">de ${total || "-"} jugadores</em></div>`;
}

function metric(label, value, tone = "") {
  const cls = tone === "hot" ? "player-hot" : tone === "blue" ? "player-blue" : tone === "warn" ? "player-warn" : "";
  return `<div><span>${esc(label)}</span><strong class="${cls}">${esc(value)}</strong></div>`;
}

function sectionCard(title, body) {
  return `<section class="card match-section"><h2>${esc(title)}</h2>${body}</section>`;
}

function topStat(rows, key) {
  const item = (rows || []).slice().sort((a, b) => (Number(b[key]) || 0) - (Number(a[key]) || 0))[0];
  return item ? { player: item.player, value: item[key] } : null;
}

function aggregateStats(detail) {
  const rows = detail || [];
  const n = rows.length || 1;
  const sum = key => rows.reduce((acc, row) => acc + (Number(row[key]) || 0), 0);
  return { sh: sum("sh") / n, sot: sum("sot") / n, gls: sum("gls") / n, ast: sum("ast") / n, min: sum("min") / n, fls: sum("fls") / n, crdy: sum("crdy") / n };
}

function realMatchLog(detail) {
  return (detail || []).filter(row => {
    const date = String(row.date || "").trim().toLowerCase();
    return date && date !== "nat" && date !== "nan" && date !== "none";
  });
}

function playerProfileLabel(avg, ranks) {
  if (ranks.gls && ranks.gls <= 3) return "perfil goleador";
  if (ranks.sh && ranks.sh <= 3) return "perfil de alto volumen de tiro";
  if (ranks.crdy && ranks.crdy <= 3 && Number(avg.crdy) >= 0.2) return "perfil disciplinario alto";
  if (Number(avg.min) >= 75) return "titular de alta carga";
  return "perfil de rotacion o contribucion especifica";
}

function per90(value, minutes) {
  const v = Number(value);
  const m = Number(minutes);
  if (!Number.isFinite(v) || !Number.isFinite(m) || m <= 0) return null;
  return v * 90 / m;
}

function cell(value, dec = 1, tone = "") {
  const out = fmt(value, dec);
  const cls = tone === "hot" ? "player-hot" : tone === "blue" ? "player-blue" : tone === "warn" ? "player-warn" : "";
  return cls && Number(value) > 0 ? `<b class="${cls}">${out}</b>` : out;
}

function playerHref(team, player) {
  const params = new URLSearchParams({ team: team || "", player: player || "" });
  return `player.html?${params.toString()}`;
}

function getLeagueForTeam(team) {
  for (const [code, data] of Object.entries(PLAYER.leagues || {})) {
    if ((data.teams || []).includes(team)) return code;
  }
  return null;
}

function initials(name) {
  return String(name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join("").toUpperCase();
}

function fmt(value, dec = 2) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(dec) : "-";
}

function norm(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
