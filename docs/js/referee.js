/**
 * referee.js - ficha individual de árbitro.
 *
 * Hero con métricas clave coloreadas contra la media de su liga, últimos
 * partidos pitados (barras + tabla con tarjetas por partido), comparación
 * visual contra la liga, ventanas disciplinarias y ranking dentro de la liga.
 */

"use strict";

const DATA_BASE = "./data/";
const REF = { referees: [], leagues: {}, fixtures: { upcoming: [], recent: [] } };
const REF_MIN_SAMPLE = 5;

document.addEventListener("DOMContentLoaded", initRefereePage);

async function initRefereePage() {
  try {
    const [referees, leagues, fixtures, teamAssets] = await Promise.all([
      fetchJSON("referees.json"),
      fetchJSON("leagues.json").catch(() => ({})),
      fetchJSON("fixtures.json").catch(() => ({ upcoming: [], recent: [] })),
      fetchJSON("team_assets.json").catch(() => ({ teams: {} })),
    ]);
    Object.assign(REF, { referees, leagues, fixtures });
    window.KDXEntities?.configure(teamAssets, { players: {} });
    renderReferee();
  } catch (err) {
    document.getElementById("referee-root").innerHTML = `<div class="state-box"><div class="icon">!</div><p>No se pudo cargar el perfil.</p></div>`;
    console.error(err);
  }
}

async function fetchJSON(file) {
  const res = await fetch(`${DATA_BASE}${file}?v=20261005a`);
  if (!res.ok) throw new Error(`HTTP ${res.status} loading ${file}`);
  return res.json();
}

function renderReferee() {
  const root = document.getElementById("referee-root");
  const ref = findRequestedReferee();
  if (!ref) {
    root.innerHTML = `
      <div class="state-box">
        <div class="icon">?</div>
        <p>No encontramos ese árbitro. Vuelve a la tabla de árbitros.</p>
        <p><a class="btn btn-primary btn-sm" href="index.html#arbitros">Volver a árbitros</a></p>
      </div>`;
    return;
  }
  const league = REF.leagues[ref.league]?.name || ref.league || "Liga";
  const stats = ref.season || ref.overall || {};
  const context = leagueContext(ref.league);
  const rank = leagueRank(ref, context);
  const upcoming = nextRefFixture(ref.name);
  document.title = `${ref.name} - Árbitro KICKDEX`;

  root.innerHTML = `
    <p style="margin:0 0 14px;"><a class="jug-back" href="index.html#arbitros" style="display:inline-block;margin:0;">← Todos los árbitros</a></p>
    <section class="match-hero card">
      <div class="ref2-hero">
        <div class="ref2-avatar">${esc(initials(ref.name))}</div>
        <div>
          <h1>${esc(ref.name)}</h1>
          <div class="ref2-tags">
            <span class="kchip">${esc(league)}</span>
            ${isActive(ref) ? '<span class="kchip kchip--under">EN ACTIVO</span>' : '<span class="kchip kchip--off">INACTIVO</span>'}
            ${profileChip(stats, context)}
            ${ref.first_match ? `<span class="kchip">DESDE ${esc(String(ref.first_match).slice(0, 4))}</span>` : ""}
            <span class="kchip">${esc(sourceLabel(ref.source || stats.source))}</span>
          </div>
        </div>
      </div>
      <div class="ref2-tiles">
        ${tile("Partidos pitados", ref.career_matches ?? ref.overall?.matches ?? ref.matches ?? 0, ref.season?.matches ? `${ref.season.matches} esta temporada` : "sin partidos esta temporada")}
        ${tile("Amarillas / partido", fmt(stats.yellows_per_match, 2), vsLeague(stats.yellows_per_match, context.yellows), tone(stats.yellows_per_match, context.yellows))}
        ${tile("Rojas / partido", fmt(stats.reds_per_match, 2), vsLeague(stats.reds_per_match, context.reds), tone(stats.reds_per_match, context.reds))}
        ${hasFouls(ref) ? tile("Faltas / partido", fmt(stats.fouls_per_match, 1), vsLeague(stats.fouls_per_match, context.fouls, 1), tone(stats.fouls_per_match, context.fouls)) : ""}
        ${rank ? tile("Ranking en su liga", `#${rank.pos}`, `de ${rank.total} por amarillas/p`, rank.pos <= Math.ceil(rank.total * 0.2) ? "hot" : rank.pos > Math.floor(rank.total * 0.8) ? "cold" : "") : ""}
      </div>
      ${upcoming ? `<div class="match-edge-chip" style="margin-top:18px;">Próximo partido <span>${esc(teamDisplayName(upcoming.home))} vs ${esc(teamDisplayName(upcoming.away))} · ${formatDate(upcoming.date, upcoming.time)}</span></div>` : ""}
    </section>

    <div class="match-layout">
      <section class="match-main">
        ${buildRecentMatches(ref, context)}
        ${buildLeagueComparison(ref, context)}
        ${buildWindowTable(ref, context)}
      </section>
      <aside class="match-side">
        ${buildLeagueRanking(ref, context)}
        ${buildCoverage(ref)}
      </aside>
    </div>
  `;
}

function tile(label, value, sub, cls = "") {
  return `<div class="ref2-tile ${cls}"><span>${esc(label)}</span><strong>${value}</strong><small class="muted">${sub || ""}</small></div>`;
}

function tone(value, avg) {
  const v = Number(value), a = Number(avg);
  if (!Number.isFinite(v) || !Number.isFinite(a) || a <= 0) return "";
  if (v >= a * 1.1) return "hot";
  if (v <= a * 0.9) return "cold";
  return "";
}

function vsLeague(value, avg, dec = 2) {
  const v = Number(value), a = Number(avg);
  if (!Number.isFinite(v) || !Number.isFinite(a)) return "sin media de liga";
  return `${kdxDiff(v - a, dec)} vs media liga (${a.toFixed(dec)})`;
}

function profileChip(stats, context) {
  const y = Number(stats.yellows_per_match), a = Number(context.yellows);
  if (!Number.isFinite(y) || !Number.isFinite(a) || a <= 0) return "";
  if (y >= a * 1.2) return '<span class="kchip kchip--over">TARJETERO</span>';
  if (y <= a * 0.8) return '<span class="kchip kchip--under">PERMISIVO</span>';
  return '<span class="kchip kchip--mid">PERFIL MEDIO</span>';
}

function sourceLabel(source) {
  return { "football-data": "PARTIDO A PARTIDO", "api-football": "PARTIDO A PARTIDO", worldsoccerdata: "AGREGADO DE TEMPORADA" }[source] || "FUENTE MIXTA";
}

function findRequestedReferee() {
  const params = new URLSearchParams(window.location.search);
  const name = params.get("name");
  const league = params.get("league");
  if (!name) return null;
  const n = norm(name);
  return REF.referees.find(r => norm(r.name) === n && (!league || r.league === league))
    || REF.referees.find(r => norm(r.name) === n)
    // "Michael Oliver" → "M Oliver": misma clave apellido + inicial que build_data.py
    || REF.referees.find(r => refKey(r.name) === refKey(name) && (!league || r.league === league))
    || null;
}

function refKey(name) {
  const parts = norm(name).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z\s]/g, "").split(/\s+/).filter(Boolean);
  if (!parts.length) return "";
  return parts.length > 1 ? `${parts[parts.length - 1]}_${parts[0][0]}` : parts[0];
}

function buildRecentMatches(ref, context) {
  const games = ref.recent_matches || [];
  if (!games.length) {
    return sectionCard("Últimos partidos", `
      <p class="muted">La fuente de esta liga solo publica el agregado de temporada del árbitro, no el detalle partido a partido.
      Por eso aquí no hay lista de partidos; las medias de arriba sí son reales.</p>`);
  }
  const avg = context.yellows;
  const chrono = games.slice().reverse();
  const max = Math.max(...chrono.map(g => (g.yellows || 0) + (g.reds || 0)), 1);
  const barCls = g => {
    if ((g.reds || 0) > 0 || (Number.isFinite(avg) && g.yellows >= avg * 1.3)) return "hot";
    if (Number.isFinite(avg) && g.yellows >= avg * 1.05) return "warm";
    if (Number.isFinite(avg) && g.yellows <= avg * 0.7) return "cold";
    return "";
  };
  const totalY = games.reduce((s, g) => s + (g.yellows || 0), 0);
  const totalR = games.reduce((s, g) => s + (g.reds || 0), 0);

  return sectionCard(`Últimos ${games.length} partidos`, `
    <p class="match-note" style="margin-top:0;">${totalY} amarillas y ${totalR} rojas en total · media ${(totalY / games.length).toFixed(2)} amarillas/p${Number.isFinite(avg) ? ` (liga ${avg.toFixed(2)})` : ""}.</p>
    <div class="ref2-spark" role="img" aria-label="Tarjetas por partido, del más antiguo al más reciente">
      ${chrono.map(g => `<div title="${esc(g.date)} · ${esc(teamDisplayName(g.home || ""))} - ${esc(teamDisplayName(g.away || ""))}: ${g.yellows ?? "?"} TA, ${g.reds ?? 0} TR">
        <b>${g.yellows ?? "·"}${g.reds ? `<span style="color:var(--red)">+${g.reds}</span>` : ""}</b>
        <i class="${barCls(g)}" style="height:${Math.max(6, (((g.yellows || 0) + (g.reds || 0)) / max) * 82)}%"></i>
      </div>`).join("")}
    </div>
    <div class="ref2-spark-labels">${chrono.map(g => `<span>${esc(shortDate(g.date))}</span>`).join("")}</div>
    <div class="table-wrap" style="margin-top:18px;">
      <table class="ktable">
        <thead><tr>
          <th>Fecha</th><th>Partido</th><th class="ctr">Resultado</th>
          <th class="ctr" title="Amarillas">TA</th><th class="ctr" title="Rojas">TR</th>
          ${games.some(g => g.fouls != null) ? '<th class="num hide-xs" title="Faltas">Faltas</th>' : ""}
        </tr></thead>
        <tbody>
          ${games.map(g => `
          <tr>
            <td class="muted" data-sort="${esc(g.date)}">${esc(formatDate(g.date))}</td>
            <td><span class="ref2-match">${teamMedia(g.home)}${esc(teamDisplayName(g.home || "-"))} <span class="muted">vs</span> ${teamMedia(g.away)}${esc(teamDisplayName(g.away || "-"))}</span></td>
            <td class="ctr"><span class="ref2-score">${g.home_score ?? "-"}–${g.away_score ?? "-"}</span></td>
            <td class="ctr" data-sort="${g.yellows ?? -1}">${kdxCardPill(g.yellows, 0, avg)}</td>
            <td class="ctr" data-sort="${g.reds ?? 0}">${g.reds ? `<i class="kcard kcard--hot">${g.reds}</i>` : '<span class="muted">0</span>'}</td>
            ${games.some(x => x.fouls != null) ? `<td class="num hide-xs">${g.fouls ?? "—"}</td>` : ""}
          </tr>`).join("")}
        </tbody>
      </table>
    </div>`);
}

function teamMedia(name) {
  return name && window.KDXEntities ? window.KDXEntities.media("team", name) : "";
}

function buildLeagueComparison(ref, context) {
  const stats = ref.season || ref.overall || {};
  const rows = [
    ["Amarillas/p", stats.yellows_per_match, context.yellows, context.maxYellows, 2],
    ["Rojas/p", stats.reds_per_match, context.reds, context.maxReds, 2],
  ];
  if (hasFouls(ref) && Number.isFinite(context.fouls)) rows.push(["Faltas/p", stats.fouls_per_match, context.fouls, context.maxFouls, 1]);
  return sectionCard("Comparación con su liga", `
    <div class="ref2-compare">
      ${rows.map(([label, v, avg, max, dec]) => {
        const val = Number(v);
        const m = Math.max(Number(max) || 0, val || 0, Number(avg) || 0) * 1.05 || 1;
        return `
        <div class="ref2-compare-row">
          <span>${label}</span>
          <div class="ref2-track" title="Barra: este árbitro · marca: media de la liga">
            <i class="ref" style="width:${Number.isFinite(val) ? (val / m) * 100 : 0}%"></i>
            ${Number.isFinite(Number(avg)) ? `<em style="left:${(avg / m) * 100}%"></em>` : ""}
          </div>
          ${kdxDiff(Number.isFinite(val) && Number.isFinite(Number(avg)) ? val - avg : NaN, dec)}
        </div>`;
      }).join("")}
    </div>
    <p class="match-note">La marca blanca es la media de los ${context.count} árbitros de ${esc(REF.leagues[ref.league]?.name || ref.league || "la liga")} con al menos ${context.minSample} partidos.</p>
  `);
}

function buildWindowTable(ref, context) {
  const blocks = [
    ["Esta temporada", ref.season],
    ["Temporada · últimos 5", ref.season_last5],
    ["Temporada · últimos 10", ref.season_last10],
    ["Últimos 5", ref.last5],
    ["Últimos 10", ref.last10],
    ["Histórico (ponderado)", ref.overall],
  ].filter(([, data]) => data && Number(data.matches || 0) > 0);
  if (!blocks.length) return "";
  const showFouls = blocks.some(([, d]) => d.fouls_per_match != null);
  const cell = (v, avg, dec) => {
    const t = tone(v, avg);
    const cls = t === "hot" ? "heat-risk-4" : t === "cold" ? "heat-risk-0" : "";
    return `<td class="num ${cls}">${fmt(v, dec)}</td>`;
  };
  return sectionCard("Ventanas disciplinarias", `
    <div class="table-wrap">
      <table class="ktable">
        <thead><tr><th data-nosort>Ventana</th><th class="num" data-nosort>PJ</th><th class="num" data-nosort>Amarillas/p</th><th class="num" data-nosort>Rojas/p</th>${showFouls ? '<th class="num hide-xs" data-nosort>Faltas/p</th>' : ""}<th class="hide-xs" data-nosort>Último</th></tr></thead>
        <tbody>
          ${blocks.map(([label, d]) => `
          <tr>
            <td><b style="font-family:var(--font-ui)">${esc(label)}</b></td>
            <td class="num muted">${d.matches}</td>
            ${cell(d.yellows_per_match, context.yellows, 2)}
            ${cell(d.reds_per_match, context.reds, 2)}
            ${showFouls ? `<td class="num hide-xs">${fmt(d.fouls_per_match, 1)}</td>` : ""}
            <td class="muted hide-xs">${esc(d.last_match ? formatDate(d.last_match) : "—")}</td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>
    <p class="match-note">Rojo/verde = más de un 10% por encima/debajo de la media de su liga. El histórico usa como máximo los 60 partidos más recientes, con más peso a lo reciente.</p>
  `);
}

function buildLeagueRanking(ref, context) {
  const list = context.ranked;
  if (!list.length) return "";
  const pos = list.findIndex(r => r === ref);
  const show = list.slice(0, 8);
  const extra = pos >= 8 ? [list[pos]] : [];
  const row = (r, i) => {
    const s = r.season || r.overall || {};
    const me = r === ref;
    return `<li style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--border);${me ? "color:var(--brand);font-weight:700;" : ""}">
      <span class="krank ${i < 3 ? `krank--${i + 1}` : ""}">${i + 1}</span>
      <a href="${refereeHref(r)}" style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:${me ? "var(--brand)" : "var(--text2)"}">${esc(r.name)}</a>
      <b style="font-family:var(--font-data);font-size:.82rem;">${fmt(s.yellows_per_match, 2)}</b>
    </li>`;
  };
  return sectionCard("Ranking de la liga", `
    <p class="match-note" style="margin-top:0;">Más amarillas por partido · árbitros en activo con ≥${context.minSample} PJ.</p>
    <ol style="list-style:none;margin:0;padding:0;">
      ${show.map((r, i) => row(r, i)).join("")}
      ${extra.length ? `<li class="muted" style="text-align:center;padding:4px 0;">…</li>${row(extra[0], pos)}` : ""}
    </ol>`);
}

function buildCoverage(ref) {
  return sectionCard("Cobertura", `
    <ul class="match-coverage">
      <li><strong>Temporada:</strong> ${ref.season ? "disponible" : "sin datos"}</li>
      <li><strong>Partido a partido:</strong> ${(ref.recent_matches || []).length ? "disponible" : "no (solo agregado)"}</li>
      <li><strong>Faltas:</strong> ${hasFouls(ref) ? "disponible" : "no disponible en fuente"}</li>
      <li><strong>Penaltis:</strong> ${hasPenalties(ref) ? "disponible" : "no disponible en fuente"}</li>
    </ul>
  `);
}

function isActive(r) {
  if (typeof r.active === "boolean") return r.active;
  if (r.season) return true;
  const last = r.overall?.last_match || r.last_match;
  return !last || (Date.now() - new Date(last).getTime()) / 86400000 <= 450;
}

function leagueContext(league) {
  const refs = REF.referees.filter(r => r.league === league && isActive(r));
  const maxPj = Math.max(0, ...refs.map(r => Number((r.season || r.overall || {}).matches || 0)));
  const minSample = Math.max(2, Math.min(REF_MIN_SAMPLE, Math.round(maxPj * 0.6)));
  const sample = refs.filter(r => Number((r.season || r.overall || {}).matches || 0) >= minSample);
  const pool = sample.length >= 3 ? sample : refs;
  // Faltas = 0 significa "sin dato en la fuente", no un árbitro sin faltas.
  const vals = key => pool.map(r => (r.season || r.overall || {})[key])
    .filter(v => v != null && (key !== "fouls_per_match" || Number(v) > 0))
    .map(Number).filter(Number.isFinite);
  const avg = key => { const v = vals(key); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; };
  const max = key => { const v = vals(key); return v.length ? Math.max(...v) : null; };
  const ranked = pool.slice().sort((a, b) =>
    (Number((b.season || b.overall || {}).yellows_per_match) || 0) - (Number((a.season || a.overall || {}).yellows_per_match) || 0));
  return {
    minSample,
    count: pool.length,
    yellows: avg("yellows_per_match"), reds: avg("reds_per_match"), fouls: avg("fouls_per_match"),
    maxYellows: max("yellows_per_match"), maxReds: max("reds_per_match"), maxFouls: max("fouls_per_match"),
    ranked,
  };
}

function leagueRank(ref, context) {
  const pos = context.ranked.indexOf(ref);
  return pos >= 0 ? { pos: pos + 1, total: context.ranked.length } : null;
}

function nextRefFixture(name) {
  return (REF.fixtures.upcoming || []).find(f => norm(f.referee || f.Referee) === norm(name)) || null;
}

function hasFouls(ref) {
  return [ref.season, ref.overall, ref.last5, ref.last10].some(block => block?.fouls_per_match != null && Number.isFinite(Number(block.fouls_per_match)));
}

function hasPenalties(ref) {
  return [ref.season, ref.overall, ref.last5, ref.last10].some(block => block?.penalties_per_match != null && Number.isFinite(Number(block.penalties_per_match)));
}

function sectionCard(title, body) {
  return `<section class="card match-section"><h2>${title}</h2>${body}</section>`;
}

function refereeHref(ref) {
  const params = new URLSearchParams({ name: ref.name || "", league: ref.league || "" });
  return `referee.html?${params.toString()}`;
}

function initials(name) {
  return String(name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join("").toUpperCase();
}

function formatDate(date, time) {
  if (!date) return "-";
  const d = new Date(`${date}T12:00:00`);
  return `${d.toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "2-digit" })}${time ? ` · ${time}` : ""}`;
}

function shortDate(date) {
  if (!date) return "";
  const d = new Date(`${date}T12:00:00`);
  return d.toLocaleDateString("es-ES", { day: "numeric", month: "numeric" });
}

function fmt(value, dec = 2) {
  if (value == null) return "-";
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(dec) : "-";
}

function norm(value) {
  return String(value || "").trim().toLowerCase();
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
