/**
 * apercibidos.js - official/verified suspensions page.
 */

"use strict";

const DATA_BASE = "./data/";
const DISC = { feed: null, leagues: {} };

document.addEventListener("DOMContentLoaded", initDisciplinePage);

async function initDisciplinePage() {
  try {
    const [feed, leagues, teamAssets, playerAssets] = await Promise.all([
      fetchJSON("suspensions.json"),
      fetchJSON("leagues.json").catch(() => ({})),
      fetchJSON("team_assets.json").catch(() => ({ teams: {} })),
      fetchJSON("player_assets.json").catch(() => ({ players: {} })),
    ]);
    DISC.feed = feed;
    DISC.leagues = leagues;
    window.KDXEntities?.configure(teamAssets, playerAssets);
    renderDisciplinePage();
  } catch (err) {
    document.getElementById("discipline-root").innerHTML = `<div class="state-box"><div class="icon">!</div><p>No se pudo cargar el feed de apercibidos.</p></div>`;
    console.error(err);
  }
}

async function fetchJSON(file) {
  const res = await fetch(`${DATA_BASE}${file}?v=${Date.now()}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} loading ${file}`);
  return res.json();
}

function renderDisciplinePage() {
  const root = document.getElementById("discipline-root");
  const params = new URLSearchParams(window.location.search);
  const league = params.get("league") || "all";
  const status = params.get("status") || "all";
  const items = getItems(league, status);
  const leagues = getLeagueOptions();

  root.innerHTML = `
    <section class="card match-section discipline-controls">
      <h2>Filtrar</h2>
      <div class="controls compact-controls">
        <div class="field">
          <label for="discipline-league">Liga</label>
          <select id="discipline-league">
            <option value="all">Todas</option>
            ${leagues.map(([code, data]) => `<option value="${esc(code)}" ${league === code ? "selected" : ""}>${esc(data.name || code)}</option>`).join("")}
          </select>
        </div>
        <div class="field">
          <label for="discipline-status">Estado</label>
          <select id="discipline-status">
            <option value="all" ${status === "all" ? "selected" : ""}>Todos</option>
            <option value="at_risk" ${status === "at_risk" ? "selected" : ""}>Apercibidos</option>
            <option value="suspended" ${status === "suspended" ? "selected" : ""}>Sancionados</option>
          </select>
        </div>
      </div>
      <p class="match-note">${esc(DISC.feed?.disclaimer || "")}</p>
    </section>

    <div class="match-layout">
      <section class="match-main">
        ${buildWatchTable(items)}
      </section>
      <aside class="match-side">
        ${buildSummary(items)}
        ${buildSources()}
      </aside>
    </div>
  `;

  document.getElementById("discipline-league")?.addEventListener("change", syncFilters);
  document.getElementById("discipline-status")?.addEventListener("change", syncFilters);
}

function getLeagueOptions() {
  const fromFeed = DISC.feed?.by_league || {};
  const sourceLeagues = new Set((DISC.feed?.sources || []).map(source => source.league).filter(Boolean));
  const known = Object.entries(DISC.leagues || {});
  const withData = new Set(Object.keys(fromFeed));
  return known
    .filter(([code]) => withData.has(code) || sourceLeagues.has(code))
    .concat(Object.entries(fromFeed).filter(([code]) => !(code in (DISC.leagues || {}))))
    .sort((a, b) => String(a[1].name || a[0]).localeCompare(String(b[1].name || b[0]), "es"));
}

function syncFilters() {
  const league = document.getElementById("discipline-league")?.value || "all";
  const status = document.getElementById("discipline-status")?.value || "all";
  const params = new URLSearchParams();
  if (league !== "all") params.set("league", league);
  if (status !== "all") params.set("status", status);
  const query = params.toString();
  window.location.href = query ? `apercibidos.html?${query}` : "apercibidos.html";
}

function getItems(league, status) {
  const items = league === "all"
    ? (DISC.feed?.items || [])
    : (DISC.feed?.by_league?.[league]?.items || []);
  if (status === "all") return items;
  return items.filter(item => item.status === status);
}

function buildWatchTable(items) {
  if (!items.length) {
    return sectionCard("Apercibidos oficiales", `
      <p class="muted">No hay registros oficiales/verificados para este filtro.</p>
      <p class="match-note">Cuando una liga no publica el dato de forma estructurada, KICKDEX queda vacio en vez de mostrar estimaciones.</p>
    `);
  }
  return sectionCard("Apercibidos y sancionados", `
    <div class="table-wrap match-table discipline-table">
      <table>
        <thead>
          <tr>
            <th>Jugador</th>
            <th>Equipo</th>
            <th>Liga</th>
            <th>Estado</th>
            <th>Tarjetas</th>
            <th>Jornada</th>
            <th>Fuente</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(item => `
            <tr>
              <td><a href="${playerHref(item.team, item.player)}"><span class="player-cell">${window.KDXEntities?.media("player", item.player, item.team) || ""}<b>${esc(item.player)}</b></span></a></td>
              <td>${esc(typeof teamDisplayName === "function" ? teamDisplayName(item.team) : item.team)}</td>
              <td>${esc(item.league_name || item.league || "-")}</td>
              <td>${statusBadge(item)}</td>
              <td>${cardCount(item)}</td>
              <td>${esc(item.matchday || "-")}</td>
              <td>${sourceLink(item)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `);
}

function buildSummary(items) {
  const updated = DISC.feed?.updated_at ? new Date(DISC.feed.updated_at).toLocaleString("es-ES") : "-";
  const totals = DISC.feed?.totals || {};
  return sectionCard("Resumen", `
    <div class="match-mini-grid compact">
      <div><span>Filtro</span><strong>${items.length}</strong></div>
      <div><span>Apercibidos</span><strong>${totals.at_risk || 0}</strong></div>
      <div><span>Sancionados</span><strong>${totals.suspended || 0}</strong></div>
      <div><span>Oficiales</span><strong>${totals.official || 0}</strong></div>
      <div><span>Actualizado</span><strong>${esc(updated)}</strong></div>
      <div><span>Estado</span><strong>${esc(DISC.feed?.status || "-")}</strong></div>
    </div>
  `);
}

function buildSources() {
  const sources = DISC.feed?.sources || [];
  if (!sources.length) {
    return sectionCard("Fuentes", `
      <ul class="match-coverage">
        <li><strong>Feed:</strong> Sin registros cargados todavia.</li>
        <li><strong>Regla:</strong> no se publican apercibidos si no hay fuente oficial o verificacion manual.</li>
      </ul>
    `);
  }
  return sectionCard("Fuentes", `
    <ul class="match-coverage">
      ${sources.map(source => `
        <li>
          <strong>${source.official ? "Oficial" : "Verificada"}:</strong>
          ${source.url ? `<a href="${esc(source.url)}" target="_blank" rel="noopener">${esc(source.name || source.url)}</a>` : esc(source.name || "-")}
        </li>
      `).join("")}
    </ul>
  `);
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

function sectionCard(title, body) {
  return `<section class="card match-section"><h2>${esc(title)}</h2>${body}</section>`;
}

function playerHref(team, player) {
  const params = new URLSearchParams({ team: team || "", player: player || "" });
  return `player.html?${params.toString()}`;
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
