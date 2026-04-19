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

let _lpScrollHandler  = null;
let _lpRevealEls      = [];
let _lpMouseGlowBound = null;
let _lpRevealObserver = null;
let _lpGlowRaf        = null;

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
  if (_lpMouseGlowBound) {
    overlay.removeEventListener("mousemove", _lpMouseGlowBound);
    _lpMouseGlowBound = null;
  }
  if (_lpRevealObserver) {
    _lpRevealObserver.disconnect();
    _lpRevealObserver = null;
  }
  if (_lpGlowRaf) {
    cancelAnimationFrame(_lpGlowRaf);
    _lpGlowRaf = null;
  }
  _lpRevealEls = [];

  _setupSmoothScroll(overlay);
  _setupScrollReveal(overlay);
  _setupNavbarScroll(overlay);
  _setupMockupAnimation();
  _setupButtonRipples(overlay);
  _setupMouseGlow(overlay);
  _setupProgressBar(overlay);
  _setupActiveNavHighlight(overlay);
  setTimeout(() => _setupLpCounters(overlay), 700);

  // Initial check: reveal elements already in viewport on load (desktop + mobile)
  setTimeout(_checkReveal, 150);
}

// ── Smooth scroll for ALL in-page anchor links ─────────────
function _setupSmoothScroll(overlay) {
  overlay.querySelectorAll('a[href^="#"]').forEach(a => {
    if (a._lpScroll) return; // already bound
    a._lpScroll = true;
    a.addEventListener("click", e => {
      const href = a.getAttribute("href");
      if (!href || href === "#") return;
      const id     = href.slice(1);
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      const oRect   = overlay.getBoundingClientRect();
      const tRect   = target.getBoundingClientRect();
      const scrollTo = overlay.scrollTop + (tRect.top - oRect.top) - 68;
      overlay.scrollTo({ top: scrollTo, behavior: "smooth" });
    });
  });
}

// ── Scroll progress bar ─────────────────────────────────────
function _setupProgressBar(overlay) {
  let bar = document.getElementById("lp-progress-bar");
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "lp-progress-bar";
    overlay.appendChild(bar);
  }
  overlay.addEventListener("scroll", () => {
    const max  = overlay.scrollHeight - overlay.clientHeight;
    const pct  = max > 0 ? (overlay.scrollTop / max) * 100 : 0;
    bar.style.width = pct + "%";
  }, { passive: true });
}

// ── Mouse glow — lerp via transform (GPU composited, no layout thrash) ──
function _setupMouseGlow(overlay) {
  let glow = document.getElementById("lp-mouse-glow");
  if (!glow) {
    glow = document.createElement("div");
    glow.id = "lp-mouse-glow";
    document.body.appendChild(glow);
  }

  let tx = 0, ty = 0, cx = 0, cy = 0, glowVisible = false;

  function lerpGlow() {
    cx += (tx - cx) * 0.11;
    cy += (ty - cy) * 0.11;
    glow.style.transform = `translate(calc(${cx}px - 50%), calc(${cy}px - 50%))`;
    if (Math.abs(tx - cx) > 0.3 || Math.abs(ty - cy) > 0.3) {
      _lpGlowRaf = requestAnimationFrame(lerpGlow);
    } else {
      _lpGlowRaf = null;
    }
  }

  _lpMouseGlowBound = e => {
    tx = e.clientX;
    ty = e.clientY;
    if (!glowVisible) {
      cx = tx; cy = ty;
      glow.style.transform = `translate(calc(${cx}px - 50%), calc(${cy}px - 50%))`;
      glow.style.opacity   = "1";
      glowVisible = true;
    }
    if (!_lpGlowRaf) _lpGlowRaf = requestAnimationFrame(lerpGlow);
  };

  overlay.addEventListener("mousemove", _lpMouseGlowBound, { passive: true });
  overlay.addEventListener("mouseleave", () => {
    glow.style.opacity = "0";
    glowVisible = false;
  }, { passive: true });
}

// ── Button ripple effect ────────────────────────────────────
function _setupButtonRipples(overlay) {
  const btns = overlay.querySelectorAll(".lp-cta-primary, .lp-cta-ghost, .lp-nav-cta");
  btns.forEach(btn => {
    if (btn._lpRipple) return;
    btn._lpRipple = true;
    btn.addEventListener("click", e => {
      const rect   = btn.getBoundingClientRect();
      const circle = document.createElement("span");
      circle.className = "lp-ripple-circle";
      circle.style.left = (e.clientX - rect.left) + "px";
      circle.style.top  = (e.clientY - rect.top)  + "px";
      btn.appendChild(circle);
      setTimeout(() => circle.remove(), 650);
    });
  });
}

// ── LP Hero stat counters (data-counter / data-suffix / data-abbrev) ──
function _setupLpCounters(overlay) {
  const els = overlay.querySelectorAll(".lp-stat-num[data-counter]");
  if (!els.length) return;

  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      io.unobserve(entry.target);
      const el     = entry.target;
      const target = parseFloat(el.dataset.counter) || 0;
      const suffix = el.dataset.suffix || "";
      const abbrev = el.dataset.abbrev === "true";
      const dur    = 1400;
      const start  = performance.now();

      function tick(now) {
        const t    = Math.min((now - start) / dur, 1);
        const ease = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
        const val  = target * ease;
        let display;
        if (abbrev && val >= 1000) {
          const k = val / 1000;
          display = (k >= 10 ? Math.round(k) : k.toFixed(1).replace(/\.0$/, "")) + "K";
        } else {
          display = Math.round(val).toString();
        }
        el.textContent = display + suffix;
        if (t < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }, { root: overlay, threshold: 0.6 });

  els.forEach(el => io.observe(el));
}

// ── Highlight active nav link based on scroll position ─────
function _setupActiveNavHighlight(overlay) {
  const sections = [
    { id: "lp-leagues",  href: "#lp-leagues"  },
    { id: "lp-features", href: "#lp-features" },
    { id: "lp-how",      href: "#lp-how"      },
  ];
  const navLinks = overlay.querySelectorAll(".lp-nav-links a");

  overlay.addEventListener("scroll", () => {
    const oRect = overlay.getBoundingClientRect();
    let active = null;
    sections.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (!el) return;
      const rect = el.getBoundingClientRect();
      if (rect.top - oRect.top < oRect.height * 0.5) active = id;
    });
    navLinks.forEach(a => {
      const href = a.getAttribute("href");
      a.classList.toggle("lp-nav-active", !!active && href === "#" + active);
    });
  }, { passive: true });
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

    _checkReveal();
  };

  overlay.addEventListener("scroll", _lpScrollHandler, { passive: true });
}

// ── Scroll-reveal via IntersectionObserver ──────────────────
function _setupScrollReveal(overlay) {
  const groups = [
    // Leagues section
    { sel: "#lp-leagues .lp-section-eyebrow", base: 0,   stagger: 0,   variant: "fade" },
    { sel: "#lp-leagues .lp-section-h2",      base: 60,  stagger: 0                    },
    { sel: ".lp-league-pill",                 base: 0,   stagger: 35,  variant: "scale" },

    // Features section
    { sel: "#lp-features .lp-section-eyebrow", base: 0,   stagger: 0,  variant: "fade" },
    { sel: "#lp-features .lp-section-h2",      base: 60,  stagger: 0                   },
    { sel: "#lp-features .lp-section-sub",     base: 110, stagger: 0,  variant: "fade" },
    { sel: ".lp-feat-card",                    base: 0,   stagger: 65                  },

    // How it works
    { sel: "#lp-how .lp-section-eyebrow",      base: 0,   stagger: 0,   variant: "fade" },
    { sel: "#lp-how .lp-section-h2",           base: 60,  stagger: 0                    },
    { sel: ".lp-step",                         base: 0,   stagger: 110, variant: "up"   },
    { sel: ".lp-step-arrow",                   base: 150, stagger: 0,   variant: "fade" },

    // Trust bar
    { sel: ".lp-trust-item",                   base: 0,   stagger: 45                  },

    // Final CTA
    { sel: ".lp-final-h2",                      base: 0,   stagger: 0                   },
    { sel: ".lp-final-sub",                     base: 80,  stagger: 0,  variant: "fade" },
    { sel: ".lp-final-section .lp-cta-primary", base: 150, stagger: 0,  variant: "scale"},
    { sel: ".lp-final-disclaimer",              base: 210, stagger: 0,  variant: "fade" },
  ];

  _lpRevealEls = [];

  // IntersectionObserver: works on mobile (touch scroll)
  _lpRevealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("lp-in");
        _lpRevealObserver.unobserve(entry.target);
        _lpRevealEls = _lpRevealEls.filter(e => e !== entry.target);
      }
    });
  }, { root: overlay, rootMargin: "0px 0px -30px 0px", threshold: 0.08 });

  groups.forEach(({ sel, base, stagger, variant }) => {
    overlay.querySelectorAll(sel).forEach((el, i) => {
      if (el.classList.contains("lp-reveal")) return;
      el.classList.add("lp-reveal");
      if (variant) el.classList.add(`lp-reveal--${variant}`);
      el.style.setProperty("--lp-d", `${base + i * stagger}ms`);
      _lpRevealEls.push(el);
      _lpRevealObserver.observe(el);
    });
  });
}

// Desktop fallback: getBoundingClientRect vs viewport (fires on overlay scroll event)
function _checkReveal() {
  if (!_lpRevealEls.length) return;
  const vh = window.innerHeight;
  _lpRevealEls = _lpRevealEls.filter(el => {
    if (el.classList.contains("lp-in")) return false;
    const rect = el.getBoundingClientRect();
    if (rect.top < vh - 30 && rect.bottom > 0) {
      el.classList.add("lp-in");
      if (_lpRevealObserver) _lpRevealObserver.unobserve(el);
      return false;
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
