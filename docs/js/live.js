/**
 * live.js - Tab "Directo": marcador con retraso vía football-data.org.
 *
 * Honestidad ante todo: el plan gratuito de football-data.org NO incluye
 * datos en vivo, así que esto es un marcador que se refresca cada ~15 min
 * (ver .github/workflows/update_live_scores.yml), nunca minuto a minuto.
 * Se etiqueta como "con retraso" en todo momento — nunca como "en directo".
 */

"use strict";

const LIVE_POLL_MS = 120000; // Recargar el JSON estático cada ~2 min mientras la pestaña esté visible.
let _liveTimer = null;

function initLive() {
  fetchLiveScores();

  document.addEventListener("kdx:tab-open", e => {
    if (e.detail?.tab === "live") fetchLiveScores();
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      clearInterval(_liveTimer);
      _liveTimer = null;
    } else if (!_liveTimer) {
      _liveTimer = setInterval(fetchLiveScores, LIVE_POLL_MS);
    }
  });
  _liveTimer = setInterval(fetchLiveScores, LIVE_POLL_MS);
}

async function fetchLiveScores() {
  try {
    const data = await fetchJSON("live_scores.json");
    APP.liveScores = data;
    renderLive(data);
  } catch (err) {
    console.warn("Live scores load failed:", err);
    renderLive(null);
  }
}

function renderLive(data) {
  const chip = document.getElementById("liveStatusChip");
  const status = document.getElementById("liveDataStatus");
  const root = document.getElementById("live-root");
  if (!root) return;

  const enabled = !!data?.enabled;
  const updated = data?.updated_at ? new Date(data.updated_at).toLocaleString("es-ES") : null;

  if (chip) {
    chip.textContent = enabled ? "DIRECTO · CON RETRASO" : "DIRECTO · OFF";
    chip.classList.toggle("live-status-chip--on", enabled);
  }
  if (status) {
    status.textContent = enabled
      ? `${data.note || "Datos con retraso, no en directo."} ${updated ? "· Actualizado " + updated : ""}`
      : (data?.note || "Directo desactivado: falta configurar el acceso a football-data.org.");
  }

  if (!enabled) {
    root.innerHTML = `
    <div class="fx-empty">
      Directo desactivado. En cuanto se configure el acceso gratuito a
      football-data.org, aquí aparecerá un marcador con retraso (~15 min),
      etiquetado siempre como tal — nunca como datos en vivo simulados.
    </div>`;
    return;
  }

  const matches = data.matches || [];
  if (!matches.length) {
    root.innerHTML = `
    <div class="fx-empty">
      No hay partidos hoy en las ligas cubiertas (${(data.leagues_covered || []).join(", ")}).
    </div>
    ${buildLiveFallback()}`;
    return;
  }

  const byLeague = new Map();
  matches.forEach(m => {
    if (!byLeague.has(m.league)) byLeague.set(m.league, []);
    byLeague.get(m.league).push(m);
  });

  const order = typeof sortLeagueCodes === "function"
    ? sortLeagueCodes([...byLeague.keys()])
    : [...byLeague.keys()].sort();

  root.innerHTML = order.map(code => {
    const leagueName = APP.leagues?.[code]?.name || code;
    const cards = byLeague.get(code)
      .sort((a, b) => (a.utc_date || "").localeCompare(b.utc_date || ""))
      .map(liveMatchCard)
      .join("");
    return `
    <div class="fx-section-title">${escHtml(leagueName)}</div>
    ${cards}`;
  }).join("");
}

function liveMatchCard(m) {
  const statusLabel = {
    live: "EN JUEGO",
    scheduled: "PROGRAMADO",
    finished: "FINALIZADO",
    suspended: "SUSPENDIDO",
    postponed: "APLAZADO",
    cancelled: "CANCELADO",
  }[m.status] || m.status.toUpperCase();

  const hasScore = m.home_score !== null && m.home_score !== undefined;
  const scoreBlock = hasScore
    ? `<div class="fx-score"><span>${m.home_score}</span><span class="fx-score-sep">–</span><span>${m.away_score}</span></div>`
    : `<div class="fx-meta"><span>${m.utc_date ? new Date(m.utc_date).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }) : "—"}</span></div>`;

  const minuteBadge = m.status === "live" && m.minute ? `<span class="live-minute">${m.minute}'</span>` : "";

  return `
  <div class="fx-card">
    <div class="fx-row">
      <span class="live-match-status live-match-status--${escHtml(m.status)}">${statusLabel}</span>
      ${minuteBadge}
    </div>
    <div class="fx-row fx-main">
      <div class="fx-teams">
        <span class="fx-team">${typeof entityMedia === "function" ? entityMedia("team", m.home) : ""}<b>${escHtml(typeof teamDisplayName === "function" ? teamDisplayName(m.home) : m.home)}</b></span>
        <span class="fx-vs">vs</span>
        <span class="fx-team">${typeof entityMedia === "function" ? entityMedia("team", m.away) : ""}<b>${escHtml(typeof teamDisplayName === "function" ? teamDisplayName(m.away) : m.away)}</b></span>
      </div>
      ${scoreBlock}
    </div>
  </div>`;
}

// Sin partidos hoy: últimos resultados registrados + próximos partidos, para
// que la pestaña no quede vacía (fuente: fixtures.json, no el feed en directo).
function buildLiveFallback() {
  const fx = APP.fixtures || {};
  const seen = new Set();
  const finished = [...(fx.recent || []), ...(fx.calendar || [])].filter(f => {
    if (f.status !== "finished" || f.home_score == null) return false;
    const key = `${f.date}|${f.home}|${f.away}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).sort((a, b) => String(b.date).localeCompare(String(a.date)) || String(b.time || "").localeCompare(String(a.time || "")));
  const lastDates = [...new Set(finished.map(f => f.date))].slice(0, 2);
  const results = finished.filter(f => lastDates.includes(f.date)).slice(0, 18);

  const today = new Date().toISOString().slice(0, 10);
  const upcoming = (fx.upcoming || []).filter(f => f.date >= today && f.status !== "finished");
  const nextDates = [...new Set(upcoming.map(f => f.date))].slice(0, 2);
  const next = upcoming.filter(f => nextDates.includes(f.date)).slice(0, 18);

  const dayLabel = d => new Date(`${d}T12:00:00`).toLocaleDateString("es-ES", { weekday: "short", day: "numeric", month: "short" });
  const name = t => escHtml(typeof teamDisplayName === "function" ? teamDisplayName(t) : t);
  const crest = t => typeof entityMedia === "function" ? entityMedia("team", t) : "";
  const href = f => typeof buildMatchHref === "function" ? buildMatchHref(f) : "#";

  const resultCard = f => {
    const hw = f.home_score > f.away_score, aw = f.away_score > f.home_score;
    return `
    <a class="live-mini" href="${href(f)}">
      <span class="lm-team ${hw ? "win" : aw ? "lose" : ""}">${crest(f.home)}<span>${name(f.home)}</span></span>
      <span class="lm-score">${f.home_score}</span>
      <span class="lm-team ${aw ? "win" : hw ? "lose" : ""}">${crest(f.away)}<span>${name(f.away)}</span></span>
      <span class="lm-score">${f.away_score}</span>
      <span class="lm-meta">${escHtml(APP.leagues?.[f.league]?.name || f.league_name || f.league)} · ${dayLabel(f.date)}</span>
    </a>`;
  };
  const nextCard = f => `
    <a class="live-mini" href="${href(f)}">
      <span class="lm-team">${crest(f.home)}<span>${name(f.home)}</span></span>
      <span class="lm-score muted" style="font-size:.74rem;">${escHtml(f.time || "por confirmar")}</span>
      <span class="lm-team">${crest(f.away)}<span>${name(f.away)}</span></span>
      <span></span>
      <span class="lm-meta">${escHtml(APP.leagues?.[f.league]?.name || f.league_name || f.league)} · ${dayLabel(f.date)}</span>
    </a>`;

  return `
    ${next.length ? `<div class="live-fallback-title">Próximos partidos <small>${nextDates.map(dayLabel).join(" · ")}</small></div>
      <div class="live-grid">${next.map(nextCard).join("")}</div>` : ""}
    ${results.length ? `<div class="live-fallback-title">Últimos resultados registrados <small>${lastDates.map(dayLabel).join(" · ")}</small></div>
      <div class="live-grid">${results.map(resultCard).join("")}</div>` : ""}`;
}
