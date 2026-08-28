/**
 * blocks/shared.js — Utilidades compartidas por todos los bloques de análisis.
 * Debe cargarse ANTES de cualquier blocks/*.js.
 * No depende de APP ni de state: funciona en index.html y match.html.
 */
"use strict";

/* ── Escape HTML ──────────────────────────────────────────────────── */
function _blkEsc(v) {
  return String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ── Formatters (delegan a los globals de app.js/match.js si existen) ── */
function _blkFmt(v, d) {
  if (d === undefined) d = 2;
  if (typeof fmt === "function") return fmt(v, d);
  if (v == null || (typeof v === "number" && isNaN(v))) return "—";
  return Number(v).toFixed(d);
}

function _blkPct(v, d) {
  if (d === undefined) d = 0;
  if (typeof pct === "function") return pct(v, d);
  if (v == null || (typeof v === "number" && isNaN(v))) return "—";
  return (Number(v) * 100).toFixed(d) + "%";
}

/* ── Venue stats resolver ─────────────────────────────────────────── */
/**
 * Devuelve los stats del objeto team_stats para la localía pedida.
 * venue: 'home' | 'away' | 'all'
 * Para 'all': promedia campos numéricos y mezcla match_log por fecha desc.
 */
function _blkGetVenueStats(teamData, venue) {
  if (!teamData) return {};
  if (venue === "all") {
    const h = teamData.home || {};
    const a = teamData.away || {};
    const numKeys = [
      "avg_goals", "avg_goals_against", "avg_shots", "avg_shots_on",
      "avg_corners", "avg_cards", "avg_fouls", "avg_xg_proxy",
      "win_rate", "draw_rate", "loss_rate",
      "over25_rate", "btts_rate", "clean_sheet_rate", "effective_matches",
    ];
    const merged = {};
    for (const k of numKeys) {
      const hv = h[k]; const av = a[k];
      if (typeof hv === "number" && typeof av === "number") {
        merged[k] = (hv + av) / 2;
      } else if (typeof hv === "number") {
        merged[k] = hv;
      } else if (typeof av === "number") {
        merged[k] = av;
      }
    }
    merged.matches_analyzed = (h.matches_analyzed || 0) + (a.matches_analyzed || 0);
    // Interleave match_log by date desc
    const hLog = (h.match_log || []).map(m => Object.assign({}, m, { _venue: "home" }));
    const aLog = (a.match_log || []).map(m => Object.assign({}, m, { _venue: "away" }));
    merged.match_log = [...hLog, ...aLog]
      .sort((x, y) => (y.date || "").localeCompare(x.date || ""))
      .slice(0, 10);
    return merged;
  }
  return teamData[venue] || {};
}

/* ── H2H lookup ───────────────────────────────────────────────────── */
function _blkGetH2H(a, b, h2h) {
  if (!h2h) return null;
  return h2h[a + "|" + b] || h2h[b + "|" + a] || null;
}

/* ── Global data accessors (index.html → APP, match.html → state) ── */
function _blkPlayers() {
  if (typeof APP !== "undefined" && APP.players) return APP.players;
  if (typeof state !== "undefined" && state.players) return state.players;
  return {};
}

/* ── Venue display label ──────────────────────────────────────────── */
function _blkVenueLabel(venue) {
  if (venue === "home") return "en casa";
  if (venue === "away") return "fuera";
  return "todos";
}
