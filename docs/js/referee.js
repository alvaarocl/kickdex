/**
 * referee.js - standalone referee profile.
 */

"use strict";

const DATA_BASE = "./data/";
const REF = { referees: [], leagues: {}, fixtures: { upcoming: [], recent: [] } };

document.addEventListener("DOMContentLoaded", initRefereePage);

async function initRefereePage() {
  try {
    const [referees, leagues, fixtures] = await Promise.all([
      fetchJSON("referees.json"),
      fetchJSON("leagues.json").catch(() => ({})),
      fetchJSON("fixtures.json").catch(() => ({ upcoming: [], recent: [] })),
    ]);
    Object.assign(REF, { referees, leagues, fixtures });
    renderReferee();
  } catch (err) {
    document.getElementById("referee-root").innerHTML = `<div class="state-box"><div class="icon">!</div><p>No se pudo cargar el perfil.</p></div>`;
    console.error(err);
  }
}

async function fetchJSON(file) {
  const res = await fetch(`${DATA_BASE}${file}?v=20260823a`);
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
        <p>No encontramos ese arbitro. Vuelve a la tabla de arbitros.</p>
        <p><a class="btn btn-primary btn-sm" href="index.html">Volver</a></p>
      </div>`;
    return;
  }
  const league = REF.leagues[ref.league]?.name || ref.league || "Liga";
  const context = leagueContext(ref.league);
  const upcoming = nextRefFixture(ref.name);
  document.title = `${ref.name} - Arbitro KICKDEX`;

  root.innerHTML = `
    <section class="match-hero card">
      <div class="match-kicker">
        <span>${esc(league)}</span>
        <span>${esc(ref.source || "fuente mixta")}</span>
        <span>${Number(ref.matches || 0)} partidos</span>
      </div>
      <div class="referee-hero-row">
        <div class="ref-avatar">${initials(ref.name)}</div>
        <div>
          <h1>${esc(ref.name)}</h1>
          <p>${disciplineLabel(ref.season || ref.overall)} · comparado contra media de liga.</p>
        </div>
      </div>
      ${upcoming ? `<div class="match-edge-chip">Proximo partido <span>${esc(teamDisplayName(upcoming.home))} vs ${esc(teamDisplayName(upcoming.away))} · ${formatDate(upcoming.date, upcoming.time)}</span></div>` : ""}
    </section>

    <div class="match-layout">
      <section class="match-main">
        ${buildWindowCards(ref)}
        ${buildLeagueComparison(ref, context)}
      </section>
      <aside class="match-side">
        ${buildRefFacts(ref, league)}
        ${buildCoverage(ref)}
      </aside>
    </div>
  `;
}

function findRequestedReferee() {
  const params = new URLSearchParams(window.location.search);
  const name = params.get("name");
  const league = params.get("league");
  if (!name) return REF.referees[0] || null;
  return REF.referees.find(r => norm(r.name) === norm(name) && (!league || r.league === league))
    || REF.referees.find(r => norm(r.name) === norm(name))
    || null;
}

function buildWindowCards(ref) {
  const blocks = [
    ["Temporada", ref.season],
    ["Ultimos 5 temporada", ref.season_last5],
    ["Ultimos 10 temporada", ref.season_last10],
    ["Historico", ref.overall],
    ["Ultimos 5 historico", ref.last5],
    ["Ultimos 10 historico", ref.last10],
  ].filter(([, data]) => data && Number(data.matches || 0) > 0);

  return sectionCard("Ventanas disciplinarias", `
    <div class="ref-window-grid">
      ${blocks.map(([label, data]) => statWindow(label, data)).join("")}
    </div>
  `);
}

function statWindow(label, data) {
  return `
    <div class="ref-window-card">
      <h3>${esc(label)}</h3>
      <div class="match-mini-grid compact">
        <div><span>PJ</span><strong>${data.matches || 0}</strong></div>
        <div><span>TA/p</span><strong>${fmt(data.yellows_per_match, 2)}</strong></div>
        <div><span>TR/p</span><strong>${fmt(data.reds_per_match, 2)}</strong></div>
        <div><span>Faltas/p</span><strong>${fmt(data.fouls_per_match, 2)}</strong></div>
      </div>
      <p class="match-note">Ultimo partido: ${esc(data.last_match || "-")}</p>
    </div>`;
}

function buildLeagueComparison(ref, context) {
  const stats = ref.season || ref.overall || {};
  const yp = Number(stats.yellows_per_match);
  const rp = Number(stats.reds_per_match);
  const yellowDiff = Number.isFinite(yp) && Number.isFinite(context.yellows) ? yp - context.yellows : null;
  const redDiff = Number.isFinite(rp) && Number.isFinite(context.reds) ? rp - context.reds : null;
  return sectionCard("Comparacion contra liga", `
    <div class="match-mini-grid">
      <div><span>Media liga TA</span><strong>${fmt(context.yellows, 2)}</strong></div>
      <div><span>Este arbitro TA</span><strong>${fmt(yp, 2)}</strong></div>
      <div><span>Diferencia TA</span><strong class="${yellowDiff >= 0 ? "ref-hot" : "ref-cold"}">${signed(yellowDiff)}</strong></div>
      <div><span>Media liga TR</span><strong>${fmt(context.reds, 2)}</strong></div>
      <div><span>Este arbitro TR</span><strong>${fmt(rp, 2)}</strong></div>
      <div><span>Diferencia TR</span><strong class="${redDiff >= 0 ? "ref-hot" : "ref-cold"}">${signed(redDiff)}</strong></div>
    </div>
    <p class="match-note">Contexto calculado con ${context.count} arbitros de ${esc(REF.leagues[ref.league]?.name || ref.league || "la liga")}.</p>
  `);
}

function buildRefFacts(ref, league) {
  const stats = ref.season || ref.overall || {};
  return sectionCard("Ficha", `
    <dl class="match-facts">
      <dt>Arbitro</dt><dd>${esc(ref.name)}</dd>
      <dt>Liga</dt><dd>${esc(league)}</dd>
      <dt>Fuente</dt><dd>${esc(ref.source || stats.source || "-")}</dd>
      <dt>PJ temp.</dt><dd>${ref.season?.matches || 0}</dd>
      <dt>PJ total</dt><dd>${ref.overall?.matches || ref.matches || 0}</dd>
      <dt>Ultimo</dt><dd>${esc(stats.last_match || "-")}</dd>
    </dl>
  `);
}

function buildCoverage(ref) {
  return sectionCard("Cobertura", `
    <ul class="match-coverage">
      <li><strong>Temporada:</strong> ${ref.season ? "disponible" : "sin datos"}</li>
      <li><strong>Ultimos 5:</strong> ${ref.season_last5 || ref.last5 ? "disponible" : "sin muestra"}</li>
      <li><strong>Faltas:</strong> ${hasFouls(ref) ? "disponible" : "no disponible en fuente"}</li>
      <li><strong>Penaltis:</strong> ${hasPenalties(ref) ? "disponible" : "no disponible en fuente"}</li>
    </ul>
  `);
}

function leagueContext(league) {
  const refs = REF.referees.filter(r => r.league === league);
  const avg = key => {
    const values = refs.map(r => Number((r.season || r.overall || {})[key])).filter(Number.isFinite);
    return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  };
  return { count: refs.length, yellows: avg("yellows_per_match"), reds: avg("reds_per_match") };
}

function nextRefFixture(name) {
  return (REF.fixtures.upcoming || []).find(f => norm(f.referee || f.Referee) === norm(name)) || null;
}

function disciplineLabel(stats) {
  const yp = Number(stats?.yellows_per_match);
  if (!Number.isFinite(yp)) return "perfil disciplinario parcial";
  if (yp >= 5) return "perfil alto en tarjetas";
  if (yp <= 2.8) return "perfil bajo en tarjetas";
  return "perfil disciplinario medio";
}

function hasFouls(ref) {
  return [ref.season, ref.overall, ref.last5, ref.last10].some(block => Number.isFinite(Number(block?.fouls_per_match)));
}

function hasPenalties(ref) {
  return [ref.season, ref.overall, ref.last5, ref.last10].some(block => Number.isFinite(Number(block?.penalties_per_match)));
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
  return `${d.toLocaleDateString("es-ES", { day: "numeric", month: "short" })}${time ? ` · ${time}` : ""}`;
}

function fmt(value, dec = 2) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(dec) : "-";
}

function signed(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}`;
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
