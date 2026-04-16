"""
Definiciones de estilos CSS para la interfaz de KICKDEX en Streamlit.
Enfocado en estética 'Data-Dense' y 'OLED Dark'.
"""

# Colores de marca
COLOR_TURF = "#00d4aa"
COLOR_SIGNAL_BLUE = "#5bd6ff"
COLOR_EDGE_GOLD = "#f5b93c"
COLOR_RED_CARD = "#ff5a6e"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ── Base ── */
    .stApp {{
        background-color: #05070d;
        color: #e8eaf6;
        font-family: 'IBM Plex Sans', sans-serif;
    }}

    /* ── Headers ── */
    h1, h2, h3, h4, h5 {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        color: #e8eaf6 !important;
    }}

    /* ── Terminal Data Style ── */
    .mono {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 45px;
        white-space: pre;
        background-color: #0b0f1a;
        border-radius: 8px 8px 0px 0px;
        color: #8b9ab0;
        padding-left: 16px;
        padding-right: 16px;
        border: 1px solid #1a2236;
        border-bottom: none;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #1a2236 !important;
        color: {COLOR_TURF} !important;
        border-top: 2px solid {COLOR_TURF} !important;
    }}

    /* ── Cards & Containers ── */
    [data-testid="stVerticalBlock"] > div > div > [data-testid="stVerticalBlock"] {{
        background-color: #0b0f1a;
        border: 1px solid #1a2236;
        border-radius: 12px;
        padding: 20px;
    }}

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #e8eaf6;
    }}
    [data-testid="stMetricLabel"] {{
        color: #8b9ab0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {{
        background-color: #0b0f1a;
        border: 1px solid #1a2236;
        border-radius: 8px;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOR_TURF} 0%, #0097a7 100%);
        color: #0e1117;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        transition: transform 0.1s;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
    }}

    /* ── Custom Tags ── */
    .tag {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }}
    .tag-w {{ background: #00d4aa22; color: #00d4aa; border: 1px solid #00d4aa44; }}
    .tag-d {{ background: #f0c04022; color: #f0c040; border: 1px solid #f0c04044; }}
    .tag-l {{ background: #ff5a6e22; color: #ff5a6e; border: 1px solid #ff5a6e44; }}

    /* ── Prob Bar ── */
    .prob-container {{
        background: #1a2236;
        border-radius: 4px;
        height: 24px;
        width: 100%;
        margin: 4px 0;
        overflow: hidden;
        display: flex;
    }}
    .prob-bar {{
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        color: #0e1117;
    }}

    /* ── Disclaimer ── */
    .disclaimer {{
        color: #8b9ab0;
        font-size: 0.7rem;
        border-top: 1px solid #1a2236;
        margin-top: 40px;
        padding-top: 10px;
        text-align: center;
    }}
</style>
""",


def result_tag(res: str) -> str:
    cls = "tag-w" if res == "W" else ("tag-d" if res == "D" else "tag-l")
    return f'<span class="tag {cls}">{res}</span>'


def prob_bar_html(p_h: float, p_d: float, p_a: float) -> str:
    total = p_h + p_d + p_a
    ph_pct = (p_h / total) * 100
    pd_pct = (p_d / total) * 100
    pa_pct = (p_a / total) * 100
    return f"""
    <div class="prob-container">
        <div class="prob-bar" style="width:{ph_pct}%; background:{COLOR_TURF};" title="Local: {p_h*100:.1f}%">{int(ph_pct)}%</div>
        <div class="prob-bar" style="width:{pd_pct}%; background:#8b9ab0;" title="Empate: {p_d*100:.1f}%">{int(pd_pct)}%</div>
        <div class="prob-bar" style="width:{pa_pct}%; background:{COLOR_SIGNAL_BLUE};" title="Visitante: {p_a*100:.1f}%">{int(pa_pct)}%</div>
    </div>
    """


def alert_card_html(text: str, color: str, emoji: str) -> str:
    return f"""
    <div style="background:{color}15; border-left: 3px solid {color}; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;">
        <span style="font-size:1rem; margin-right:8px;">{emoji}</span>
        <span style="color:#e8eaf6; font-size:0.9rem;">{text}</span>
    </div>
    """
