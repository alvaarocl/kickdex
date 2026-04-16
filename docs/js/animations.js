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
 */
function triggerAnimations(container) {
  staggerIn(container, 65);
  setTimeout(() => observeCounters(container), 80);
}

// ═══════════════════════════════════════════════════════════
// LANDING PAGE ANIMATIONS
// ═══════════════════════════════════════════════════════════

let _lpScrollHandler = null;
let _lpRevealEls     = [];

/**
 * Initialize all landing page animations.
 * Safe to call multiple times (teardown + reinit).
 */
function initLandingAnimations() {
  const overlay = document.getElementById("landing-overlay");
  if (!overlay) return;

  // Teardown previous listeners
  if (_lpScrollHandler) {
    overlay.removeEventListener("scroll", _lpScrollHandler);
    _lpScrollHandler = null;
  }
  _lpRevealEls = [];

  _setupSmoothScroll(overlay);
  _setupScrollReveal(overlay);
  _setupNavbarScroll(overlay);
  _setupMockupAnimation();

  // Trigger initial check after a short paint delay
  setTimeout(() => _checkReveal(overlay), 120);
}

// ── Smooth scroll for in-page nav links ────────────────────
function _setupSmoothScroll(overlay) {
  overlay.querySelectorAll('a[href^="#lp-"]').forEach(a => {
    a.addEventListener("click", e => {
      const id     = a.getAttribute("href").slice(1);
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      const oRect = overlay.getBoundingClientRect();
      const tRect = target.getBoundingClientRect();
      const scrollTo = overlay.scrollTop + (tRect.top - oRect.top) - 68;
      overlay.scrollTo({ top: scrollTo, behavior: "smooth" });
    });
  });
}

// ── Navbar scroll state ─────────────────────────────────────
function _setupNavbarScroll(overlay) {
  const nav = document.getElementById("lpNav");

  _lpScrollHandler = () => {
    const y = overlay.scrollTop;

    if (nav) nav.classList.toggle("lp-nav--scrolled", y > 30);

    // Parallax orbs
    const orb1 = overlay.querySelector(".lp-orb-1");
    const orb2 = overlay.querySelector(".lp-orb-2");
    const orb3 = overlay.querySelector(".lp-orb-3");
    if (orb1) orb1.style.transform = `translateY(${y * 0.1}px)`;
    if (orb2) orb2.style.transform = `translateY(${-y * 0.07}px)`;
    if (orb3) orb3.style.transform = `translateY(${y * 0.05}px)`;

    _checkReveal(overlay);
  };

  overlay.addEventListener("scroll", _lpScrollHandler, { passive: true });
}

// ── Scroll-reveal via scroll event (reliable for fixed containers) ──
function _setupScrollReveal(overlay) {
  const groups = [
    // Leagues section
    { sel: "#lp-leagues .lp-section-eyebrow", base: 0,   stagger: 0   },
    { sel: "#lp-leagues .lp-section-h2",      base: 80,  stagger: 0   },
    { sel: ".lp-league-pill",                 base: 0,   stagger: 45,  variant: "scale" },

    // Features section
    { sel: "#lp-features .lp-section-eyebrow", base: 0,   stagger: 0  },
    { sel: "#lp-features .lp-section-h2",      base: 70,  stagger: 0  },
    { sel: "#lp-features .lp-section-sub",     base: 120, stagger: 0  },
    { sel: ".lp-feat-card",                    base: 0,   stagger: 75 },

    // How it works
    { sel: "#lp-how .lp-section-eyebrow",      base: 0,   stagger: 0   },
    { sel: "#lp-how .lp-section-h2",           base: 70,  stagger: 0   },
    { sel: ".lp-step",                         base: 0,   stagger: 130, variant: "up" },
    { sel: ".lp-step-arrow",                   base: 180, stagger: 0,   variant: "fade" },

    // Trust bar
    { sel: ".lp-trust-item",                   base: 0,   stagger: 55  },

    // Final CTA
    { sel: ".lp-final-h2",                      base: 0,   stagger: 0   },
    { sel: ".lp-final-sub",                     base: 90,  stagger: 0   },
    { sel: ".lp-final-section .lp-cta-primary", base: 170, stagger: 0,  variant: "scale" },
    { sel: ".lp-final-disclaimer",              base: 240, stagger: 0,  variant: "fade"  },
  ];

  _lpRevealEls = [];

  groups.forEach(({ sel, base, stagger, variant }) => {
    overlay.querySelectorAll(sel).forEach((el, i) => {
      el.classList.add("lp-reveal");
      if (variant) el.classList.add(`lp-reveal--${variant}`);
      el.style.setProperty("--lp-d", `${base + i * stagger}ms`);
      _lpRevealEls.push(el);
    });
  });
}

/**
 * Check all registered reveal elements and add lp-in to those in viewport.
 * Uses getBoundingClientRect relative to overlay bounds — works correctly
 * for position:fixed overflow-y:auto containers.
 */
function _checkReveal(overlay) {
  if (!_lpRevealEls.length) return;
  const oRect  = overlay.getBoundingClientRect();
  const bottom = oRect.height + 40; // 40px grace below fold

  _lpRevealEls = _lpRevealEls.filter(el => {
    if (el.classList.contains("lp-in")) return false; // already triggered
    const rect = el.getBoundingClientRect();
    const elTop = rect.top - oRect.top;
    if (elTop < bottom && rect.bottom > oRect.top) {
      el.classList.add("lp-in");
      return false; // remove from future checks
    }
    return true;
  });
}

// ── Parallax placeholder (handled in scroll handler above) ──
function _setupParallax() {}

// ── Mockup: staggered form badges + rows + alert ─────────────
function _setupMockupAnimation() {
  document.querySelectorAll(".lp-mock-form span").forEach((el, i) => {
    el.style.animation = `lp-badge-pop .3s cubic-bezier(.34,1.56,.64,1) ${300 + i * 90}ms both`;
  });

  document.querySelectorAll(".lp-mock-row").forEach((el, i) => {
    el.style.animation = `lp-slide-up .4s ease ${500 + i * 90}ms both`;
  });

  const alert = document.querySelector(".lp-mock-alert");
  if (alert) {
    alert.style.animation = "lp-slide-up .4s ease 800ms both, lp-alert-glow 2.5s 1.2s ease-in-out infinite";
  }
}
