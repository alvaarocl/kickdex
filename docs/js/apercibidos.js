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
      fetchJSON("leagues.json").catch(() => ({})).then(l => fetchJSON("competitions.json").catch(() => ({})).then(c => mergeCompetitions(l, c))),
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
  const state = { league: params.get("league") || "all", status: params.get("status") || "all", q: "" };
  const feed = DISC.feed || {};
  const all = feed.items || [];
  const leagueCodes = Object.keys(feed.by_league || {});
  const order = Object.keys(DISC.leagues || {}).filter(c => leagueCodes.includes(c))
    .concat(leagueCodes.filter(c => !(c in (DISC.leagues || {}))))
    .sort((a, b) => (DISC.leagues?.[b]?.competition ? 1 : 0) - (DISC.leagues?.[a]?.competition ? 1 : 0));
  const rules = {};
  all.forEach(i => { if (i.rule && !rules[i.league]) rules[i.league] = { text: i.rule, confidence: i.confidence }; });

  root.innerHTML = `
    <div class="kstat-grid" id="disc-stats"></div>
    <div class="ktoolbar">
      <select id="disc-league" class="ksearch" style="max-width:260px" aria-label="Competición">
        <option value="all">Todas las competiciones</option>
        ${[["Competiciones europeas", order.filter(c => DISC.leagues?.[c]?.competition)],
           ["Ligas nacionales", order.filter(c => !DISC.leagues?.[c]?.competition)]]
          .filter(([, list]) => list.length)
          .map(([label, list]) => `<optgroup label="${label}">${list.map(c =>
            `<option value="${esc(c)}">${esc(DISC.leagues?.[c]?.name || feed.by_league?.[c]?.name || c)}</option>`).join("")}</optgroup>`).join("")}
      </select>
      <button type="button" class="ktoggle" data-status="all">Todos</button>
      <button type="button" class="ktoggle" data-status="suspended">Sancionados</button>
      <button type="button" class="ktoggle" data-status="at_risk">Apercibidos</button>
      <input id="disc-q" class="ksearch" type="search" placeholder="Buscar jugador o equipo…" autocomplete="off" />
    </div>
    <div id="disc-body"></div>
    <p class="match-note" style="margin-top:18px;">${esc(feed.disclaimer || "")}
      Actualizado ${feed.updated_at ? new Date(feed.updated_at).toLocaleString("es-ES") : "-"}.</p>`;

  const leagueSel = document.getElementById("disc-league");
  leagueSel.value = order.includes(state.league) ? state.league : "all";

  const draw = () => {
    const q = state.q.trim().toLowerCase();
    const items = all.filter(i =>
      (state.league === "all" || i.league === state.league) &&
      (state.status === "all" || i.status === state.status) &&
      (!q || `${i.player} ${discTeamName(i.team)} ${i.team}`.toLowerCase().includes(q)));
    const sus = items.filter(i => i.status === "suspended");
    const risk = items.filter(i => i.status === "at_risk");
    document.getElementById("disc-stats").innerHTML = `
      <div class="kstat kstat--red"><span>Sancionados</span><strong>${sus.length}</strong><small>se pierden su próximo partido</small></div>
      <div class="kstat kstat--gold"><span>Apercibidos</span><strong>${risk.length}</strong><small>a una amarilla de la sanción</small></div>
      <div class="kstat kstat--blue"><span>Ligas</span><strong>${new Set(items.map(i => i.league)).size}</strong><small>con algún jugador en la lista</small></div>
      <div class="kstat kstat--green"><span>Oficiales</span><strong>${items.filter(i => i.official || i.verified).length}</strong><small>confirmados por la competición</small></div>`;
    document.querySelectorAll(".ktoggle[data-status]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.status === state.status)));

    const codes = order.filter(c => items.some(i => i.league === c));
    document.getElementById("disc-body").innerHTML = codes.length ? codes.map(code => {
      const s = sus.filter(i => i.league === code);
      const r = risk.filter(i => i.league === code);
      const rule = rules[code];
      return `
      <section class="card match-section disc-league">
        <h2>${esc(DISC.leagues?.[code]?.name || code)}
          <small class="muted" style="font:500 .78rem var(--font-ui);letter-spacing:0;text-transform:none;margin-left:8px;">
            ${s.length} sancionado${s.length === 1 ? "" : "s"} · ${r.length} apercibido${r.length === 1 ? "" : "s"}</small></h2>
        ${rule ? `<p class="match-note" style="margin-top:0;">Regla: ${esc(rule.text)} · fiabilidad ${esc(rule.confidence)}. Doble amarilla: 1 partido. Roja directa: mínimo 1 (decide el comité).</p>` : ""}
        ${s.length ? `<h3 class="disc-h3 disc-h3--red">Sancionados</h3>${discSuspendedTable(s, { playerHref })}` : ""}
        ${r.length ? `<h3 class="disc-h3 disc-h3--gold">Apercibidos</h3>${discRiskTable(r, { playerHref })}` : ""}
      </section>`;
    }).join("") : `<div class="state-box"><div class="icon">✓</div><p>Nadie en la lista para este filtro.</p></div>`;
  };

  leagueSel.addEventListener("change", () => { state.league = leagueSel.value; syncUrl(state); draw(); });
  document.querySelectorAll(".ktoggle[data-status]").forEach(b => b.addEventListener("click", () => {
    state.status = b.dataset.status; syncUrl(state); draw();
  }));
  document.getElementById("disc-q").addEventListener("input", e => { state.q = e.target.value; draw(); });
  draw();
}

function syncUrl(state) {
  const params = new URLSearchParams();
  if (state.league !== "all") params.set("league", state.league);
  if (state.status !== "all") params.set("status", state.status);
  history.replaceState(null, "", params.toString() ? `apercibidos.html?${params}` : "apercibidos.html");
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
