/**
 * live.js - Tab "Directo": marcadores en vivo.
 *
 * Fuente principal: marcador público de ESPN, consultado DIRECTAMENTE desde el
 * navegador (CORS abierto, caché de ~3 s en su CDN). Retraso típico < 1 min.
 * Es una API pública no oficial: si falla o cambia, se cae al JSON con
 * retraso que genera el workflow (docs/data/live_scores.json).
 *
 * Por qué no GitHub Actions: aunque el cron diga "cada 15 min", GitHub lo
 * ejecutaba cada 4-7 h en la práctica (oct-2026), inservible para un directo.
 *
 * Cadencia adaptativa (solo con la pestaña Directo abierta y visible):
 *   partido en juego → 30 s · partidos más tarde hoy → 2 min · nada → 10 min.
 */

"use strict";

const ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={date}";
const ESPN_SLUGS = {
  SP1: "esp.1", SP2: "esp.2", E0: "eng.1", E1: "eng.2", I1: "ita.1", I2: "ita.2",
  D1: "ger.1", D2: "ger.2", F1: "fra.1", F2: "fra.2", N1: "ned.1",
};
const LIVE_MS = { live: 30000, today: 120000, idle: 600000 };

let _liveTimer = null;
let _liveScores = {};      // id -> "h-a" del refresco anterior (para el destello)
let _liveFetching = false;
let _liveTeamIndex = null;

function initLive() {
  refreshLive();
  document.addEventListener("kdx:tab-open", e => {
    if (e.detail?.tab === "live") refreshLive();
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && liveTabActive()) refreshLive();
  });
}

function liveTabActive() {
  return document.getElementById("tab-live")?.classList.contains("active");
}

function scheduleLive(ms) {
  clearTimeout(_liveTimer);
  _liveTimer = setTimeout(() => {
    if (document.hidden || !liveTabActive()) return; // se reanuda al volver
    refreshLive();
  }, ms);
}

function todayStamp() {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

async function fetchWithTimeout(url, ms = 9000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(url, { signal: ctrl.signal, cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

async function refreshLive() {
  if (_liveFetching) return;
  _liveFetching = true;
  try {
    // ?livedate=YYYYMMDD permite revisar un día concreto (pruebas).
    const date = new URLSearchParams(location.search).get("livedate") || todayStamp();
    const codes = Object.keys(ESPN_SLUGS);
    const settled = await Promise.allSettled(codes.map(code =>
      fetchWithTimeout(ESPN_SCOREBOARD.replace("{slug}", ESPN_SLUGS[code]).replace("{date}", date))
        .then(data => ({ code, data }))));
    const ok = settled.filter(r => r.status === "fulfilled").map(r => r.value);
    if (!ok.length) throw new Error("ESPN no disponible");

    const matches = [];
    ok.forEach(({ code, data }) => (data.events || []).forEach(ev => {
      const m = normalizeEspnEvent(ev, code);
      if (m) matches.push(m);
    }));
    renderLiveEspn(matches, settled.length - ok.length);

    const now = Date.now();
    const anyLive = matches.some(m => m.state === "in");
    const laterToday = matches.some(m => m.state === "pre" && m.kickoff - now < 6 * 3600 * 1000);
    scheduleLive(anyLive ? LIVE_MS.live : laterToday ? LIVE_MS.today : LIVE_MS.idle);
  } catch (err) {
    console.warn("Directo ESPN falló, usando JSON con retraso:", err);
    await fetchLiveScoresFallback();
    scheduleLive(LIVE_MS.today);
  } finally {
    _liveFetching = false;
  }
}

// ── Normalización ESPN → contrato interno ─────────────────────────────────

function normalizeEspnEvent(ev, league) {
  const comp = ev.competitions?.[0];
  if (!comp) return null;
  const home = comp.competitors?.find(c => c.homeAway === "home");
  const away = comp.competitors?.find(c => c.homeAway === "away");
  if (!home || !away) return null;
  const status = ev.status || comp.status || {};
  const type = status.type || {};
  const side = teamId => (String(teamId) === String(home.team?.id) ? "home" : "away");

  const events = (comp.details || []).map(d => {
    const kind = d.scoringPlay ? "goal" : d.redCard ? "red" : d.yellowCard ? "yellow"
      : /red/i.test(d.type?.text || "") ? "red" : /yellow/i.test(d.type?.text || "") ? "yellow" : null;
    if (!kind) return null;
    return {
      kind,
      side: side(d.team?.id),
      minute: d.clock?.displayValue || "",
      player: d.athletesInvolved?.[0]?.displayName || d.athletesInvolved?.[0]?.shortName || "",
      own: !!d.ownGoal,
      pen: !!d.penaltyKick,
    };
  }).filter(Boolean);

  return {
    id: ev.id,
    league,
    kickoff: Date.parse(ev.date),
    state: type.state || "pre",               // pre | in | post
    statusName: type.name || "",
    detail: type.shortDetail || type.detail || "",
    clock: status.displayClock || "",
    home: {
      name: home.team?.displayName || home.team?.name || "",
      logo: home.team?.logo || "",
      score: home.score != null ? Number(home.score) : null,
      key: matchTeamKey(league, home.team),
    },
    away: {
      name: away.team?.displayName || away.team?.name || "",
      logo: away.team?.logo || "",
      score: away.score != null ? Number(away.score) : null,
      key: matchTeamKey(league, away.team),
    },
    events,
  };
}

// ESPN usa "Atlético Madrid"; el dataset, "Ath Madrid" (estilo football-data).
// Se cruza contra el nombre canónico y el nombre visible de cada equipo de la liga.
const LIVE_NOISE = new Set(["fc", "cf", "afc", "sc", "cd", "ud", "sd", "rc", "rcd", "club", "de", "del", "la", "el",
  "the", "ac", "as", "ss", "us", "sv", "vfb", "vfl", "tsg", "1", "fk", "calcio", "city", "town"]);

function liveTokens(s) {
  return String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(t => t && !LIVE_NOISE.has(t));
}

function buildTeamIndex() {
  const idx = {};
  Object.entries(APP.leagues || {}).forEach(([code, info]) => {
    idx[code] = (info.teams || []).map(key => ({
      key,
      variants: [key, typeof teamDisplayName === "function" ? teamDisplayName(key) : key].map(liveTokens),
    }));
  });
  return idx;
}

function matchTeamKey(league, team) {
  if (!team) return null;
  _liveTeamIndex = _liveTeamIndex || buildTeamIndex();
  const candidates = _liveTeamIndex[league] || [];
  const names = [team.displayName, team.shortDisplayName, team.name, team.location].filter(Boolean).map(liveTokens);
  let best = null, bestScore = 0;
  candidates.forEach(c => c.variants.forEach(v => names.forEach(n => {
    if (!v.length || !n.length) return;
    const joinedV = v.join(" "), joinedN = n.join(" ");
    let score;
    if (joinedV === joinedN) score = 1;
    else {
      const inter = v.filter(t => n.includes(t)).length;
      score = inter / Math.max(v.length, n.length);
      // "Man United" vs "Manchester United": prefijos de 3+ letras cuentan
      if (score < 1) {
        const fuzzy = v.filter(t => n.some(u => t.length >= 3 && u.length >= 3 && (u.startsWith(t) || t.startsWith(u)))).length;
        score = Math.max(score, 0.9 * fuzzy / Math.max(v.length, n.length));
      }
    }
    if (score > bestScore) { bestScore = score; best = c.key; }
  })));
  return bestScore >= 0.5 ? best : null;
}

// ── Render ────────────────────────────────────────────────────────────────

function renderLiveEspn(matches, failedLeagues) {
  const chip = document.getElementById("liveStatusChip");
  const status = document.getElementById("liveDataStatus");
  const root = document.getElementById("live-root");
  if (!root) return;

  const live = matches.filter(m => m.state === "in").sort(byKickoff);
  const pre = matches.filter(m => m.state === "pre").sort(byKickoff);
  const post = matches.filter(m => m.state === "post").sort((a, b) => b.kickoff - a.kickoff);

  updateLiveBadge(live.length);
  if (chip) {
    chip.textContent = live.length ? `● EN DIRECTO · ${live.length}` : "DIRECTO";
    chip.classList.toggle("live-status-chip--on", live.length > 0);
  }
  if (status) {
    const t = new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    status.textContent = `Marcadores casi en tiempo real (retraso típico < 1 min) · fuente: ESPN, datos públicos no oficiales · actualizado ${t}`
      + (live.length ? " · se refresca cada 30 s" : "")
      + (failedLeagues ? ` · ${failedLeagues} liga(s) sin respuesta` : "");
  }

  if (!matches.length) {
    root.innerHTML = `<div class="fx-empty">Hoy no hay partidos en las ligas cubiertas.</div>${buildLiveFallback()}`;
    return;
  }

  const section = (title, list, note) => list.length ? `
    <div class="live-fallback-title">${title} <small>${note || list.length}</small></div>
    <div class="live-grid">${list.map(liveEspnCard).join("")}</div>` : "";

  root.innerHTML =
    section("En juego", live) +
    section("Hoy, más tarde", pre) +
    section("Finalizados hoy", post) +
    (live.length || pre.length ? "" : buildLiveFallback());

  // Destello en los marcadores que han cambiado desde el último refresco.
  matches.forEach(m => {
    const score = `${m.home.score}-${m.away.score}`;
    if (_liveScores[m.id] && _liveScores[m.id] !== score) {
      document.querySelector(`[data-live-id="${m.id}"]`)?.classList.add("live-card--flash");
    }
    _liveScores[m.id] = score;
  });
}

function byKickoff(a, b) { return a.kickoff - b.kickoff; }

function updateLiveBadge(n) {
  const btn = document.querySelector('.tab-btn[data-tab="live"]');
  if (!btn) return;
  let badge = btn.querySelector(".live-count");
  if (!n) { badge?.remove(); return; }
  if (!badge) {
    badge = document.createElement("span");
    badge.className = "live-count";
    btn.appendChild(badge);
  }
  badge.textContent = n;
}

function liveStatusLabel(m) {
  if (m.state === "in") {
    if (/HALF/i.test(m.statusName)) return { text: "DESCANSO", cls: "ht" };
    return { text: m.clock || m.detail || "EN JUEGO", cls: "live" };
  }
  if (m.state === "post") {
    if (/POSTPON/i.test(m.statusName)) return { text: "APLAZADO", cls: "off" };
    if (/CANCEL|ABANDON/i.test(m.statusName)) return { text: "SUSPENDIDO", cls: "off" };
    return { text: "FINAL", cls: "ft" };
  }
  const time = Number.isFinite(m.kickoff)
    ? new Date(m.kickoff).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })
    : "—";
  return { text: time, cls: "pre" };
}

function liveTeamCrest(team) {
  if (team.key && typeof entityMedia === "function") return entityMedia("team", team.key);
  if (team.logo) return `<span class="entity-media entity-media--team"><img src="${escHtml(team.logo)}" alt="" loading="lazy"></span>`;
  return `<span class="entity-media entity-media--team">${escHtml((team.name || "?").slice(0, 2).toUpperCase())}</span>`;
}

function liveTeamName(team) {
  return team.key && typeof teamDisplayName === "function" ? teamDisplayName(team.key) : team.name;
}

function liveEspnCard(m) {
  const st = liveStatusLabel(m);
  const showScore = m.state !== "pre" && m.home.score != null;
  const hs = m.home.score, as = m.away.score;
  const winH = showScore && m.state === "post" && hs > as, winA = showScore && m.state === "post" && as > hs;
  const goals = side => m.events.filter(e => (e.kind === "goal" && e.side === side) || (e.kind === "red" && e.side === side));
  const evHtml = side => goals(side).map(e =>
    `<span class="lm-ev lm-ev--${e.kind}">${e.kind === "goal" ? "⚽" : "🟥"} ${escHtml(e.minute)} ${escHtml(e.player)}${e.pen ? " (p)" : ""}${e.own ? " (pp)" : ""}</span>`).join("");
  const yellows = side => m.events.filter(e => e.kind === "yellow" && e.side === side).length;
  const anyCards = m.events.some(e => e.kind === "yellow" || e.kind === "red");
  const href = m.home.key && m.away.key && typeof buildMatchHref === "function"
    ? buildMatchHref({ league: m.league, date: new Date(m.kickoff).toISOString().slice(0, 10), home: m.home.key, away: m.away.key })
    : null;
  const tag = href ? "a" : "div";

  return `
  <${tag} class="live-mini live-card live-card--${st.cls}" data-live-id="${escHtml(m.id)}"${href ? ` href="${href}"` : ""}>
    <span class="lm-meta">${escHtml(APP.leagues?.[m.league]?.name || m.league)}</span>
    <span class="live-badge live-badge--${st.cls}">${escHtml(st.text)}</span>
    <span class="lm-team ${winH ? "win" : winA ? "lose" : ""}">${liveTeamCrest(m.home)}<span>${escHtml(liveTeamName(m.home))}</span></span>
    <span class="lm-score">${showScore ? hs : ""}</span>
    ${goals("home").length ? `<span class="lm-events">${evHtml("home")}</span>` : ""}
    <span class="lm-team ${winA ? "win" : winH ? "lose" : ""}">${liveTeamCrest(m.away)}<span>${escHtml(liveTeamName(m.away))}</span></span>
    <span class="lm-score">${showScore ? as : ""}</span>
    ${goals("away").length ? `<span class="lm-events">${evHtml("away")}</span>` : ""}
    ${anyCards ? `<span class="lm-cards">🟨 ${yellows("home")} – ${yellows("away")}</span>` : ""}
  </${tag}>`;
}

// ── Respaldo: JSON con retraso del workflow ───────────────────────────────

async function fetchLiveScoresFallback() {
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
    chip.classList.toggle("live-status-chip--on", false);
  }
  if (status) {
    status.textContent = enabled
      ? `La fuente en vivo no responde; mostrando la copia con retraso (puede ser de hace horas). ${updated ? "· Actualizado " + updated : ""}`
      : (data?.note || "Directo no disponible ahora mismo.");
  }

  const matches = enabled ? (data.matches || []) : [];
  if (!matches.length) {
    root.innerHTML = `
    <div class="fx-empty">
      Sin marcadores disponibles ahora mismo.
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
  }[m.status] || String(m.status || "").toUpperCase();

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
// que la pestaña no quede vacía (fuente: fixtures.json).
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
  const upcoming = (fx.upcoming || []).filter(f => f.date > today && f.status !== "finished");
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
