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
    </div>`;
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
