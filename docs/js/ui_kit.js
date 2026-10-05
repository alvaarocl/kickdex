/**
 * ui_kit.js - helpers visuales compartidos por las tablas (index, match,
 * referee). Globals sin import/export, sin dependencias de APP.
 *
 * - Escala de calor por columna: cada celda se colorea según su percentil
 *   dentro de la columna visible (no por umbrales fijos), así una liga con
 *   pocas tarjetas no sale toda "verde".
 * - Tono "risk": alto = rojo (tarjetas, faltas). Tono "good": alto = verde
 *   de marca (goles, puntos).
 */

"use strict";

// Devuelve una función v -> percentil 0..1 dentro de `values` (null si no hay muestra).
function kdxRanker(values) {
  const sorted = (values || []).map(Number).filter(Number.isFinite).sort((a, b) => a - b);
  return value => {
    const v = Number(value);
    if (sorted.length < 3 || !Number.isFinite(v)) return null;
    let below = 0, equal = 0;
    for (const x of sorted) {
      if (x < v) below++;
      else if (x === v) equal++;
    }
    return (below + equal / 2) / sorted.length;
  };
}

// Percentil -> clase CSS heat-{tone}-{0..4}.
function kdxHeatClass(pct, tone = "risk") {
  if (pct == null) return "";
  const level = pct >= 0.9 ? 4 : pct >= 0.7 ? 3 : pct >= 0.3 ? 2 : pct >= 0.1 ? 1 : 0;
  return `heat-${tone}-${level}`;
}

// Barra horizontal mini (0..max).
function kdxBar(value, max, tone = "brand") {
  const v = Number(value);
  const m = Number(max);
  const w = Number.isFinite(v) && m > 0 ? Math.max(3, Math.min(100, (v / m) * 100)) : 0;
  return `<span class="kbar kbar--${tone}" aria-hidden="true"><i style="width:${w.toFixed(1)}%"></i></span>`;
}

// Diferencia con signo, coloreada (positivo = más tarjetas = "hot").
function kdxDiff(value, dec = 2, positiveIsHot = true) {
  const n = Number(value);
  if (!Number.isFinite(n)) return `<span class="kdiff">—</span>`;
  const cls = Math.abs(n) < 0.005 ? "" : (n > 0) === positiveIsHot ? "kdiff--hot" : "kdiff--cold";
  return `<span class="kdiff ${cls}">${n > 0 ? "+" : ""}${n.toFixed(dec)}</span>`;
}

// Pastillas de forma V/E/D. `results` = ["W","D","L",...] del más antiguo al más reciente.
function kdxFormPills(results, titles) {
  const map = { W: ["V", "w"], D: ["E", "d"], L: ["D", "l"] };
  if (!results || !results.length) return `<span class="kform kform--empty">—</span>`;
  return `<span class="kform">${results.map((r, i) => {
    const [label, cls] = map[r] || ["·", "n"];
    const title = titles?.[i] ? ` title="${String(titles[i]).replace(/"/g, "&quot;")}"` : "";
    return `<i class="kform-pill kform-pill--${cls}"${title}>${label}</i>`;
  }).join("")}</span>`;
}

// Pastilla de tarjetas de un partido (amarillas + rojas) coloreada vs la media.
function kdxCardPill(yellows, reds, avg) {
  const y = Number(yellows);
  if (!Number.isFinite(y)) return `<i class="kcard kcard--na">·</i>`;
  const r = Number(reds) || 0;
  const ref = Number(avg);
  let cls = "mid";
  if (Number.isFinite(ref) && ref > 0) {
    if (y >= ref * 1.3 || r > 0) cls = "hot";
    else if (y >= ref * 1.05) cls = "warm";
    else if (y <= ref * 0.7) cls = "cold";
  }
  return `<i class="kcard kcard--${cls}" title="${y} amarillas${r ? ` · ${r} roja${r > 1 ? "s" : ""}` : ""}">${y}${r ? `<b>${r}</b>` : ""}</i>`;
}

// Racha de un equipo desde fixtures (calendar/recent) → ["W","L",...] últimos n.
function kdxTeamForm(fixtureLists, team, n = 5) {
  const seen = new Set();
  const games = [];
  (fixtureLists || []).forEach(list => (list || []).forEach(f => {
    if (f.status !== "finished" || f.home_score == null || f.away_score == null) return;
    if (f.home !== team && f.away !== team) return;
    const key = `${f.date}|${f.home}|${f.away}`;
    if (seen.has(key)) return;
    seen.add(key);
    games.push(f);
  }));
  games.sort((a, b) => String(a.date).localeCompare(String(b.date)));
  return games.slice(-n).map(f => {
    const isHome = f.home === team;
    const gf = isHome ? f.home_score : f.away_score;
    const ga = isHome ? f.away_score : f.home_score;
    const res = gf > ga ? "W" : gf < ga ? "L" : "D";
    const rival = isHome ? f.away : f.home;
    return { res, title: `${f.date} · ${isHome ? "vs" : "en"} ${rival} ${gf}-${ga}` };
  });
}
