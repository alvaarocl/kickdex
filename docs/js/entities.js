/**
 * Shared visual identity renderer for standalone KICKDEX pages.
 */
"use strict";

window.KDXEntities = (() => {
  let teamAssets = { teams: {} };
  let playerAssets = { players: {} };

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[char]);
  }

  function initials(value) {
    return String(value || "KD").trim().split(/\s+/).slice(0, 2).map(part => part[0] || "").join("").toUpperCase();
  }

  function configure(teams, players) {
    teamAssets = teams || { teams: {} };
    playerAssets = players || { players: {} };
  }

  function media(kind, name, team = "", extraClass = "") {
    const asset = kind === "player"
      ? playerAssets.players?.[team + "::" + name] || {}
      : teamAssets.teams?.[name] || {};
    const src = asset.photo_local || asset.photo || asset.crest_local || asset.crest;
    const label = kind === "team"
      ? initials(typeof teamDisplayName === "function" ? teamDisplayName(name) : name)
      : (asset.initials || initials(name));
    const cls = kind === "player" ? "entity-media entity-media--player" : "entity-media entity-media--team";
    if (!src) return '<span class="' + cls + " " + extraClass + '" aria-hidden="true">' + esc(label) + "</span>";
    return '<span class="' + cls + " " + extraClass + '"><img src="' + esc(src) + '" alt="" loading="lazy" onerror="this.parentElement.classList.add(\'is-fallback\');this.remove()"><i>' + esc(label) + "</i></span>";
  }

  return { configure, initials, media };
})();
