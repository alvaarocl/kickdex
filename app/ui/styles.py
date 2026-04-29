"""
Estilos Core Premium para KICKDEX — Terminal de Datos Institucional.
Replica exactamente la estética de la web estática (OLED Dark, Glassmorphism).
"""
COLOR_BG, COLOR_BRAND, COLOR_BRAND2, COLOR_GOLD = "#05070D", "#2EE6A6", "#5BD6FF", "#F5B93C"
FULL_CSS = """
<style>
/* ── Reset & variables ── */
:root { --bg:#05070D; --bg1:#0B0F1A; --bg2:#111728; --brand:#2EE6A6; --brand2:#5BD6FF; --brand-soft:rgba(46,230,166,.1); --brand-glow:rgba(46,230,166,.4); --border:rgba(255,255,255,.05); --border2:rgba(255,255,255,.1); --text:#F1F5FB; --muted:#8A94AB; --grad-brand:linear-gradient(135deg,#2EE6A6 0%,#5BD6FF 100%); --grad-card:linear-gradient(160deg,rgba(17,23,40,.85) 0%,rgba(11,15,26,.92) 100%); }

/* ── Smooth scroll global ── */
html { scroll-behavior: smooth; }

/* ── Keyframes ── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(28px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes floatOrb {
  0%,100% { transform: translateY(0) scale(1); }
  50%      { transform: translateY(-40px) scale(1.06); }
}
@keyframes floatOrb2 {
  0%,100% { transform: translateY(0) scale(1); }
  50%      { transform: translateY(30px) scale(.97); }
}
@keyframes pulseGlow {
  0%,100% { filter: drop-shadow(0 0 18px rgba(46,230,166,.5)); }
  50%      { filter: drop-shadow(0 0 60px rgba(46,230,166,.9)) drop-shadow(0 0 120px rgba(91,214,255,.4)); }
}
@keyframes shimmerText {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}
@keyframes ctaPulse {
  0%,100% { box-shadow: 0 8px 30px -8px rgba(46,230,166,.5); }
  50%      { box-shadow: 0 8px 50px 0px rgba(46,230,166,.9), 0 0 80px rgba(91,214,255,.3); }
}

/* ── Page transition ── */
.main .block-container { animation: fadeIn .45s ease-out; }

/* ── App shell ── */
.stApp { background: var(--bg); color: var(--text); font-family: sans-serif; }
header[data-testid="stHeader"], [data-testid="stSidebarNav"], #MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
.main .block-container { padding-top: 0 !important; max-width: 1380px !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: #04060e; border-bottom: 1px solid var(--border); padding: 10px 20px 0; position: sticky; top: 0; z-index: 90; }
.stTabs [data-baseweb="tab"] { height: 45px; color: var(--muted); font-size: .8rem; font-weight: 600; background: none !important; border: none !important; transition: color .2s; }
.stTabs [aria-selected="true"] { color: var(--brand) !important; border-bottom: 2px solid var(--brand) !important; background: rgba(255,255,255,.03) !important; }

/* ── Header ── */
.header-inner { display: flex; align-items: center; justify-content: space-between; height: 70px; border-bottom: 1px solid var(--border); padding: 0 20px; margin-bottom: 20px; }
.logo { display: flex; align-items: center; gap: 10px; font-size: 1.3rem; font-weight: 700; color: #fff; }
.logo-icon { width: 34px; height: 34px; background: var(--grad-brand); border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.brand-cursor { color: var(--brand); font-family: monospace; }
.season-badge { background: var(--brand-soft); color: var(--brand); border: 1px solid rgba(0,212,170,.2); padding: 4px 12px; border-radius: 99px; font-size: .7rem; }
.meta-info { color: var(--muted); font-size: .7rem; font-family: monospace; }

/* ── Cards ── */
.card { background: var(--grad-card); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 20px; }
.section-title { font-size: .9rem; font-weight: 700; color: #fff; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
.section-h2 { font-size: 1.3rem; font-weight: 800; color: #fff; margin-bottom: 5px; }
.section-desc { font-size: .85rem; color: var(--muted); margin-bottom: 20px; }

/* ── Landing ── */
.landing-root { min-height: 100vh; display: flex; flex-direction: column; }
.landing-hero { text-align: center; padding: 80px 20px 60px; animation: fadeInUp .8s ease-out both; }
.landing-logo-text {
  font-size: clamp(4rem, 10vw, 7rem); font-weight: 900; letter-spacing: -2px; line-height: 1;
  background: linear-gradient(135deg, #2EE6A6 0%, #5BD6FF 40%, #2EE6A6 80%);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  animation: shimmerText 4s linear infinite, pulseGlow 3s ease-in-out infinite;
  display: block;
}
.landing-tagline { font-size: clamp(1.1rem, 2.5vw, 1.6rem); font-weight: 700; color: var(--text); margin-top: 16px; animation: fadeInUp .8s .15s ease-out both; }
.landing-sub { font-size: clamp(.85rem, 1.5vw, 1rem); color: var(--muted); margin-top: 10px; animation: fadeInUp .8s .25s ease-out both; }
.landing-stats { display: flex; justify-content: center; gap: clamp(20px, 4vw, 60px); margin: 40px 0; flex-wrap: wrap; animation: fadeInUp .8s .35s ease-out both; }
.landing-stat { text-align: center; }
.landing-stat-num { font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 900; font-family: monospace; background: var(--grad-brand); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.landing-stat-label { font-size: .75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
.landing-cta-wrap { animation: fadeInUp .8s .45s ease-out both; margin: 10px auto 60px; max-width: 420px; }
.landing-features { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; padding: 0 0 60px; }
.landing-feat { background: var(--grad-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; opacity: 0; animation: fadeInUp .7s ease-out forwards; transition: border-color .2s, transform .2s; }
.landing-feat:nth-child(1) { animation-delay: .5s; }
.landing-feat:nth-child(2) { animation-delay: .65s; }
.landing-feat:nth-child(3) { animation-delay: .8s; }
.landing-feat:nth-child(4) { animation-delay: .95s; }
.landing-feat:nth-child(5) { animation-delay: 1.1s; }
.landing-feat:nth-child(6) { animation-delay: 1.25s; }
.landing-feat:hover { border-color: rgba(46,230,166,.25); transform: translateY(-3px); }
.landing-feat-icon { font-size: 1.8rem; margin-bottom: 12px; }
.landing-feat-title { font-size: .95rem; font-weight: 800; color: var(--brand); margin-bottom: 8px; }
.landing-feat-body { font-size: .82rem; color: var(--muted); line-height: 1.5; }
.landing-footer { text-align: center; color: #4a5568; font-size: .72rem; padding-bottom: 30px; animation: fadeIn 1s 1.4s ease-out both; }

/* ── Botón CTA ── */
.stButton > button {
  background: var(--grad-brand) !important; color: #011a10 !important; font-weight: 800 !important;
  border-radius: 14px !important; border: none !important;
  animation: ctaPulse 2.5s ease-in-out infinite !important;
  transition: transform .15s, filter .15s !important; width: 100% !important;
}
.stButton > button:hover { transform: translateY(-2px) scale(1.02) !important; filter: brightness(1.1) !important; }

/* ── Background orbs animados ── */
.bg-orb { position: fixed; border-radius: 50%; filter: blur(90px); pointer-events: none; z-index: -1; }
.bg-orb-1 { width: 700px; height: 450px; background: radial-gradient(ellipse, rgba(0,212,170,.12) 0%, transparent 70%); top: -120px; left: -150px; animation: floatOrb 12s ease-in-out infinite; }
.bg-orb-2 { width: 600px; height: 600px; background: radial-gradient(ellipse, rgba(91,214,255,.08) 0%, transparent 70%); top: 20%; right: -150px; animation: floatOrb2 15s ease-in-out infinite; }
.bg-orb-3 { width: 400px; height: 400px; background: radial-gradient(ellipse, rgba(167,139,250,.06) 0%, transparent 70%); bottom: 10%; left: 30%; animation: floatOrb 18s 3s ease-in-out infinite; }

/* ── Comparador ── */
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

/* ── Calculadora Maestra ── */
.calc-box { background: linear-gradient(160deg,rgba(17,23,40,.95) 0%,rgba(11,15,26,.98) 100%); border: 1px solid rgba(46,230,166,.3); border-radius: 16px; padding: 24px; margin-top: 20px; }
.calc-title { font-size: 1rem; font-weight: 800; color: var(--brand); margin-bottom: 4px; }

/* ── Inicio / Fixtures ── */
.fx-card { background: var(--grad-card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 10px; }
.fx-row { display: flex; align-items: center; justify-content: space-between; }
.fx-league-badge { font-size: .6rem; font-weight: 800; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; }
.fx-league-badge.sp1 { background: rgba(46,230,166,.1); color: var(--brand); }
.fx-league-badge.sp2 { background: rgba(91,214,255,.1); color: var(--brand2); }
.fx-team { font-weight: 700; color: #fff; font-size: .95rem; }
.fx-score { font-family: monospace; font-weight: 800; color: var(--brand); background: rgba(46,230,166,.1); padding: 2px 8px; border-radius: 4px; }

/* ── Árbitros badges ── */
.ref-badge-high { background: rgba(255,90,110,.12); color: #FF5A6E; border: 1px solid rgba(255,90,110,.3); padding: 2px 8px; border-radius: 20px; font-size: .65rem; font-weight: 800; }
.ref-badge-low { background: rgba(46,230,166,.12); color: var(--brand); border: 1px solid rgba(46,230,166,.3); padding: 2px 8px; border-radius: 20px; font-size: .65rem; font-weight: 800; }
.ref-badge-med { background: rgba(245,185,60,.1); color: #F5B93C; border: 1px solid rgba(245,185,60,.3); padding: 2px 8px; border-radius: 20px; font-size: .65rem; font-weight: 800; }

/* ── Selects & misc ── */
div[data-baseweb="select"] > div { background: #020409 !important; border: 1px solid var(--border2) !important; border-radius: 10px !important; color: #fff !important; }
.stDataFrame { border: 1px solid var(--border); border-radius: 12px; }
.disclaimer { font-size: .72rem; color: #4a5568; margin-top: 20px; padding: 12px; border-top: 1px solid var(--border); }
.players-col-title { font-size: .85rem; font-weight: 700; color: var(--brand); margin-bottom: 8px; }
</style>
<div class="bg-orb bg-orb-1"></div>
<div class="bg-orb bg-orb-2"></div>
<div class="bg-orb bg-orb-3"></div>
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
