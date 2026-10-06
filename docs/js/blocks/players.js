/**
 * blocks/players.js — Comparativa de jugadores (Comparador y ficha de partido).
 * Accede a los jugadores vía _blkPlayers() — funciona en APP y state.
 *
 * buildBlockPlayers(homeTeam, awayTeam, ctx)
 *
 * Dos vistas:
 *   - Faltas y tarjetas: faltas cometidas / recibidas / amarillas por partido en
 *     la ventana elegida (temporada, últimos 5/10/15) y frecuencias "≥N en n/N"
 *     a partir de players.json → seq (últimos 15 partidos, más reciente primero).
 *   - Ataque: tiros, tiros a puerta, goles, asistencias (media de temporada).
 * Interactivo por delegación de eventos: el bloque se re-renderiza en su sitio.
 */
"use strict";

const PBLK_STATE = { view: "fouls", win: 10, thr: 2 };
const PBLK_WINDOWS = [["season", "Temporada"], [5, "Últ. 5"], [10, "Últ. 10"], [15, "Últ. 15"]];
let _pblkBound = false;

function buildBlockPlayers(homeTeam, awayTeam, ctx) {
  _pblkBind();
  return `<div class="pblk" data-home="${_blkEsc(homeTeam)}" data-away="${_blkEsc(awayTeam)}">${_pblkInner(homeTeam, awayTeam)}</div>`;
}

function _pblkBind() {
  if (_pblkBound) return;
  _pblkBound = true;
  document.addEventListener("click", e => {
    const btn = e.target.closest("[data-pblk]");
    if (!btn) return;
    const box = btn.closest(".pblk");
    if (!box) return;
    const [key, raw] = btn.dataset.pblk.split(":");
    PBLK_STATE[key] = key === "view" ? raw : (raw === "season" ? "season" : Number(raw));
    // Todas las instancias en pantalla comparten estado (ficha + comparador).
    document.querySelectorAll(".pblk").forEach(el => {
      el.innerHTML = _pblkInner(el.dataset.home, el.dataset.away);
      if (typeof initAllTables === "function") initAllTables(el);
    });
  });
}

function _pblkInner(homeTeam, awayTeam) {
  const all = _blkPlayers();
  // Clubes sin liga doméstica cubierta (Porto, Galatasaray…): sus partidos de Champions.
  const cl = (typeof APP !== "undefined" && APP.playersCL) || (typeof state !== "undefined" && state.playersCL) || {};
  const pick = t => ((all[t] || []).length ? all[t] : (cl[t] || []));
  const home = pick(homeTeam);
  const away = pick(awayTeam);
  if (!home.length && !away.length) {
    return `
      <div class="blk-empty">
        <p class="muted">Sin datos de jugadores para estos equipos.</p>
        <p class="muted" style="font-size:.8rem;">Aún no tienen partidos con estadísticas de jugador esta temporada.
        Consulta <a href="coverage.html" style="color:var(--brand)">cobertura de datos</a>.</p>
      </div>`;
  }
  const s = PBLK_STATE;
  const toggle = (key, value, label) =>
    `<button type="button" class="ktoggle" data-pblk="${key}:${value}" aria-pressed="${String(s[key]) === String(value)}">${label}</button>`;
  const fouls = s.view === "fouls";
  const toolbar = `
    <div class="pblk-toolbar">
      <div class="pblk-group">${toggle("view", "fouls", "Faltas y tarjetas")}${toggle("view", "attack", "Ataque")}</div>
      ${fouls ? `
      <div class="pblk-group"><span class="pblk-lbl">Ventana</span>${PBLK_WINDOWS.map(([v, l]) => toggle("win", v, l)).join("")}</div>
      <div class="pblk-group"><span class="pblk-lbl">Frecuencia</span>${[1, 2, 3].map(n => toggle("thr", n, `${n}+`)).join("")}</div>` : ""}
    </div>`;

  const note = fouls
    ? `<p class="match-note">${s.win === "season"
        ? "Medias por partido de toda la temporada; la frecuencia se calcula sobre sus últimos partidos registrados (hasta 15)."
        : `Medias de los últimos ${s.win} partidos de cada jugador (o los que haya jugado).`}
       <b>Com.</b> = faltas cometidas · <b>Rec.</b> = faltas recibidas · <b>${s.thr}+ com./rec.</b> = partidos con ${s.thr} o más (n/N).</p>`
    : `<p class="match-note">Medias por partido jugado esta temporada.</p>`;

  const table = fouls ? _pblkFoulsTable : _pblkAttackTable;
  return `${toolbar}${note}
    <div class="players-comparison">
      ${table(homeTeam, home)}
      ${table(awayTeam, away)}
    </div>`;
}

// ── Faltas y tarjetas ─────────────────────────────────────────────────────

function _pblkWindowStats(p) {
  const s = PBLK_STATE;
  const seq = p.seq || {};
  const n = s.win === "season" ? (seq.fls || []).length : Math.min(s.win, (seq.fls || []).length);
  const take = k => (seq[k] || []).slice(0, n);
  const avg = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
  const hits = arr => arr.length ? { hit: arr.filter(v => v >= s.thr).length, of: arr.length } : null;
  if (s.win === "season") {
    return {
      mp: p.mp ?? n, min: p.min, fls: p.fls, fld: p.fld, crdy: p.crdy,
      comHits: hits(take("fls")), recHits: hits(take("fld")),
    };
  }
  if (!n) return null;
  return {
    mp: n, min: avg(take("min")), fls: avg(take("fls")), fld: avg(take("fld")), crdy: avg(take("crdy")),
    comHits: hits(take("fls")), recHits: hits(take("fld")),
  };
}

function _pblkFoulsTable(team, players) {
  const label = typeof teamDisplayName === "function" ? teamDisplayName(team) : team;
  const rows = players
    .map(p => ({ p, w: _pblkWindowStats(p) }))
    .filter(x => x.w && (x.w.min || 0) >= 20 && (x.w.mp || 0) >= Math.min(2, PBLK_STATE.win === "season" ? 2 : PBLK_STATE.win))
    .sort((a, b) => (b.w.fls || 0) + (b.w.fld || 0) * 0.01 - ((a.w.fls || 0) + (a.w.fld || 0) * 0.01))
    .slice(0, 12);
  if (!rows.length) return _pblkEmpty(label);

  const rank = k => typeof kdxRanker === "function" ? kdxRanker(rows.map(x => x.w[k])) : () => null;
  const rFls = rank("fls"), rFld = rank("fld"), rTa = rank("crdy");
  const heat = (r, v, tone) => typeof kdxHeatClass === "function" ? kdxHeatClass(r(v), tone) : "";
  // Cometidas: frecuencia alta = riesgo (rojo). Recibidas: frecuencia alta = verde.
  const hitCell = (h, tone = "risk") => {
    if (!h) return `<td class="ctr muted" data-sort="-1">—</td>`;
    const rate = h.hit / h.of;
    const cls = tone === "risk"
      ? (rate >= 0.7 ? "heat-risk-4" : rate >= 0.5 ? "heat-risk-3" : rate <= 0.15 ? "heat-risk-0" : "")
      : (rate >= 0.7 ? "heat-good-4" : rate >= 0.5 ? "heat-good-3" : "");
    return `<td class="ctr ${cls}" data-sort="${rate.toFixed(3)}" title="${Math.round(rate * 100)}%">${h.hit}/${h.of}</td>`;
  };

  const body = rows.map(({ p, w }) => `
    <tr>
      <td><span class="player-cell">${typeof entityMedia === "function" ? entityMedia("player", p.player, team) : ""}<b>${_blkEsc(p.player)}</b></span></td>
      <td class="num muted" data-sort="${w.mp}">${w.mp}</td>
      <td class="num ${heat(rFls, w.fls, "risk")}" data-sort="${w.fls ?? -1}">${_blkFmt(w.fls, 1)}</td>
      <td class="num ${heat(rFld, w.fld, "good")}" data-sort="${w.fld ?? -1}">${_blkFmt(w.fld, 1)}</td>
      ${hitCell(w.comHits)}
      ${hitCell(w.recHits, "good")}
      <td class="num ${heat(rTa, w.crdy, "risk")}" data-sort="${w.crdy ?? -1}">${_blkFmt(w.crdy, 2)}</td>
    </tr>`).join("");

  const thr = PBLK_STATE.thr;
  return `
    <div class="players-team-panel">
      <div class="players-col-title">${_blkEsc(label)}</div>
      <div class="table-wrap players-table-wrap" style="overflow-x:auto;max-height:460px;overflow-y:auto;">
        <table class="ktable">
          <thead><tr>
            <th>Jugador</th>
            <th class="num" title="Partidos en la ventana">PJ</th>
            <th class="num" title="Faltas cometidas por partido">Com./p</th>
            <th class="num" title="Faltas recibidas por partido">Rec./p</th>
            <th class="ctr" title="Partidos con ${thr} o más faltas cometidas">${thr}+ com.</th>
            <th class="ctr" title="Partidos con ${thr} o más faltas recibidas">${thr}+ rec.</th>
            <th class="num" title="Amarillas por partido">TA/p</th>
          </tr></thead>
          <tbody>${body}</tbody>
        </table>
      </div>
    </div>`;
}

// ── Ataque ────────────────────────────────────────────────────────────────

function _pblkAttackTable(team, players) {
  const label = typeof teamDisplayName === "function" ? teamDisplayName(team) : team;
  const top = players.slice()
    .filter(p => (p.min || 0) >= 20)
    .sort((a, b) => ((b.gls || 0) * 3 + (b.sot || 0) + (b.sh || 0) * 0.25) - ((a.gls || 0) * 3 + (a.sot || 0) + (a.sh || 0) * 0.25))
    .slice(0, 10);
  if (!top.length) return _pblkEmpty(label);
  const body = top.map(p => `
    <tr>
      <td><span class="player-cell">${typeof entityMedia === "function" ? entityMedia("player", p.player, team) : ""}<b>${_blkEsc(p.player)}</b></span></td>
      <td class="num muted">${p.mp ?? "—"}</td>
      <td class="num">${_blkFmt(p.sh, 1)}</td>
      <td class="num">${_blkFmt(p.sot, 1)}</td>
      <td class="num">${p.gls_tot ?? _blkFmt(p.gls, 2)}</td>
      <td class="num">${p.ast_tot ?? _blkFmt(p.ast, 2)}</td>
      <td class="num">${p.crdy != null ? _blkFmt(p.crdy, 2) : "—"}</td>
    </tr>`).join("");
  return `
    <div class="players-team-panel">
      <div class="players-col-title">${_blkEsc(label)}</div>
      <div class="table-wrap players-table-wrap" style="overflow-x:auto;max-height:460px;overflow-y:auto;">
        <table class="ktable">
          <thead><tr><th>Jugador</th><th class="num" title="Partidos jugados">PJ</th><th class="num" title="Tiros por partido">Tiros/p</th>
            <th class="num" title="Tiros a puerta por partido">SoT/p</th><th class="num" title="Goles (temporada)">Goles</th>
            <th class="num" title="Asistencias (temporada)">Asist.</th><th class="num" title="Amarillas por partido">TA/p</th></tr></thead>
          <tbody>${body}</tbody>
        </table>
      </div>
    </div>`;
}

function _pblkEmpty(label) {
  return `
    <div class="players-team-panel">
      <div class="players-col-title">${_blkEsc(label)}</div>
      <p class="muted">Sin jugadores con minutos suficientes en esta ventana.</p>
    </div>`;
}
