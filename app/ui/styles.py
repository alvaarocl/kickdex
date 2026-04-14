"""CSS global de Analista Pro — modo oscuro, estética pro-analista."""

CUSTOM_CSS = """
<style>
/* ── Base ─────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background-color: #0e1117;
}
[data-testid="stSidebar"] {
    background-color: #1a1f2e;
}
h1, h2, h3, h4 {
    color: #e8eaf6 !important;
    letter-spacing: -0.3px;
}
p, li, span, label {
    color: #b0bec5 !important;
}
/* ── Tarjetas de métricas ─────────────────────────────────── */
[data-testid="metric-container"] {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] {
    color: #e8eaf6 !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #8b9ab0 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
[data-testid="stMetricDelta"] svg { display: none; }
/* ── Tablas ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}
/* ── Tabs ─────────────────────────────────────────────────── */
[data-testid="stTabs"] button {
    color: #8b9ab0 !important;
    font-weight: 600;
    font-size: 0.85rem;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00d4aa !important;
    border-bottom: 2px solid #00d4aa !important;
}
/* ── Botón primario ───────────────────────────────────────── */
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #00d4aa, #0097a7) !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
}
/* ── Divider ──────────────────────────────────────────────── */
hr {
    border-color: #2a3040 !important;
    margin: 18px 0 !important;
}
/* ── Alertas personalizadas ───────────────────────────────── */
.alert-card {
    background: #1a1f2e;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    border-left: 3px solid #00d4aa;
    font-size: 0.88rem;
    color: #d0d9e6 !important;
}
.alert-card.medium { border-left-color: #f0c040; }
.alert-card.low    { border-left-color: #8b9ab0; }
/* ── Prob bar ─────────────────────────────────────────────── */
.prob-container {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 6px 0;
}
.prob-label { color: #8b9ab0; font-size: 0.78rem; min-width: 90px; }
.prob-bar-wrap { flex: 1; background: #2a3040; border-radius: 4px; height: 8px; }
.prob-bar { height: 8px; border-radius: 4px; }
.prob-value { color: #e8eaf6; font-size: 0.82rem; min-width: 42px; text-align: right; font-weight: 600; }
/* ── Form tag ─────────────────────────────────────────────── */
.form-w { background:#00d4aa22; color:#00d4aa; padding:2px 7px; border-radius:4px; font-weight:700; font-size:0.8rem; }
.form-d { background:#f0c04022; color:#f0c040; padding:2px 7px; border-radius:4px; font-weight:700; font-size:0.8rem; }
.form-l { background:#ff4b4b22; color:#ff4b4b; padding:2px 7px; border-radius:4px; font-weight:700; font-size:0.8rem; }
/* ── Value badge ──────────────────────────────────────────── */
.value-badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
.value-green { background:#00d4aa22; color:#00d4aa; }
.value-red   { background:#ff4b4b22; color:#ff4b4b; }
.value-grey  { background:#2a304088; color:#8b9ab0; }
/* ── Disclaimer ───────────────────────────────────────────── */
.disclaimer {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 6px;
    padding: 10px 14px;
    color: #8b9ab0 !important;
    font-size: 0.75rem;
    margin-top: 20px;
}
</style>
"""


def result_tag(result: str) -> str:
    """Devuelve HTML de tag coloreado para W/D/L."""
    tags = {
        "W": '<span class="form-w">G</span>',
        "D": '<span class="form-d">E</span>',
        "L": '<span class="form-l">P</span>',
    }
    return tags.get(result, result)


def prob_bar_html(label: str, prob: float, color: str = "#00d4aa") -> str:
    """Genera barra de probabilidad HTML."""
    pct = int(prob * 100)
    return f"""
    <div class="prob-container">
        <span class="prob-label">{label}</span>
        <div class="prob-bar-wrap">
            <div class="prob-bar" style="width:{pct}%; background:{color};"></div>
        </div>
        <span class="prob-value">{pct}%</span>
    </div>"""


def alert_card_html(alert) -> str:
    """Genera card HTML para un Alert."""
    cls_map = {"HIGH": "", "MEDIUM": " medium", "LOW": " low"}
    cls = cls_map.get(alert.strength.value, "")
    return f'<div class="alert-card{cls}">{alert.emoji} {alert.text}</div>'
