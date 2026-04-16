"""
Estilos Core Premium para KICKDEX — Terminal de Datos Institucional.
Replica exactamente la estética de la web estática (OLED Dark, Glassmorphism).
"""
COLOR_BG, COLOR_BRAND, COLOR_BRAND2, COLOR_GOLD = "#05070D", "#2EE6A6", "#5BD6FF", "#F5B93C"
FULL_CSS = """
<style>
:root { --bg:#05070D; --bg1:#0B0F1A; --bg2:#111728; --brand:#2EE6A6; --brand2:#5BD6FF; --brand-soft:rgba(46,230,166,.1); --brand-glow:rgba(46,230,166,.4); --border:rgba(255,255,255,.05); --border2:rgba(255,255,255,.1); --text:#F1F5FB; --muted:#8A94AB; --grad-brand:linear-gradient(135deg,#2EE6A6 0%,#5BD6FF 100%); --grad-card:linear-gradient(160deg,rgba(17,23,40,.85) 0%,rgba(11,15,26,.92) 100%); }
.stApp { background: var(--bg); color: var(--text); font-family: sans-serif; }
header[data-testid="stHeader"], [data-testid="stSidebarNav"], #MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
.main .block-container { padding-top: 0 !important; max-width: 1380px !important; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: #04060e; border-bottom: 1px solid var(--border); padding: 10px 20px 0; position: sticky; top: 0; z-index: 90; }
.stTabs [data-baseweb="tab"] { height: 45px; color: var(--muted); font-size: .8rem; font-weight: 600; background: none !important; border: none !important; }
.stTabs [aria-selected="true"] { color: var(--brand) !important; border-bottom: 2px solid var(--brand) !important; background: rgba(255,255,255,.03) !important; }
.header-inner { display: flex; align-items: center; justify-content: space-between; height: 70px; border-bottom: 1px solid var(--border); padding: 0 20px; margin-bottom: 20px; }
.logo { display: flex; align-items: center; gap: 10px; font-size: 1.3rem; font-weight: 700; color: #fff; }
.logo-icon { width: 34px; height: 34px; background: var(--grad-brand); border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.brand-cursor { color: var(--brand); font-family: monospace; }
.season-badge { background: var(--brand-soft); color: var(--brand); border: 1px solid rgba(0,212,170,.2); padding: 4px 12px; border-radius: 99px; font-size: .7rem; }
.meta-info { color: var(--muted); font-size: .7rem; font-family: monospace; }
.card { background: var(--grad-card); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 20px; }
.section-title { font-size: .9rem; font-weight: 700; color: #fff; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
.section-h2 { font-size: 1.3rem; font-weight: 800; color: #fff; margin-bottom: 5px; }
.section-desc { font-size: .85rem; color: var(--muted); margin-bottom: 20px; }
.fixture-header { display: flex; align-items: center; justify-content: space-between; padding: 20px; background: var(--grad-card); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 20px; }
.fixture-team-name { font-weight: 800; font-size: 1.1rem; }
.fixture-team-sub { font-size: .7rem; color: var(--muted); }
.fixture-vs-badge { width: 40px; height: 40px; border: 1.5px solid var(--brand); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: var(--brand); font-size: .6rem; font-weight: 800; }
.duel-row { display: grid; grid-template-columns: 50px 1fr 80px 1fr 50px; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.duel-val-home { color: var(--brand); font-family: monospace; font-weight: 700; text-align: right; }
.duel-val-away { color: #fb7185; font-family: monospace; font-weight: 700; }
.duel-label { text-align: center; font-size: .6rem; color: var(--muted); text-transform: uppercase; font-weight: 700; }
.duel-track-home, .duel-track-away { height: 6px; background: rgba(255,255,255,.05); border-radius: 3px; overflow: hidden; }
.duel-bar-home { height: 100%; background: var(--brand); float: right; }
.duel-bar-away { height: 100%; background: #fb7185; }
.prob-row { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
.prob-label { color: var(--muted); font-size: .8rem; width: 120px; }
.prob-track { flex: 1; height: 8px; background: rgba(255,255,255,.05); border-radius: 4px; overflow: hidden; }
.prob-fill { height: 100%; background: var(--grad-brand); box-shadow: 0 0 10px var(--brand-glow); }
.prob-pct { font-family: monospace; font-weight: 700; font-size: .8rem; width: 45px; text-align: right; }
.alert-card { background: rgba(46,230,166,.05); border-left: 3px solid var(--brand); padding: 12px; border-radius: 8px; font-size: .8rem; margin-bottom: 8px; }
.alert-card.medium { border-left-color: #F5B93C; background: rgba(245,185,60,.05); }
.fx-card { background: var(--grad-card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 10px; }
.fx-row { display: flex; align-items: center; justify-content: space-between; }
.fx-league-badge { font-size: .6rem; font-weight: 800; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; }
.fx-league-badge.sp1 { background: rgba(46,230,166,.1); color: var(--brand); }
.fx-league-badge.sp2 { background: rgba(91,214,255,.1); color: var(--brand2); }
.fx-team { font-weight: 700; color: #fff; font-size: .95rem; }
.fx-score { font-family: monospace; font-weight: 800; color: var(--brand); background: rgba(46,230,166,.1); padding: 2px 8px; border-radius: 4px; }
.fx-odds { display: flex; gap: 8px; margin-top: 10px; }
.fx-odd { background: var(--bg2); border: 1px solid var(--border); padding: 4px 10px; border-radius: 6px; font-family: monospace; font-size: .75rem; text-align: center; }
.fx-odd span { display: block; font-size: .6rem; color: var(--muted); }
.bg-orb { position: fixed; border-radius: 50%; filter: blur(90px); pointer-events: none; z-index: -1; opacity: .85; }
.bg-orb-1 { width: 600px; height: 400px; background: radial-gradient(ellipse, rgba(0,212,170,.1) 0%, transparent 70%); top: -100px; left: -100px; }
.bg-orb-2 { width: 500px; height: 500px; background: radial-gradient(ellipse, rgba(91,214,255,.07) 0%, transparent 70%); top: 20%; right: -100px; }
.stButton > button { background: var(--grad-brand); color: #011a10 !important; font-weight: 700; border-radius: 10px; border: none; padding: 10px 20px; box-shadow: 0 8px 30px -8px var(--brand-glow); width: 100%; cursor: pointer; }
div[data-baseweb="select"] > div { background: #020409 !important; border: 1px solid var(--border2) !important; border-radius: 10px !important; color: #fff !important; }
.stDataFrame { border: 1px solid var(--border); border-radius: 12px; }
</style>
<div class="bg-orb bg-orb-1"></div><div class="bg-orb bg-orb-2"></div>
"""
def get_custom_css(): return FULL_CSS
def result_tag(res):
    c, b = ("#2EE6A6","rgba(46,230,166,.1)") if res=="W" else (("#F5B93C","rgba(245,185,60,.1)") if res=="D" else ("#FF5A6E","rgba(255,90,110,.1)"))
    l = "V" if res=="W" else ("E" if res=="D" else "D")
    return f'<span style="display:inline-block;min-width:25px;text-align:center;padding:2px 6px;border-radius:4px;font-family:monospace;font-weight:800;font-size:.7rem;background:{b};color:{c};">{l}</span>'
def prob_bar_html(label, value, color=COLOR_BRAND):
    p = max(0, min(100, value * 100))
    return f'<div class="prob-row"><div class="prob-label">{label}</div><div class="prob-track"><div class="prob-fill" style="width:{p}%;background:{color};"></div></div><div class="prob-pct">{p:.1f}%</div></div>'
def alert_card_html(text, color=COLOR_BRAND, emoji="⚡"):
    cls = "alert-card medium" if color=="#F5B93C" else "alert-card"
    return f'<div class="{cls}">{emoji} {text}</div>'
def header_html(season="2025/26", meta_info=""):
    return f'<div class="header-inner"><div class="logo"><div class="logo-icon"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#021a12" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg></div><div class="logo-text">kick<span class="brand-cursor">dex</span></div></div><div style="display:flex;align-items:center;gap:15px;"><span class="season-badge">🟢 {season}</span><span class="meta-info">{meta_info}</span></div></div>'
