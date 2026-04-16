"""
Tab 🛬 Landing Page — Diseño Premium usando componentes nativos + CSS.
"""

import streamlit as st
from app.i18n import t

def render():
    # El CSS ya está inyectado globalmente desde styles.py
    st.markdown('<div style="text-align:center; margin-bottom:20px;">', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size: 5rem; font-weight: 900; background: linear-gradient(135deg, #2EE6A6 0%, #5BD6FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.2;">KICKDEX</h1>', unsafe_allow_html=True)
    st.markdown(f'<h2 style="font-size: 2rem; font-weight: 700; color: #F1F5FB; margin-top:-10px;">{t("landing_title")}</h2>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size: 1.1rem; color: #8A94AB; margin-bottom: 40px;">{t("landing_subtitle")}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Grid de features usando st.columns (para evitar que falle el HTML)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="card" style="padding:25px; margin-bottom:15px;">
            <h4 style="color:#2EE6A6; margin-top:0;">{t('landing_f1_title')}</h4>
            <p style="color:#8A94AB; font-size:0.9rem;">{t('landing_f1_body')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card" style="padding:25px;">
            <h4 style="color:#2EE6A6; margin-top:0;">{t('landing_f3_title')}</h4>
            <p style="color:#8A94AB; font-size:0.9rem;">{t('landing_f3_body')}</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card" style="padding:25px; margin-bottom:15px;">
            <h4 style="color:#2EE6A6; margin-top:0;">{t('landing_f2_title')}</h4>
            <p style="color:#8A94AB; font-size:0.9rem;">{t('landing_f2_body')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card" style="padding:25px;">
            <h4 style="color:#2EE6A6; margin-top:0;">{t('landing_f4_title')}</h4>
            <p style="color:#8A94AB; font-size:0.9rem;">{t('landing_f4_body')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botón CTA
    if st.button(t('landing_cta'), use_container_width=True):
        st.session_state.show_landing = False
        st.rerun()

    st.markdown(f'<p style="text-align:center; color:#6B7A97; font-size:.78rem; margin-top:30px;">{t("landing_footer")}</p>', unsafe_allow_html=True)
