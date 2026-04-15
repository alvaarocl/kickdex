"""
Landing page — primera visita. Muestra explicación + CTA grande.
Controlada por st.session_state.show_landing.
"""

import streamlit as st

from app.i18n import t


LANDING_CSS = """
<style>
.kdx-landing {
    max-width: 1100px;
    margin: 0 auto;
    padding: 40px 20px 60px;
}
.kdx-logo {
    font-size: 5.2rem;
    font-weight: 900;
    letter-spacing: -2px;
    background: linear-gradient(135deg, #00d4aa 0%, #7c4dff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0;
    line-height: 1;
}
.kdx-title {
    text-align: center;
    font-size: 2.1rem !important;
    color: #e8eaf6 !important;
    margin-top: 8px !important;
    margin-bottom: 6px !important;
    font-weight: 700;
}
.kdx-subtitle {
    text-align: center;
    color: #8b9ab0 !important;
    font-size: 1.05rem;
    margin-bottom: 42px;
}
.kdx-features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 18px;
    margin-bottom: 50px;
}
.kdx-feature {
    background: linear-gradient(135deg, #1a1f2e 0%, #151925 100%);
    border: 1px solid #2a3040;
    border-radius: 14px;
    padding: 22px 20px;
    transition: transform 0.18s, border-color 0.18s;
}
.kdx-feature:hover {
    transform: translateY(-3px);
    border-color: #00d4aa55;
}
.kdx-feature h4 {
    color: #00d4aa !important;
    font-size: 1.05rem !important;
    margin: 0 0 10px 0 !important;
    font-weight: 700;
}
.kdx-feature p {
    color: #b0bec5 !important;
    font-size: 0.88rem !important;
    line-height: 1.5;
    margin: 0 !important;
}
.kdx-cta-wrap { text-align: center; margin: 10px 0 30px; }
.kdx-footer {
    text-align: center;
    color: #8b9ab0 !important;
    font-size: 0.78rem;
    margin-top: 30px;
}
/* Mega button override */
div[data-testid="stButton"] button.kdx-mega,
.kdx-cta-wrap div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #00d4aa 0%, #0097a7 100%) !important;
    border: none !important;
    color: #0e1117 !important;
    font-size: 1.3rem !important;
    font-weight: 900 !important;
    letter-spacing: 1px !important;
    padding: 22px 60px !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 30px rgba(0, 212, 170, 0.35) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.kdx-cta-wrap div[data-testid="stButton"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 40px rgba(0, 212, 170, 0.5) !important;
}
</style>
"""


def render() -> None:
    """Renderiza la landing. Pulsa el botón → guarda state y recarga."""
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="kdx-landing">
            <div class="kdx-logo">KICKDEX</div>
            <h1 class="kdx-title">{t("landing_title")}</h1>
            <p class="kdx-subtitle">{t("landing_subtitle")}</p>
            <div class="kdx-features">
                <div class="kdx-feature">
                    <h4>{t("landing_f1_title")}</h4>
                    <p>{t("landing_f1_body")}</p>
                </div>
                <div class="kdx-feature">
                    <h4>{t("landing_f2_title")}</h4>
                    <p>{t("landing_f2_body")}</p>
                </div>
                <div class="kdx-feature">
                    <h4>{t("landing_f3_title")}</h4>
                    <p>{t("landing_f3_body")}</p>
                </div>
                <div class="kdx-feature">
                    <h4>{t("landing_f4_title")}</h4>
                    <p>{t("landing_f4_body")}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kdx-cta-wrap">', unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button(t("landing_cta"), type="primary", use_container_width=True, key="landing_start"):
            st.session_state.show_landing = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="kdx-footer">{t("landing_footer")}</div>',
        unsafe_allow_html=True,
    )
