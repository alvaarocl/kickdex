/* ============================================================
   KICKDEX — Edge Number component (V3 brand)
   Renders the brand hero metric: EDGE %, probability or KPI.
   ============================================================ */

const SIZE_CLASS = {
  xxl: 'edge-number--xxl',
  xl:  '',
  lg:  'edge-number--lg',
  md:  'edge-number--md',
};

const TONE_CLASS = {
  value:   '',
  risk:    'edge-number--risk',
  neutral: 'edge-number--neutral',
};

function formatValue(value, { prefix = '', suffix = '%', decimals = 1 } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const sign = value > 0 ? '+' : '';
  return `${prefix}${sign}${Number(value).toFixed(decimals)}${suffix}`;
}

export function renderEdgeNumber(target, {
  value,
  label = 'EDGE',
  caption = '',
  size = 'xl',
  tone = 'value',
  prefix = '',
  suffix = '%',
  decimals = 1,
  animate = true,
} = {}) {
  const el = typeof target === 'string' ? document.querySelector(target) : target;
  if (!el) return;

  const sizeCls = SIZE_CLASS[size] ?? '';
  const toneCls = TONE_CLASS[tone] ?? '';
  const formatted = formatValue(value, { prefix, suffix, decimals });

  el.innerHTML = `
    <div class="edge-number ${sizeCls} ${toneCls}">
      <span class="edge-number__label">${label}</span>
      <span class="edge-number__value" data-final="${formatted}">${animate ? '0.0%' : formatted}</span>
      <div class="edge-number__spark"></div>
      ${caption ? `<span class="edge-number__caption">${caption}</span>` : ''}
    </div>
  `;

  if (animate && typeof value === 'number' && !Number.isNaN(value)) {
    typeNumber(el.querySelector('.edge-number__value'), value, { prefix, suffix, decimals });
  }
}

function typeNumber(node, target, opts) {
  if (!node) return;
  const duration = 600;
  const start = performance.now();
  const from = 0;

  function tick(now) {
    const t = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    const cur = from + (target - from) * eased;
    node.firstChild
      ? (node.firstChild.nodeValue = formatValue(cur, opts))
      : (node.textContent = formatValue(cur, opts));
    if (t < 1) requestAnimationFrame(tick);
    else node.textContent = formatValue(target, opts);
  }
  requestAnimationFrame(tick);
}

/* Helper: derive edge from probabilities.
   edge% = (probReal - probImplied) * 100
   probImplied = 1 / odds                                                */
export function computeEdge({ probReal, odds }) {
  if (!probReal || !odds || odds <= 1) return null;
  const probImplied = 1 / odds;
  return (probReal - probImplied) * 100;
}

/* Auto-mount: any element with [data-edge] gets rendered. */
export function mountEdgeNumbers(root = document) {
  root.querySelectorAll('[data-edge]').forEach((el) => {
    const value = parseFloat(el.dataset.edge);
    renderEdgeNumber(el, {
      value,
      label:    el.dataset.edgeLabel   || 'EDGE',
      caption:  el.dataset.edgeCaption || '',
      size:     el.dataset.edgeSize    || 'xl',
      tone:     el.dataset.edgeTone    || (value >= 0 ? 'value' : 'risk'),
      suffix:   el.dataset.edgeSuffix  ?? '%',
      decimals: parseInt(el.dataset.edgeDecimals ?? '1', 10),
      animate:  el.dataset.edgeAnimate !== 'false',
    });
  });
}

if (typeof window !== 'undefined') {
  window.KDXEdge = { renderEdgeNumber, computeEdge, mountEdgeNumbers };
  document.addEventListener('DOMContentLoaded', () => mountEdgeNumbers());
}
