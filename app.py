import json
import io
import base64
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_cookies_controller import CookieController

from leadhunter import db, messages, pipeline, ai_agent
from leadhunter.sources import SECTORS
from leadhunter.welcome import render_welcome

st.set_page_config(
    page_title="LeadHunter AI — Conexión Humana + Inteligencia de Prospección",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar Logo Oficial de Marca
LOGO_BRAND_PATH = Path(__file__).parent / "assets" / "logo_brand.png"
LOGO_B64 = ""
if LOGO_BRAND_PATH.exists():
    LOGO_B64 = f"data:image/png;base64,{base64.b64encode(LOGO_BRAND_PATH.read_bytes()).decode('utf-8')}"

# -----------------------------------------------------------------------------
# PALETA DE COLORES CORPORATIVA (Manual de Identidad y Sistema Visual)
# Obsidian Black: #050B14 | Deep Navy: #0B1329 | Electric Blue: #0055FF | Pure White: #FFFFFF
# -----------------------------------------------------------------------------
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');

:root {
    --lh-bg: #f3f4f6;
    --lh-bg-soft: #eef2f7;
    --lh-panel: #ffffff;
    --lh-panel-soft: #f8fafc;
    --lh-sidebar: #f7f8fa;
    --lh-border: rgba(15, 23, 42, 0.08);
    --lh-text: #0f172a;
    --lh-text-soft: #334155;
    --lh-muted: #64748b;
    --lh-brand: #2563eb;
    --lh-brand-strong: #1d4ed8;
    --lh-shadow: 0 18px 38px rgba(15, 23, 42, 0.08);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: var(--lh-bg);
    color: var(--lh-text);
    line-height: 1.5;
}

.stApp, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, var(--lh-bg) 0%, var(--lh-bg-soft) 100%) !important;
    color: var(--lh-text) !important;
}

main .block-container {
    max-width: 1600px !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] {
    background: var(--lh-sidebar) !important;
    border-right: 1px solid var(--lh-border) !important;
    box-shadow: none !important;
    width: 270px !important;
    min-width: 270px !important;
}

[data-testid="stSidebar"] * {
    color: var(--lh-text) !important;
}

h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.03em !important;
    color: var(--lh-text) !important;
}

p, li, span, div, strong, em, label {
    color: var(--lh-text) !important;
}

button, input, textarea, select, [data-baseweb="select"] {
    transition: all 0.2s ease-in-out !important;
}

.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--lh-brand-strong) 0%, var(--lh-brand) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.18) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 16px 28px rgba(37, 99, 235, 0.22) !important;
}

[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 10px 8px !important;
    margin: 0 !important;
    max-width: 100% !important;
}

[data-testid="stChatMessage"] .stMarkdownContainer {
    background: rgba(255, 255, 255, 0.92) !important;
    border: 1px solid var(--lh-border) !important;
    border-radius: 18px !important;
    padding: 16px 18px !important;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04) !important;
    color: var(--lh-text) !important;
    max-width: min(82%, 860px) !important;
}

[data-testid="stChatMessage"] .stMarkdownContainer p,
[data-testid="stChatMessage"] .stMarkdownContainer li,
[data-testid="stChatMessage"] .stMarkdownContainer strong,
[data-testid="stChatMessage"] .stMarkdownContainer span,
[data-testid="stChatMessage"] .stMarkdownContainer em,
[data-testid="stChatMessage"] .stMarkdownContainer a,
[data-testid="stChatMessage"] .stMarkdownContainer h1,
[data-testid="stChatMessage"] .stMarkdownContainer h2,
[data-testid="stChatMessage"] .stMarkdownContainer h3,
[data-testid="stChatMessage"] .stMarkdownContainer h4,
[data-testid="stChatMessage"] .stMarkdownContainer code {
    color: var(--lh-text) !important;
}

[data-testid="stChatMessage"] .stMarkdownContainer code {
    background: rgba(37, 99, 235, 0.08) !important;
    border: 1px solid rgba(37, 99, 235, 0.14) !important;
    border-radius: 8px !important;
    padding: 0.16rem 0.42rem !important;
}

[data-testid="stChatMessage"] .stMarkdownContainer pre {
    background: #f8fafc !important;
    border: 1px solid var(--lh-border) !important;
    border-radius: 12px !important;
    padding: 12px 14px !important;
    overflow-x: auto !important;
}

section[data-testid="stChatInput"],
div[data-testid="stChatInput"] {
    background: #0b1329 !important;
    border: 1px solid rgba(148, 163, 184, 0.32) !important;
    border-radius: 18px !important;
    min-height: 76px !important;
    padding: 8px 10px !important;
    box-shadow: 0 16px 36px rgba(11, 19, 41, 0.18) !important;
    width: min(100%, 900px) !important;
    margin: 0 auto !important;
}

section[data-testid="stChatInput"] *,
div[data-testid="stChatInput"] * {
    background-color: #0b1329 !important;
    color: #f8fafc !important;
}

section[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea,
section[data-testid="stChatInput"] input,
div[data-testid="stChatInput"] input,
section[data-testid="stChatInput"] [data-baseweb="textarea"],
div[data-testid="stChatInput"] [data-baseweb="textarea"],
section[data-testid="stChatInput"] [data-baseweb="base-input"],
div[data-testid="stChatInput"] [data-baseweb="base-input"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
    min-height: 46px !important;
    font-size: 1rem !important;
    padding: 8px 10px !important;
}

section[data-testid="stChatInput"] textarea::placeholder,
div[data-testid="stChatInput"] textarea::placeholder {
    color: #cbd5e1 !important;
    -webkit-text-fill-color: #cbd5e1 !important;
}

section[data-testid="stChatInput"] button,
div[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, var(--lh-brand-strong) 0%, var(--lh-brand) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    width: 54px !important;
    min-width: 54px !important;
    height: 54px !important;
    padding: 0 !important;
    box-shadow: 0 12px 20px rgba(37, 99, 235, 0.18) !important;
}

section[data-testid="stChatInput"] button *,
div[data-testid="stChatInput"] button * {
    background: transparent !important;
    color: #ffffff !important;
}

.chat-feed {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 4px 0;
}

[data-testid="stChatMessage"] {
    max-width: 900px !important;
    margin: 0 auto !important;
    padding: 8px 12px !important;
}

[data-testid="stChatMessage"] .stMarkdownContainer {
    max-width: 100% !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 8px 2px !important;
    box-shadow: none !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdownContainer {
    width: fit-content !important;
    max-width: min(82%, 720px) !important;
    margin-left: auto !important;
    padding: 12px 16px !important;
    background: #0b1329 !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 18px 18px 4px 18px !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdownContainer p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdownContainer li,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdownContainer strong,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdownContainer em {
    color: #f8fafc !important;
}

@media (max-width: 700px) {
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdownContainer {
        max-width: 94% !important;
    }
}

.chat-loading {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.9);
    border: 1px solid var(--lh-border);
}

.chat-loading span {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--lh-brand);
    display: inline-block;
    animation: chatPulse 1.2s ease-in-out infinite;
}

.chat-loading span:nth-child(2) { animation-delay: 0.12s; }
.chat-loading span:nth-child(3) { animation-delay: 0.24s; }

@keyframes chatPulse {
    0%, 80%, 100% { opacity: 0.35; transform: translateY(0); }
    40% { opacity: 1; transform: translateY(-2px); }
}
</style>""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# ESTADO DE SESIÓN (AUTENTICACIÓN, ONBOARDING Y PERFILES)
# -----------------------------------------------------------------------------
if "auth_screen" not in st.session_state:
    st.session_state.auth_screen = "welcome"  # "welcome", "login", "signup", "onboarding", "plans", "workspace"

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Iniciar sesión"

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "first_name": "Usuario",
        "last_name": "",
        "age": 32,
        "email": "",
        "role": "Fundador",
        "companies": []
    }

if "onboarding_companies" not in st.session_state:
    st.session_state.onboarding_companies = [
        {"name": "Novus Ops", "niche": "Desarrollo Web y Software", "goal": "Conseguir 10 clientes al mes"}
    ]


def badge(score):
    c, l = ("#00E5BE", "Alto") if score >= 70 else ("#FF9457", "Medio") if score >= 40 else ("#94A3B8", "Bajo")
    return f"<span class='pill' style='background:{c}1A;color:{c};border-color:{c}'>{score}/100 · {l}</span>"


SCORE_COL = st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")


def parse(raw, default):
    try:
        return json.loads(raw) if raw else default
    except Exception:
        return default


def get_user_display_name(profile=None):
    profile = profile or st.session_state.get("user_profile", {})
    first = (profile.get("first_name") or "").strip()
    last = (profile.get("last_name") or "").strip()
    name = f"{first} {last}".strip()
    return name or "Usuario"


def persist_user_profile(profile=None):
    profile = profile or st.session_state.get("user_profile", {})
    email = str(profile.get("email") or "").strip().lower()
    if not email:
        return profile

    saved = db.upsert_user(
        email=email,
        first_name=(profile.get("first_name") or "").strip(),
        last_name=(profile.get("last_name") or "").strip(),
        role=(profile.get("role") or "").strip(),
        age=int(profile.get("age") or 0),
    )
    if saved:
        profile["first_name"] = saved.get("first_name") or profile.get("first_name") or "Usuario"
        profile["last_name"] = saved.get("last_name") or profile.get("last_name") or ""
        profile["role"] = saved.get("role") or profile.get("role") or "Fundador"
        profile["age"] = int(saved.get("age") or profile.get("age") or 0)
    return profile


def export_leads_excel(df):
    """Genera archivo Excel (.xlsx) nativo con formato comercial y evidencias limpias."""
    if df.empty:
        return b""
    out_df = df.copy()

    def clean_json_list(val):
        try:
            items = json.loads(val) if isinstance(val, str) else val
            return "\n".join(f"• {x}" for x in items) if isinstance(items, list) else str(items or "")
        except Exception:
            return str(val or "")

    if "evidence" in out_df.columns:
        out_df["evidence"] = out_df["evidence"].apply(clean_json_list)
    if "inferences" in out_df.columns:
        out_df["inferences"] = out_df["inferences"].apply(clean_json_list)

    col_map = {
        "id": "ID Lead",
        "name": "Nombre de Empresa",
        "score": "Score (0-100)",
        "status": "Estado Comercial",
        "sector": "Sector",
        "city": "Ciudad",
        "country": "País",
        "phone": "Teléfono",
        "email": "Email",
        "linkedin": "LinkedIn",
        "instagram": "Instagram",
        "website": "Sitio Web",
        "address": "Dirección",
        "evidence": "Evidencias Observadas",
        "notes": "Notas Comerciales",
        "diagnosis": "Diagnóstico detectado",
        "outreach": "Mensaje de primer contacto",
        "next_followup": "Próximo Seguimiento",
        "source": "Fuente"
    }
    cols_to_keep = [c for c in col_map.keys() if c in out_df.columns]
    export_df = out_df[cols_to_keep].rename(columns=col_map)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Prospectos B2B")
    return buf.getvalue()


def export_leads_csv(df):
    """Genera CSV con codificación UTF-8 BOM para apertura perfecta en Excel y Google Sheets."""
    if df.empty:
        return b""
    out_df = df.copy()
    drop_cols = [c for c in ["dedupe_key", "score_detail"] if c in out_df.columns]
    return out_df.drop(columns=drop_cols).to_csv(index=False).encode("utf-8-sig")


db.connect().close()

SESSION_COOKIE_NAME = "leadhunter_remembered_session"
SESSION_COOKIE_SECURE = any(
    os.getenv(name, "").lower() == "production"
    for name in ("APP_ENV", "ENVIRONMENT")
)
cookie_controller = CookieController(key="leadhunter_auth_cookies")


def save_remembered_session(email):
    token = db.create_remembered_session(email, ttl_days=30)
    cookie_controller.set(
        SESSION_COOKIE_NAME,
        token,
        max_age=30 * 24 * 60 * 60,
        secure=SESSION_COOKIE_SECURE,
        same_site="lax",
    )


def clear_remembered_session():
    token = cookie_controller.get(SESSION_COOKIE_NAME)
    if token:
        db.revoke_remembered_session(token)
        cookie_controller.remove(
            SESSION_COOKIE_NAME,
            secure=SESSION_COOKIE_SECURE,
            same_site="lax",
        )


def load_authenticated_user(user):
    st.session_state.user_profile["email"] = user["email"]
    st.session_state.user_profile["first_name"] = (user.get("first_name") or "Usuario").strip()
    st.session_state.user_profile["last_name"] = (user.get("last_name") or "").strip()
    st.session_state.user_profile["role"] = (user.get("role") or "Fundador").strip()
    st.session_state.user_profile["age"] = int(user.get("age") or 0)
    st.session_state.auth_screen = "workspace" if user.get("first_name") else "onboarding"


# =============================================================================
# VENTANA 1: LOGIN Y ACCESO INICIAL (AUTH GATE)
# =============================================================================
remembered_token = cookie_controller.get(SESSION_COOKIE_NAME)
if remembered_token and st.session_state.auth_screen in {"welcome", "login", "signup"}:
    remembered_user = db.get_user_by_remembered_session(remembered_token)
    if remembered_user:
        load_authenticated_user(remembered_user)
    else:
        clear_remembered_session()

persisted_user = None
if st.session_state.get("user_profile", {}).get("email"):
    persisted_user = db.get_user_by_email(st.session_state.user_profile["email"])
    if persisted_user:
        st.session_state.user_profile["first_name"] = persisted_user.get("first_name") or st.session_state.user_profile.get("first_name") or "Usuario"
        st.session_state.user_profile["last_name"] = persisted_user.get("last_name") or st.session_state.user_profile.get("last_name") or ""
        st.session_state.user_profile["role"] = persisted_user.get("role") or st.session_state.user_profile.get("role") or "Fundador"
        st.session_state.user_profile["age"] = int(persisted_user.get("age") or st.session_state.user_profile.get("age") or 0)

welcome_action = st.query_params.get("welcome_action")
if welcome_action in {"welcome", "login", "signup"}:
    st.session_state.auth_screen = welcome_action
    if welcome_action in {"login", "signup"}:
        st.session_state.auth_mode = "Crear cuenta" if welcome_action == "signup" else "Iniciar sesión"
    del st.query_params["welcome_action"]

if st.session_state.auth_screen == "welcome":
    render_welcome()

elif st.session_state.auth_screen in {"login", "signup"}:
    c_left, c_center, c_right = st.columns([1, 2, 1])
    with c_center:
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        
        # Logo Centrado
        if LOGO_B64:
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="{LOGO_B64}" style="max-width: 240px; filter: drop-shadow(0 0 25px rgba(0, 85, 255, 0.4));">
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align: center;">
            <div class="brand-title">Lead hunter</div>
            <div class="brand-subtitle">expande tu cartera de clientes</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='text-align:center; margin: 8px 0 18px;'><a href='?welcome_action=welcome'>← Volver al inicio</a></div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='dark-card'>", unsafe_allow_html=True)
            
            # Opción 1: Continuar con Google
            if st.button("🌐 Continuar con Google", use_container_width=True):
                st.session_state.user_profile["email"] = "usuario.google@ejemplo.com"
                persist_user_profile()
                st.session_state.auth_screen = "onboarding"
                st.rerun()

            st.markdown("""
            <div style="display: flex; align-items: center; margin: 18px 0; color: #64748B;">
                <div style="flex: 1; height: 1px; background: rgba(255, 255, 255, 0.1);"></div>
                <span style="padding: 0 12px; font-size: 0.8rem; text-transform: uppercase;">o con tu correo</span>
                <div style="flex: 1; height: 1px; background: rgba(255, 255, 255, 0.1);"></div>
            </div>
            """, unsafe_allow_html=True)

            auth_mode = st.segmented_control(
                "Acceso",
                ["Iniciar sesión", "Crear cuenta"],
                label_visibility="collapsed",
                key="auth_mode",
                width="stretch",
            )

            if auth_mode == "Iniciar sesión":
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                login_email = st.text_input("Correo Electrónico", value="", key="login_email_input")
                login_pass = st.text_input("Contraseña", type="password", value="", key="login_pass_input")
                remember_login = st.checkbox(
                    "Recordarme en este dispositivo durante 30 días",
                    key="remember_login_checkbox",
                )
                
                if st.button("Ingresar a mi Workspace →", type="primary", use_container_width=True):
                    email = (login_email or "").strip().lower()
                    if not email or not login_pass:
                        st.warning("Ingresa tu correo y contraseña para continuar.")
                    else:
                        user = db.authenticate_user(email, login_pass)
                        if not user:
                            st.warning("Credenciales incorrectas. Revisa tu correo o contraseña.")
                        else:
                            if remember_login:
                                save_remembered_session(email)
                            else:
                                clear_remembered_session()
                            load_authenticated_user(user)
                            st.rerun()

            elif auth_mode == "Crear cuenta":
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                signup_email = st.text_input("Tu Correo Electrónico", placeholder="nombre@tuempresa.com", key="signup_email_input")
                signup_pass = st.text_input("Crea una Contraseña segura", type="password", key="signup_pass_input")
                remember_signup = st.checkbox(
                    "Recordarme en este dispositivo durante 30 días",
                    key="remember_signup_checkbox",
                )
                
                if st.button("Crear Cuenta y Configurar Negocios →", type="primary", use_container_width=True):
                    email = (signup_email or "").strip().lower()
                    if not email:
                        st.warning("Ingresa un correo válido.")
                    elif len((signup_pass or "")) < 8:
                        st.warning("La contraseña debe tener al menos 8 caracteres.")
                    else:
                        existing = db.get_user_by_email(email)
                        if existing and existing.get("password_hash"):
                            st.warning("Este correo ya existe. Inicia sesión con tu contraseña.")
                            st.session_state.auth_mode = "Iniciar sesión"
                            st.rerun()
                        else:
                            db.create_user_account(email, signup_pass)
                            if remember_signup:
                                save_remembered_session(email)
                            else:
                                clear_remembered_session()
                            st.session_state.user_profile["email"] = email
                            st.session_state.user_profile["first_name"] = ""
                            st.session_state.user_profile["last_name"] = ""
                            st.session_state.user_profile["role"] = "Fundador"
                            st.session_state.user_profile["age"] = 32
                            persist_user_profile()
                            st.session_state.auth_screen = "onboarding"
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# VENTANA 2: ONBOARDING (PERFIL PERSONAL + CONFIGURACIÓN MULTI-EMPRESA)
# =============================================================================
elif st.session_state.auth_screen == "onboarding":
    c_l, c_main, c_r = st.columns([1, 2.5, 1])
    with c_main:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <div class="brand-title" style="font-size: 2.2rem;">Bienvenido a LeadHunter AI</div>
            <div class="brand-subtitle">Paso 1 de 2: Configura tu perfil y las empresas que deseas prospectar</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='dark-card'>", unsafe_allow_html=True)
        st.markdown("### 👤 Tus Datos Personales")
        st.caption("Información utilizada para personalizar los borradores y propuestas comerciales.")
        
        c1, c2 = st.columns(2)
        f_name = c1.text_input("Nombre", value=st.session_state.user_profile.get("first_name", "Carlos"))
        l_name = c2.text_input("Apellido", value=st.session_state.user_profile.get("last_name", "Gómez"))
        
        c3, c4 = st.columns(2)
        age = c3.number_input("Edad", min_value=18, max_value=99, value=int(st.session_state.user_profile.get("age", 30)))
        role = c4.text_input("Cargo o Rol", value="Director Comercial / Fundador", placeholder="Ej: CEO, Consultor, Ventas")

        st.markdown("---")
        st.markdown("### 🏢 Tus Empresas y Marcas")
        st.caption("Indica la empresa o empresas para las que buscarás clientes. Cada una tendrá su base de leads 100% aislada.")

        # Manejador de empresas dinámicas
        num_comps = len(st.session_state.onboarding_companies)
        updated_comps = []

        for i, comp in enumerate(st.session_state.onboarding_companies):
            with st.expander(f"Empresa #{i+1}: {comp.get('name') or 'Nueva Empresa'}", expanded=True):
                col_c1, col_c2 = st.columns(2)
                c_name = col_c1.text_input(f"Nombre de la empresa #{i+1}", value=comp.get("name", ""), key=f"ob_cname_{i}", placeholder="Ej: Novus Ops")
                
                niche_options = [
                    "Desarrollo Web y Software",
                    "Producción Audiovisual y Fotografía",
                    "Marketing Digital y Captación",
                    "Construcción e Inmobiliaria",
                    "Asesoría Legal y Fiscal",
                    "Salud y Clínicas Especializadas",
                    "Consultoría Estratégica",
                    "Otro"
                ]
                cur_niche = comp.get("niche", niche_options[0])
                idx_n = niche_options.index(cur_niche) if cur_niche in niche_options else 0
                c_niche = col_c2.selectbox(f"Nicho o sector #{i+1}", niche_options, index=idx_n, key=f"ob_cniche_{i}")

                c_goal = st.text_input(
                    f"Meta comercial para {c_name or f'esta empresa'}",
                    value=comp.get("goal", "Conseguir 10 clientes al mes"),
                    key=f"ob_cgoal_{i}",
                    placeholder="Ej: Conseguir 10 clientes al mes, prospectar constructoras de alto ticket"
                )

                updated_comps.append({"name": c_name, "niche": c_niche, "goal": c_goal})

        st.session_state.onboarding_companies = updated_comps

        col_btn_add, col_empty = st.columns([1, 1])
        if col_btn_add.button("+ Agregar otra empresa"):
            st.session_state.onboarding_companies.append({
                "name": f"Empresa {len(st.session_state.onboarding_companies)+1}",
                "niche": "Desarrollo Web y Software",
                "goal": "Conseguir 10 clientes al mes"
            })
            st.rerun()

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("Guardar Configuración y Continuar a Planes →", type="primary", use_container_width=True):
            valid_comps = [c for c in st.session_state.onboarding_companies if c["name"].strip()]
            if not valid_comps:
                st.error("Por favor ingresa al menos el nombre de una empresa.")
            else:
                st.session_state.user_profile["first_name"] = f_name
                st.session_state.user_profile["last_name"] = l_name
                st.session_state.user_profile["age"] = age
                st.session_state.user_profile["role"] = role
                st.session_state.user_profile["companies"] = valid_comps
                persist_user_profile()
                
                # Registrar empresas en la base de datos
                for c in valid_comps:
                    db.register_business(c["name"].strip())
                st.session_state.active_business = valid_comps[0]["name"].strip()
                
                st.session_state.auth_screen = "plans"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# VENTANA 3: RECOMENDACIÓN DE PLANES (PLACEHOLDER ELEGANTE)
# =============================================================================
elif st.session_state.auth_screen == "plans":
    c_l, c_main, c_r = st.columns([1, 3, 1])
    with c_main:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <div class="brand-title" style="font-size: 2.2rem;">Planes de Prospección B2B</div>
            <div class="brand-subtitle">Selecciona el plan configurado según tus metas de crecimiento</div>
        </div>
        """, unsafe_allow_html=True)

        p1, p2, p3 = st.columns(3)

        with p1:
            st.markdown("""
            <div class="dark-card" style="border: 2px solid #0055FF; box-shadow: 0 0 25px rgba(0, 85, 255, 0.25);">
                <span class="pill" style="background: rgba(0, 85, 255, 0.2); color: #70A1FF; border-color: #0055FF;">RECOMENDADO</span>
                <h3 style="margin-top: 10px;">Early Adopter (MVP)</h3>
                <p style="font-size: 1.8rem; font-weight: 800; color: #FFFFFF; font-family: 'Outfit';">$0 <span style="font-size: 0.9rem; color: #94A3B8;">/ mes</span></p>
                <p style="font-size: 0.85rem; color: #94A3B8;">Acceso completo para validar y cerrar tus primeros clientes.</p>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                <ul style="font-size: 0.8rem; color: #E2E8F0; padding-left: 15px; line-height: 1.8;">
                    <li>✓ Asistente IA de Nicho e ICP</li>
                    <li>✓ Scraping y scoring en tiempo real</li>
                    <li>✓ Gestión Multi-Empresa incluida</li>
                    <li>✓ Exportación a Excel (.xlsx) y CSV</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Comenzar con este Plan →", type="primary", use_container_width=True):
                st.session_state.auth_screen = "workspace"
                st.rerun()

        with p2:
            st.markdown("""
            <div class="dark-card" style="opacity: 0.75;">
                <span class="pill" style="background: rgba(255, 255, 255, 0.1); color: #94A3B8; border-color: rgba(255,255,255,0.2);">PRÓXIMAMENTE</span>
                <h3 style="margin-top: 10px;">Growth Pro</h3>
                <p style="font-size: 1.8rem; font-weight: 800; color: #FFFFFF; font-family: 'Outfit';">$49 <span style="font-size: 0.9rem; color: #94A3B8;">/ mes</span></p>
                <p style="font-size: 0.85rem; color: #94A3B8;">Para agencias que buscan prospección recurrente automatizada.</p>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                <ul style="font-size: 0.8rem; color: #94A3B8; padding-left: 15px; line-height: 1.8;">
                    <li>• Búsquedas programadas automáticas</li>
                    <li>• Enriquecimiento con email corporativo</li>
                    <li>• Hasta 5 empresas activas</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            st.button("Configurar después", disabled=True, use_container_width=True)

        with p3:
            st.markdown("""
            <div class="dark-card" style="opacity: 0.75;">
                <span class="pill" style="background: rgba(255, 255, 255, 0.1); color: #94A3B8; border-color: rgba(255,255,255,0.2);">ENTERPRISE</span>
                <h3 style="margin-top: 10px;">Scale Unlimited</h3>
                <p style="font-size: 1.8rem; font-weight: 800; color: #FFFFFF; font-family: 'Outfit';">$149 <span style="font-size: 0.9rem; color: #94A3B8;">/ mes</span></p>
                <p style="font-size: 0.85rem; color: #94A3B8;">Solución ilimitada para equipos y múltiples agentes de venta.</p>
                <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
                <ul style="font-size: 0.8rem; color: #94A3B8; padding-left: 15px; line-height: 1.8;">
                    <li>• Empresas ilimitadas</li>
                    <li>• Acceso API y Webhooks</li>
                    <li>• Soporte prioritario dedicado</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            st.button("Contactar Ventas", disabled=True, use_container_width=True)


# =============================================================================
# VENTANA 4: WORKSPACE PRINCIPAL (APLICACIÓN LEADHUNTER AI CON NUEVA ESTÉTICA)
# =============================================================================
elif st.session_state.auth_screen == "workspace":

    # ------------------------------------------------------------ Sidebar
    with st.sidebar:
        if LOGO_B64:
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <img src="{LOGO_B64}" style="width: 100%; max-width: 220px; filter: drop-shadow(0 0 15px rgba(0, 85, 255, 0.3));">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='brand-title' style='font-size: 1.5rem;'>Lead <span>Hunter</span></div>", unsafe_allow_html=True)

        # Perfil del usuario activo
        user_p = st.session_state.user_profile
        full_name = get_user_display_name(user_p)
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 10px 14px; margin-bottom: 16px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #FFFFFF;">👤 {full_name}</div>
            <div style="font-size: 0.75rem; color: #94A3B8;">{user_p.get('role', 'Comercial')} · <span style="color: #70A1FF;">Early Adopter</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🏢 Empresa Activa")
        available_biz = db.get_available_businesses()
        
        # Añadir las empresas del usuario si no están en available_biz
        for uc in user_p.get("companies", []):
            if uc["name"] and uc["name"] not in available_biz:
                available_biz.append(uc["name"])

        if "active_business" not in st.session_state or not st.session_state.active_business:
            st.session_state.active_business = available_biz[0] if available_biz else "Mi Empresa"

        if st.session_state.active_business not in available_biz:
            available_biz.append(st.session_state.active_business)

        idx = available_biz.index(st.session_state.active_business) if st.session_state.active_business in available_biz else 0
        business = st.selectbox(
            "Espacio de trabajo",
            available_biz,
            index=idx,
            help="Cada empresa gestiona sus leads y configuraciones de forma 100% aislada."
        )
        st.session_state.active_business = business

        with st.expander("+ Agregar otra empresa"):
            st.caption("Gestiona múltiples marcas o proyectos separando sus prospectos:")
            new_name = st.text_input("Nombre de la nueva empresa", key="new_biz_input_ws", placeholder="Ej: NTO Media")
            if st.button("Crear y cambiar a esta empresa") and new_name.strip():
                db.register_business(new_name.strip())
                st.session_state.active_business = new_name.strip()
                st.success(f"Empresa '{new_name.strip()}' activada y guardada.")
                st.rerun()

        st.markdown("---")
        page = st.radio("Navegación", [
            "🤖 Asistente IA (Orientación + Prospección)",
            "📋 Leads Guardados",
            "🔎 Búsqueda Manual",
            "📊 Dashboard",
            "📁 Importar CSV",
            "⏰ Programación"
        ])
        st.markdown("---")
        
        sender = st.text_input("Tu nombre (para mensajes)", value=get_user_display_name(user_p))
        name_parts = sender.strip().split()
        st.session_state.user_profile["first_name"] = name_parts[0] if name_parts else "Usuario"
        st.session_state.user_profile["last_name"] = " ".join(name_parts[1:])
        persist_user_profile()
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            clear_remembered_session()
            st.session_state.user_profile = {
                "first_name": "Usuario",
                "last_name": "",
                "age": 32,
                "email": "",
                "role": "Fundador",
                "companies": [],
            }
            st.session_state.onboarding_companies = [
                {"name": "Novus Ops", "niche": "Desarrollo Web y Software", "goal": "Conseguir 10 clientes al mes"}
            ]
            st.session_state.pop("active_business", None)
            st.session_state.chat_history = []
            st.session_state.auth_screen = "welcome"
            st.rerun()

    # ---------------------------------------------------------------- Asistente IA (Orientación + Prospección)
    if page == "🤖 Asistente IA (Orientación + Prospección)":
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        elif (
            len(st.session_state.chat_history) == 1
            and st.session_state.chat_history[0].get("role") == "assistant"
            and st.session_state.chat_history[0].get("content", "").startswith(
                "👋 ¡Hola! Soy tu asistente de prospección comercial para **"
            )
        ):
            st.session_state.chat_history = []

        quick_prompts = {
            "Web en Santo Domingo": "Ofrezco desarrollo web, software a medida y páginas corporativas en Santo Domingo. ¿A qué nicho debo venderle?",
            "Video y fotografía": "Hago producción de video profesional y contenido multimedia en Santo Domingo. ¿Quién es mi cliente ideal?",
            "Marketing en CDMX": "Ofrezco marketing digital, pauta publicitaria y captación de clientes en Ciudad de México. ¿Qué sector me conviene?",
            "Legal y finanzas": "Presto servicios de asesoría contable, legal y fiscal para empresas en Madrid. ¿Qué nicho tiene mayor demanda?",
            "Constructoras · Santo Domingo": "Encuentra constructoras en Santo Domingo con proyectos activos y presencia digital mejorable.",
            "Inmobiliarias · Madrid": "Busca agencias inmobiliarias en Madrid para ofrecerles producción audiovisual.",
            "Clínicas dentales · CDMX": "Encuentra clínicas dentales en Ciudad de México que puedan requerir optimización de captación."
        }
        selected_suggestion = None
        if not st.session_state.chat_history:
            st.markdown(f"## 👋 Hola, {get_user_display_name(st.session_state.user_profile)}", text_alignment="center")
            st.markdown("## :material/auto_awesome: ¿En qué puedo ayudarte?", text_alignment="center")
            st.caption(
                "Cuéntame qué ofreces y dónde, o elige una consulta para empezar.",
                text_alignment="center"
            )
            selected_suggestion = st.pills(
                "Consultas de ejemplo",
                options=list(quick_prompts),
                selection_mode="single",
                label_visibility="collapsed",
                key="chat_suggestions"
            )

        # Renderizar historial
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "table" in msg and msg["table"] is not None:
                    st.dataframe(msg["table"], use_container_width=True, hide_index=True, column_config={"score": SCORE_COL})
                if "download_df" in msg and msg["download_df"] is not None and not msg["download_df"].empty:
                    d_df = msg["download_df"]
                    c_d1, c_d2 = st.columns(2)
                    c_d1.download_button(
                        "⬇ Descargar esta búsqueda en Excel (.xlsx)",
                        export_leads_excel(d_df),
                        f"prospectos_{business.replace(' ', '_')}_{date.today()}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_xl_{msg.get('key_id', id(msg))}"
                    )
                    c_d2.download_button(
                        "⬇ Descargar esta búsqueda en CSV",
                        export_leads_csv(d_df),
                        f"prospectos_{business.replace(' ', '_')}_{date.today()}.csv",
                        "text/csv",
                        key=f"dl_csv_{msg.get('key_id', id(msg))}"
                    )
        user_input = st.chat_input("Escribe qué vendes o qué buscas...")
        pending_prompt = st.session_state.pop("pending_chat_prompt", None)
        final_prompt = quick_prompts.get(selected_suggestion) or user_input or pending_prompt

        if final_prompt:
            st.session_state.chat_history.append({"role": "user", "content": final_prompt})
            with st.chat_message("user"):
                st.markdown(final_prompt)

            business_profile = next(
                (company for company in st.session_state.user_profile.get("companies", []) if company.get("name") == business),
                {},
            )
            service_profile = business_profile.get("niche") or business_profile.get("goal", "")
            intent = ai_agent.detect_intent(final_prompt)

            with st.chat_message("assistant"):
                if intent == "general":
                    response_text = ai_agent.reply_general(final_prompt)
                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})

                elif intent == "advice":
                    # Flujo 1: Orientación Estratégica de Nicho / ICP
                    with st.spinner("Analizando tu oferta y evaluando qué nicho tiene mayor necesidad y capacidad de pago..."):
                        advice = ai_agent.advise_icp(final_prompt)
                        sector_rec = advice.get("recommended_sector", "Constructoras")
                        city_rec = advice.get("target_city", "Santo Domingo")
                        country_rec = advice.get("target_country", "República Dominicana")
                        pains = advice.get("pain_points", [])

                        response_text = (
                            "## Análisis estratégico de cliente ideal (ICP)\n\n"
                            f"**Nicho recomendado:** {sector_rec}\n"
                            f"**Mercado objetivo:** {city_rec}, {country_rec}\n\n"
                            f"**¿Por qué este nicho?** {advice.get('reasoning', 'No se identificó aún una razón clara.')}\n\n"
                            "**Puntos débiles clave a atacar:**\n"
                            + (
                                "\n".join(f"- {p}" for p in pains)
                                if pains
                                else "- No se identificaron puntos específicos todavía."
                            )
                            + f"\n\n**Gancho de contacto sugerido:**\n> {advice.get('suggested_pitch', 'No disponible por ahora.') }"
                        )
                        st.markdown(response_text)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response_text,
                            "ready_prompt": advice.get("ready_search_prompt")
                        })

                        if st.button(f"🔎 Buscar {sector_rec} en {city_rec} ahora", type="primary"):
                            st.session_state.pending_chat_prompt = f"Busca {sector_rec} en {city_rec}"
                            st.rerun()

                else:
                    with st.status("Preparando prospección…", expanded=True) as search_status:
                        progress_bar = st.progress(0.0, text="Buscando empresas en fuentes públicas…")

                        def report_progress(progress_value, message):
                            progress_bar.progress(min(max(progress_value, 0.0), 1.0), text=message)
                            search_status.update(label=message)

                        result = ai_agent.run_conversational_search(
                            business=business,
                            prompt=final_prompt,
                            service_profile=service_profile,
                            sender=sender,
                            progress_callback=report_progress,
                        )
                        progress_bar.empty()
                        search_status.update(
                            label=f"Análisis completo · {len(result['leads'])} prospectos calificados",
                            state="complete",
                        )

                    interp = result["interpretation"]
                    prospects_df = pd.DataFrame(result["leads"])
                    table_columns = [
                        "name", "score", "website", "email", "phone", "linkedin",
                        "instagram", "diagnosis", "outreach",
                    ]
                    if not prospects_df.empty:
                        prospects_df = prospects_df[[column for column in table_columns if column in prospects_df.columns]]
                        display_df = prospects_df.rename(columns={
                            "name": "Empresa",
                            "score": "Score",
                            "website": "Sitio web",
                            "email": "Email",
                            "phone": "Teléfono",
                            "linkedin": "LinkedIn",
                            "instagram": "Instagram",
                            "diagnosis": "Diagnóstico",
                            "outreach": "Mensaje sugerido",
                        })
                        summary_text = (
                            f"**Prospección terminada para {interp['sector']} en {interp['city']}, {interp['country']}.**  \n"
                            f"Encontré **{len(prospects_df)}** prospectos que superaron los filtros; "
                            f"{result['new_leads']} son nuevos y {result['existing_leads']} ya estaban guardados."
                        )
                    else:
                        display_df = None
                        summary_text = (
                            f"No encontré prospectos que superaran los criterios de calificación para "
                            f"{interp['sector']} en {interp['city']}, {interp['country']}. "
                            "Prueba ampliar la ubicación o ajustar el servicio y el sector."
                        )

                    if result["errors"]:
                        summary_text += f"\n\n*Fuentes con limitaciones:* {'; '.join(result['errors'])}"
                    st.markdown(summary_text)
                    if display_df is not None:
                        st.dataframe(
                            display_df,
                            width="stretch",
                            hide_index=True,
                            column_config={"Score": SCORE_COL},
                        )

                    key_id = f"gen_{datetime.now().timestamp()}"
                    if not prospects_df.empty:
                        c_d1, c_d2 = st.columns(2)
                        c_d1.download_button(
                            "⬇ Descargar resultados en Excel (.xlsx)",
                            export_leads_excel(prospects_df),
                            f"leads_{business.replace(' ', '_')}_{date.today()}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"btn_xl_{key_id}"
                        )
                        c_d2.download_button(
                            "⬇ Descargar resultados en CSV",
                            export_leads_csv(prospects_df),
                            f"leads_{business.replace(' ', '_')}_{date.today()}.csv",
                            "text/csv",
                            key=f"btn_csv_{key_id}"
                        )

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": summary_text,
                        "table": display_df,
                        "download_df": prospects_df if not prospects_df.empty else None,
                        "key_id": key_id,
                    })

    # ---------------------------------------------------------------- Leads Guardados
    elif page == " Leads Guardados":
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.1rem;">Leads Guardados · <span style="color: #70A1FF;">{business}</span></h1>
            <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
                Gestiona tus prospectos calificados, notas internas, fechas de seguimiento y exportación con 1 clic.
            </p>
        </div>
        """, unsafe_allow_html=True)

        f1, f2, f3 = st.columns([2, 1, 1])
        text = f1.text_input("Filtrar por nombre / ciudad / sector", placeholder="Buscar...")
        status = f2.selectbox("Estado comercial", ["Todos"] + db.STATUSES)
        minscore = f3.slider("Score mínimo de oportunidad", 0, 100, 0)

        df = db.leads_df(business, status, minscore, text)

        # Botones destacados de exportación
        c_exp1, c_exp2 = st.columns(2)
        c_exp1.download_button(
            "⬇ Descargar Leads en Excel (.xlsx)",
            export_leads_excel(df),
            f"leads_{business.replace(' ', '_')}_{date.today()}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        c_exp2.download_button(
            "⬇ Descargar Leads en CSV (Excel compatible)",
            export_leads_csv(df),
            f"leads_{business.replace(' ', '_')}_{date.today()}.csv",
            "text/csv",
            use_container_width=True
        )

        st.markdown(f"**Total prospectos guardados:** {len(df)}")
        st.dataframe(
            df[["id", "name", "sector", "city", "score", "status", "email", "phone", "instagram", "website", "next_followup"]],
            use_container_width=True, hide_index=True, column_config={"score": SCORE_COL}
        )

        if len(df):
            st.markdown("---")
            label = {int(r.id): f"{r.score:>3} · {r.name} ({r.city})" for r in df.itertuples()}
            lid = st.selectbox("Abrir ficha del lead", list(label), format_func=lambda i: label[i])
            lead = db.get_lead(lid)
            sd = parse(lead["score_detail"], {})

            st.markdown(f"### {lead['name']}")
            st.markdown(badge(lead["score"]), unsafe_allow_html=True)

            left, right = st.columns(2)
            with left:
                st.markdown("**Desglose del score de oportunidad**")
                for k, v in sd.get("detail", {}).items():
                    st.progress(min(v / {"Encaje": 30, "Capacidad (est.)": 20, "Necesidad": 25, "Actividad": 15, "Calidad de datos": 10}.get(k, 20), 1.0), f"{k}: {v}")

                st.markdown("** Evidencias verificadas en la web**")
                ev_list = parse(lead["evidence"], [])
                for e in ev_list:
                    st.markdown(f"<span class='tag-v'>●</span> {e}", unsafe_allow_html=True)
                if not ev_list:
                    st.caption("No se detectaron evidencias críticas o la web no cuenta con portal activo.")

                st.markdown("** Inferencias comerciales**")
                for e in parse(lead["inferences"], []):
                    st.markdown(f"<span class='tag-i'>●</span> {e}", unsafe_allow_html=True)

                if not lead["analyzed"]:
                    st.caption("Web sin analizar o inaccesible.")

            with right:
                st.markdown(f" **Web:** {lead['website'] or '—'}  \n📞 **Tel:** {lead['phone'] or '—'}  \n✉️ **Email:** {lead['email'] or '—'}  \n"
                            f" **Instagram:** {lead['instagram'] or '—'}  \n📍 **Ubicación:** {lead['address'] or lead['city']}  \nFuente: {lead['source']}")

                new_st = st.selectbox("Estado", db.STATUSES, index=db.STATUSES.index(lead["status"]))
                notes = st.text_area("Notas internas", value=lead["notes"] or "", height=80)
                follow = st.date_input("Próximo seguimiento", value=datetime.strptime(lead["next_followup"], "%Y-%m-%d").date() if lead["next_followup"] else None)

                if st.button("Guardar cambios en ficha", type="primary"):
                    db.update_lead_crm(lid, new_st, notes, follow.isoformat() if follow else None)
                    st.success("Ficha actualizada con éxito.")
                    st.rerun()

            st.markdown("---")
            st.markdown("####  Borrador personalizado para prospección")
            preview = messages.draft_preview(lead, business, sender)
            msg_txt = st.text_area("Borrador listo para copiar:", value=preview, height=140)
            
            c_msg1, c_msg2 = st.columns(2)
            if c_msg1.button(" Marcar como Contactado"):
                db.update_lead_crm(lid, "Contactado", notes, follow.isoformat() if follow else None)
                st.success("Lead actualizado a Contactado.")
                st.rerun()

    # ---------------------------------------------------------------- Búsqueda Manual
    elif page == "🔎 Búsqueda Manual":
        st.markdown(f"<h1>Búsqueda Manual Avanzada · <span style='color: #70A1FF;'>{business}</span></h1>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        country = c1.text_input("País", "República Dominicana")
        city = c2.text_input("Ciudad", "Santo Domingo")
        sector = c3.selectbox("Sector comercial", SECTORS)

        c4, c5 = st.columns(2)
        sources = c4.multiselect("Fuentes de datos", ["OpenStreetMap", "DuckDuckGo"], default=["OpenStreetMap", "DuckDuckGo"])
        max_r = c5.slider("Límite de resultados", 5, 50, 20)

        if st.button("Ejecutar Búsqueda y Analizar Sitios", type="primary"):
            bar = st.progress(0.0, "Consultando fuentes…")
            new, old, errs = pipeline.run_search(
                business=business, country=country, city=city, sector=sector,
                use_sources=sources, max_results=max_r,
                progress=lambda p, m: bar.progress(p, m)
            )
            bar.empty()
            st.success(f"Búsqueda finalizada: {new} nuevos prospectos, {old} ya existentes.")
            if errs:
                st.warning("Avisos: " + "; ".join(errs))

    # ---------------------------------------------------------------- Dashboard
    elif page == "Dashboard":
        st.markdown(f"<h1>Métricas de Prospección · <span style='color: #70A1FF;'>{business}</span></h1>", unsafe_allow_html=True)
        df_all = db.leads_df(business)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Prospectos", len(df_all))
        m2.metric("Alta Oportunidad (Score ≥ 70)", len(df_all[df_all["score"] >= 70]))
        m3.metric("Contactados", len(df_all[df_all["status"] == "Contactado"]))
        m4.metric("Reuniones", len(df_all[df_all["status"] == "Reunión"]))

    # ---------------------------------------------------------------- Importar CSV
    elif page == "Importar CSV":
        st.markdown(f"<h1>Importar Leads desde CSV · <span style='color: #70A1FF;'>{business}</span></h1>", unsafe_allow_html=True)
        st.caption("Carga un archivo CSV con columnas: name, website, phone, email, etc.")
        up = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
        if up and st.button("Procesar e Importar", type="primary"):
            added, dups = pipeline.import_csv(up, business)
            st.success(f"Importación completada: {added} nuevos prospectos, {dups} duplicados ignorados.")

    # ---------------------------------------------------------------- Programación
    elif page == "Programación":
        st.markdown(f"<h1>Búsquedas Programadas · <span style='color: #70A1FF;'>{business}</span></h1>", unsafe_allow_html=True)
        st.caption("Configura búsquedas recurrentes que se ejecuten automáticamente en segundo plano.")
        st.info("Para activar la ejecución automática diaria en Windows, usa el archivo 'run_scheduled.bat' en el Programador de Tareas.")
