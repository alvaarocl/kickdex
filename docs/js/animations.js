/**
 * animations.js — Premium animations: team badges, count-up, stagger entrance
 */

"use strict";

// ── Team badge color palette (deterministic from name hash) ──
const BADGE_PALETTES = [
  ["#00d4aa", "#009e7e"],  // emerald
  ["#38bdf8", "#0369a1"],  // sky
  ["#f59e0b", "#b45309"],  // amber
  ["#f43f5e", "#be123c"],  // rose
  ["#a78bfa", "#6d28d9"],  // violet
  ["#fb923c", "#c2410c"],  // orange
  ["#34d399", "#047857"],  // green
  ["#60a5fa", "#1d4ed8"],  // blue
  ["#e879f9", "#a21caf"],  // fuchsia
  ["#facc15", "#a16207"],  // yellow
  ["#2dd4bf", "#0f766e"],  // teal
  ["#f97316", "#9a3412"],  // deep orange
];

function _teamHash(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) {
    h = Math.imul(31, h) + name.charCodeAt(i) | 0;
  }
  return Math.abs(h) % BADGE_PALETTES.length;
}

function teamBadgeGradient(name) {
  const [c1, c2] = BADGE_PALETTES[_teamHash(name)];
  return `linear-gradient(145deg, ${c1} 0%, ${c2} 100%)`;
}

function teamBadgeInitials(name) {
  const parts = name.trim().split(/[\s\-\.]+/).filter(w => w.length > 0);
  if (!parts || parts.length === 0) return name.slice(0, 2).toUpperCase();
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Returns HTML string for a team badge circle.
 * @param {string} name  Team name
 * @param {number} size  Size in px (default 50)
 */
function teamBadge(name, size = 50) {
  const initials = teamBadgeInitials(name);
  const gradient = teamBadgeGradient(name);
  const radius   = Math.round(size * 0.28);
  return `<div class="team-badge" style="background:${gradient};width:${size}px;height:${size}px;border-radius:${radius}px;" title="${name}"><span>${initials}</span></div>`;
}

// ── Count-up animation ────────────────────────────────────

/**
 * Animate a number in an element from 0 to target.
 */
function countUp(el, target, duration = 800, decimals = 1) {
  if (!el) return;
  const start = performance.now();
  function tick(now) {
    const t = Math.min((now - start) / duration, 1);
    // easeOutExpo
    const ease = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
    const val  = target * ease;
    el.textContent = decimals === 0 ? Math.round(val) : val.toFixed(decimals);
    if (t < 1) requestAnimationFrame(tick);
    else el.textContent = decimals === 0 ? String(Math.round(target)) : target.toFixed(decimals);
  }
  requestAnimationFrame(tick);
}

/**
 * Wire IntersectionObserver to all [data-count] elements inside container.
 * Usage: <span data-count="1.82" data-decimals="2" class="count-up">1.82</span>
 */
function observeCounters(container) {
  const root = container || document;
  const els  = root.querySelectorAll("[data-count]");
  if (!els.length) return;

  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el       = entry.target;
      const target   = parseFloat(el.dataset.count)    ?? 0;
      const decimals = parseInt(el.dataset.decimals    ?? "1");
      const duration = parseInt(el.dataset.duration    ?? "800");
      countUp(el, target, duration, decimals);
      io.unobserve(el);
    });
  }, { threshold: 0.25 });

  els.forEach(el => io.observe(el));
}

// ── Stagger entrance animations ───────────────────────────

/**
 * Apply sequential animation delays to .stagger-item elements.
 * We set the full animation shorthand to avoid restart artefacts from
 * overriding only animation-delay on an already-playing animation.
 */
function staggerIn(container, delayStep = 65) {
  const root  = container || document;
  const items = root.querySelectorAll(".stagger-item");
  items.forEach((el, i) => {
    const delay = i * delayStep;
    el.style.animation = `staggerIn .55s cubic-bezier(.2,.8,.2,1) ${delay}ms both`;
  });
}

// ── Master trigger — call after dynamic render ─────────────

/**
 * Trigger all premium animations within a freshly rendered container.
 * Called from comparador.js, h2h.js, etc. after innerHTML is set.
 */
function triggerAnimations(container) {
  staggerIn(container, 65);
  // Small delay so DOM is fully painted before counters observe
  setTimeout(() => observeCounters(container), 80);
}
