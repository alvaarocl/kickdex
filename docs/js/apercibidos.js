/**
 * apercibidos.js - discipline watchlist page.
 */

"use strict";

const DATA_BASE = "./data/";
const DISC = { watch: null, leagues: {} };

document.addEventListener("DOMContentLoaded", initDisciplinePage);

async function initDisciplinePage() {
  try {
    const [watch, leagues] = await Promise.all([
      fetchJSON("discipline_watch.json"),
      fetchJSON("leagues.json").catch(() => ({})),
    ]);
    DISC.watch = watch;
    DISC.leagues = leagues;
    renderDisciplinePage();
  } catch (err) {
    document.getElementById("discipline-root").innerHTML = `<div class="state-box"><div class="icon">!</div><p>No se pudo cargar la watchlist.</p></div>`;
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
  const items = getItems(league);
  const leagues = Object.entries(DISC.watch?.by_league || {});

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
      </div>
      <p class="match-note">${esc(DISC.watch?.disclaimer || "")}</p>
    </section>

    <div class="match-layout">
      <section class="match-main">
        ${buildWatchTable(items)}
      </section>
      <aside class="match-side">
        ${buildSummary(items)}
        ${buildMethod()}
      </aside>
    </div>
  `;

  document.getElementById("discipline-league")?.addEventListener("change", event => {
    const value = event.target.value;
    const url = value === "all" ? "apercibidos.html" : `apercibidos.html?league=${encodeURIComponent(value)}`;
    window.location.href = url;
  });
}

function getItems(league) {
  if (league !== "all") return DISC.watch?.by_league?.[league]?.players || [];
  return DISC.watch?.top || [];
}

function buildWatchTable(items) {
  if (!items.length) return sectionCard("Watchlist", `<p class="muted">No hay jugadores con riesgo relevante en este filtro.</p>`);
  return sectionCard("Watchlist de tarjetas", `
    <div class="table-wrap match-table discipline-table">
      <table>
        <thead>
          <tr>
            <th>Jugador</th>
            <th>Equipo</th>
            <th>Liga</th>
            <th>TA/p</th>
            <th>TA P90</th>
            <th>Min/p</th>
            <th>Riesgo</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(item => `
            <tr>
              <td><a href="${playerHref(item.team, item.player)}"><b>${esc(item.player)}</b></a></td>
              <td>${esc(item.team)}</td>
              <td>${esc(item.league_name || item.league || "-")}</td>
              <td>${fmt(item.yellow_cards_per_match, 2)}</td>
              <td>${fmt(item.yellow_cards_p90, 2)}</td>
              <td>${fmt(item.minutes_per_match, 0)}</td>
              <td><span class="discipline-risk discipline-risk--${esc(item.risk)}">${esc(item.risk)}</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `);
}

function buildSummary(items) {
  const high = items.filter(item => item.risk === "alto").length;
  const updated = DISC.watch?.updated_at ? new Date(DISC.watch.updated_at).toLocaleString("es-ES") : "-";
  return sectionCard("Resumen", `
    <div class="match-mini-grid compact">
      <div><span>Jugadores</span><strong>${items.length}</strong></div>
      <div><span>Riesgo alto</span><strong>${high}</strong></div>
      <div><span>Actualizado</span><strong>${esc(updated)}</strong></div>
      <div><span>Estado</span><strong>No oficial</strong></div>
    </div>
  `);
}

function buildMethod() {
  const th = DISC.watch?.thresholds || {};
  return sectionCard("Metodo", `
    <ul class="match-coverage">
      <li><strong>Fuente:</strong> ${esc(DISC.watch?.source || "players.json")}</li>
      <li><strong>Minimos:</strong> ${th.min_minutes_per_match || 25} min/p y ${th.min_yellow_cards_per_match || 0.12} TA/p.</li>
      <li><strong>Alto:</strong> ${th.high_risk_yellow_cards_per_match || 0.28} TA/p o ${th.high_risk_yellow_cards_p90 || 0.38} TA P90.</li>
      <li><strong>Limitacion:</strong> No suma acumulaciones oficiales por competicion.</li>
    </ul>
  `);
}

function sectionCard(title, body) {
  return `<section class="card match-section"><h2>${esc(title)}</h2>${body}</section>`;
}

function playerHref(team, player) {
  const params = new URLSearchParams({ team: team || "", player: player || "" });
  return `player.html?${params.toString()}`;
}

function fmt(value, dec = 2) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(dec) : "-";
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
