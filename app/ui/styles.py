"""
Estilos de Grado Institucional para KICKDEX.
Replicando la estética premium de la web estática con la potencia de Streamlit.
"""

COLOR_TURF = "#00d4aa"
COLOR_SIGNAL_BLUE = "#5bd6ff"
COLOR_EDGE_GOLD = "#f5b93c"
COLOR_RED_CARD = "#ff5a6e"
COLOR_BG = "#05070d"
COLOR_CARD = "#0b0f1a"
COLOR_BORDER = "#1a2236"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ── Root & Base ── */
    .stApp {{
        background-color: {COLOR_BG};
        color: #e8eaf6;
        font-family: 'IBM Plex Sans', sans-serif;
    }}

    /* ── Glassmorphism Cards ── */
    [data-testid="stVerticalBlock"] > div > div > [data-testid="stVerticalBlock"] {{
        background: linear-gradient(145deg, {COLOR_CARD} 0%, #080a12 100%);
        border: 1px solid {COLOR_BORDER};
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        transition: border-color 0.3s ease;
    }}
    [data-testid="stVerticalBlock"] > div > div > [data-testid="stVerticalBlock"]:hover {{
        border-color: {COLOR_TURF}33;
    }}

    /* ── Typography ── */
    h1, h2, h3 {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -1px !important;
    }}
    .mono, code, .stMetricValue {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* ── Custom Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        padding: 10px 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 48px;
        background: {COLOR_CARD};
        border: 1px solid {COLOR_BORDER};
        border-radius: 12px;
        color: #8b9ab0;
        padding: 0 24px;
        font-weight: 600;
        transition: all 0.2s;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLOR_BORDER} !important;
        color: {COLOR_TURF} !important;
        border: 1px solid {COLOR_TURF}44 !important;
        box-shadow: 0 0 15px {COLOR_TURF}22;
    }}

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {{
        color: {COLOR_TURF};
        font-size: 2.2rem !important;
    }}
    [data-testid="stMetricLabel"] {{
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
        font-size: 0.7rem;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOR_TURF} 0%, #0097a7 100%);
        color: {COLOR_BG} !important;
        border: none;
        border-radius: 14px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 15px 30px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 30px {COLOR_TURF}55;
    }}

    /* ── Dataframes & Tables ── */
    .stDataFrame {{
        border-radius: 16px;
        border: 1px solid {COLOR_BORDER};
    }}
</style>
"""

def alert_card_html(text, color=COLOR_TURF, emoji="⚡"):
    return f'''
    <div style="background:{color}10; border-left: 5px solid {color}; padding:20px; border-radius:12px; margin-bottom:15px; border-right: 1px solid {color}10; border-top: 1px solid {color}10; border-bottom: 1px solid {color}10;">
        <div style="display:flex; align-items:center; gap:15px;">
            <span style="font-size:1.5rem;">{emoji}</span>
            <span style="color:#e8eaf6; font-size:1rem; font-weight:600; letter-spacing:0.3px;">{text}</span>
        </div>
    </div>
    '''
