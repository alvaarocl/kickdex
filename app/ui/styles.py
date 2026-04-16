"""
Estilos Core para KICKDEX — Terminal de Datos Profesional.
Inyecta CSS de alto nivel para estética OLED Dark y Glassmorphism.
"""

COLOR_BRAND = "#00d4aa"
COLOR_BG = "#05070d"
COLOR_CARD = "#0b0f1a"
COLOR_BORDER = "#1a2236"
COLOR_TEXT = "#e8eaf6"
COLOR_MUTED = "#8b9ab0"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ── Base Reset ── */
    .stApp {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: 'IBM Plex Sans', sans-serif;
    }}

    /* ── Ocultar basura de Streamlit ── */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    [data-testid="stHeader"] {{background: rgba(0,0,0,0);}}

    /* ── Contenedores Tipo Glassmorphism ── */
    [data-testid="stVerticalBlock"] > div > div > [data-testid="stVerticalBlock"] {{
        background: {COLOR_CARD};
        border: 1px solid {COLOR_BORDER};
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }}

    /* ── Tabs Profesionales ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: {COLOR_CARD};
        border-radius: 10px 10px 0px 0px;
        color: {COLOR_MUTED};
        padding: 0 20px;
        border: 1px solid {COLOR_BORDER};
        border-bottom: none;
        font-weight: 600;
        transition: all 0.2s;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_BORDER} !important;
        color: {COLOR_BRAND} !important;
        border-top: 3px solid {COLOR_BRAND} !important;
    }}

    /* ── Métricas Estilo Bloomberg ── */
    [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        letter-spacing: -1px;
    }}
    [data-testid="stMetricLabel"] {{
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 1.5px;
        color: {COLOR_MUTED};
    }}

    /* ── Dataframes Limpios ── */
    .stDataFrame {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ── Botones Premium ── */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOR_BRAND} 0%, #0097a7 100%);
        color: #05070d !important;
        font-weight: 700;
        border-radius: 12px;
        border: none;
        padding: 12px 28px;
        width: 100%;
        transition: transform 0.1s, box-shadow 0.1s;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 212, 170, 0.4);
    }}
</style>
"""

def alert_card_html(text, color="#f5b93c", emoji="⚠️"):
    return f'''
    <div style="background:{color}15; border-left: 4px solid {color}; padding:16px; border-radius:8px; margin-bottom:12px;">
        <span style="font-size:1.2rem; margin-right:10px;">{emoji}</span>
        <span style="color:#e8eaf6; font-size:0.95rem; font-weight:500;">{text}</span>
    </div>
    '''
