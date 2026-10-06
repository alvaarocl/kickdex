/**
 * discipline_ui.js - piezas visuales compartidas de apercibidos/sancionados
 * (apercibidos.html y ficha de partido). Globals, sin dependencias de APP.
 *
 * Contrato: suspensions.json → items[] con status "suspended" | "at_risk",
 * cards, threshold, reason, ban_matches, remaining, min_only, misses[], next,
 * rule, confidence, source ("calculated" u oficial), official, source_url.
 */

"use strict";

function discEsc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function discTeamName(team) {
  return typeof teamDisplayName === "function" ? teamDisplayName(team) : team;
}

function discMedia(kind, name, team) {
  return window.KDXEntities?.media(kind, name, team) || "";
}

function discDate(date, time) {
  if (!date) return "";
  const d = new Date(`${date}T12:00:00`);
  const label = d.toLocaleDateString("es-ES", { weekday: "short", day: "numeric", month: "short" });
  return time ? `${label} · ${time}` : label;
}

// Amarillas como pastillas: llenas hasta `cards`, vacías hasta el umbral.
function discCardPips(cards, threshold) {
  const c = Number(cards) || 0;
  const t = Number(threshold) || 0;
  if (!t) return `<span class="disc-count">${c} TA</span>`;
  const shown = Math.min(t, 10);
  const filled = Math.min(c - Math.max(0, t - shown), shown);
  const pips = Array.from({ length: shown }, (_, i) =>
    `<i class="disc-pip${i < filled ? " is-on" : ""}${i === shown - 1 ? " is-last" : ""}"></i>`).join("");
  return `<span class="disc-pips" title="${c} amarillas · sanción al llegar a ${t}">${pips}</span><span class="disc-count">${c}/${t}</span>`;
}

function discSource(item) {
  if (item.official || item.verified) {
    const label = item.official ? "Oficial" : "Verificado";
    const chip = `<span class="kchip kchip--under">${label}</span>`;
    return item.source_url ? `<a href="${discEsc(item.source_url)}" target="_blank" rel="noopener">${chip}</a>` : chip;
  }
  const conf = item.confidence ? ` · regla ${discEsc(item.confidence)}` : "";
  return `<span class="kchip" title="Calculado con las tarjetas registradas${conf}">Calculado</span>`;
}

function discMatchLabel(m) {
  if (!m) return `<span class="muted">sin partido publicado</span>`;
  return `<span class="disc-match">${discMedia("team", m.opponent)}<span>${m.venue === "H" ? "vs" : "en"} ${discEsc(discTeamName(m.opponent))}</span><small>${discEsc(discDate(m.date, m.time))}</small></span>`;
}

function discBanText(item) {
  if (item.min_only) return `mín. ${item.remaining || 1} partido · pendiente de comité`;
  const n = item.remaining || item.ban_matches || 1;
  return `${n} partido${n > 1 ? "s" : ""}`;
}

function discPlayerCell(item, linkFn) {
  const href = linkFn ? linkFn(item.team, item.player) : null;
  const inner = `<span class="player-cell">${discMedia("player", item.player, item.team)}<b>${discEsc(item.player)}</b></span>`;
  return href ? `<a href="${href}">${inner}</a>` : inner;
}

function discSuspendedTable(items, opts = {}) {
  if (!items.length) return "";
  return `
  <div class="table-wrap">
    <table class="ktable disc-table">
      <thead><tr>
        <th>Jugador</th>${opts.hideTeam ? "" : '<th class="hide-sm">Equipo</th>'}
        <th>Motivo</th><th>Sanción</th><th>Se pierde</th><th class="hide-xs">Fuente</th>
      </tr></thead>
      <tbody>${items.map(i => `
        <tr class="disc-row disc-row--suspended">
          <td>${discPlayerCell(i, opts.playerHref)}${opts.hideTeam ? "" : `<small class="show-sm-only muted">${discEsc(discTeamName(i.team))}</small>`}</td>
          ${opts.hideTeam ? "" : `<td class="hide-sm"><span class="fx-team">${discMedia("team", i.team)}${discEsc(discTeamName(i.team))}</span></td>`}
          <td>${discEsc(i.reason || i.notes || "Sanción")}${i.trigger_opponent ? `<small class="muted"> vs ${discEsc(discTeamName(i.trigger_opponent))}</small>` : ""}</td>
          <td><span class="disc-ban">${discEsc(discBanText(i))}</span></td>
          <td>${(i.misses || []).length ? i.misses.map(discMatchLabel).join("") : discMatchLabel(null)}</td>
          <td class="hide-xs">${discSource(i)}</td>
        </tr>`).join("")}
      </tbody>
    </table>
  </div>`;
}

function discRiskTable(items, opts = {}) {
  if (!items.length) return "";
  return `
  <div class="table-wrap">
    <table class="ktable disc-table">
      <thead><tr>
        <th>Jugador</th>${opts.hideTeam ? "" : '<th class="hide-sm">Equipo</th>'}
        <th>Amarillas</th><th>Si ve una más</th><th class="hide-sm">Próximo partido</th><th class="hide-xs">Fuente</th>
      </tr></thead>
      <tbody>${items.map(i => `
        <tr class="disc-row disc-row--risk">
          <td>${discPlayerCell(i, opts.playerHref)}${opts.hideTeam ? "" : `<small class="show-sm-only muted">${discEsc(discTeamName(i.team))}</small>`}</td>
          ${opts.hideTeam ? "" : `<td class="hide-sm"><span class="fx-team">${discMedia("team", i.team)}${discEsc(discTeamName(i.team))}</span></td>`}
          <td>${i.window_cards != null ? `${discCardPips(i.window_cards, i.threshold)}<small class="muted"> en 10 partidos</small>` : discCardPips(i.cards, i.threshold)}</td>
          <td><span class="disc-ban disc-ban--risk">${discEsc(i.ban_matches || 1)} partido${(i.ban_matches || 1) > 1 ? "s" : ""}</span></td>
          <td class="hide-sm">${discMatchLabel(i.next)}</td>
          <td class="hide-xs">${discSource(i)}</td>
        </tr>`).join("")}
      </tbody>
    </table>
  </div>`;
}
