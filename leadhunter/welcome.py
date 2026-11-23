from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def render_welcome() -> None:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.svg"
    logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")

    st.html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        body:has(.lh-welcome) [data-testid="stSidebar"],
        body:has(.lh-welcome) [data-testid="stHeader"] {{
            display: none !important;
        }}

        body:has(.lh-welcome) main .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
        }}

        .lh-welcome {{
            --welcome-ink: #ffffff;
            --welcome-muted: #94a3b8;
            --welcome-blue: #3b82f6;
            position: relative;
            isolation: isolate;
            min-height: 100vh;
            overflow: hidden;
            padding: 18px clamp(22px, 5vw, 76px) 56px;
            background: linear-gradient(180deg, #070b14 0%, #0a0f1d 100%);
            color: var(--welcome-ink) !important;
            font-family: 'Inter', sans-serif;
        }}

        .lh-welcome::before {{
            position: absolute;
            z-index: -1;
            content: '';
            left: 18%;
            right: 18%;
            bottom: 1%;
            height: 48%;
            opacity: 0.38;
            filter: blur(90px);
            background: linear-gradient(90deg, transparent, #1e40af 28%, #3b82f6 50%, #1e40af 72%, transparent);
            pointer-events: none;
        }}

        .lh-welcome::after {{
            position: absolute;
            z-index: -1;
            content: '';
            inset: 0;
            opacity: 0.14;
            background-image: linear-gradient(rgba(148, 163, 184, 0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.09) 1px, transparent 1px);
            background-size: 64px 64px;
            mask-image: linear-gradient(to bottom, black, transparent 78%);
            pointer-events: none;
        }}

        .lh-welcome a {{
            color: #ffffff !important;
            text-decoration: none !important;
        }}

        .lh-nav {{
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            max-width: 1400px;
            min-height: 56px;
            margin: 0 auto;
            padding: 0 18px;
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 14px;
            background: rgba(5, 8, 15, 0.78);
            backdrop-filter: blur(16px);
        }}

        .lh-brand {{ display: flex; align-items: center; gap: 10px; white-space: nowrap; }}
        .lh-brand img {{ width: 30px; height: 30px; filter: brightness(0) invert(1); }}
        .lh-brand-name {{ color: #fff !important; font-size: 14px; font-weight: 700; }}
        .lh-brand-name span {{ color: #60a5fa !important; }}
        .lh-nav-links {{ display: flex; align-items: center; gap: clamp(16px, 2.5vw, 34px); }}
        .lh-nav-links a {{ color: #aab4c5 !important; font-size: 11px; transition: color 180ms ease; }}
        .lh-nav-links a:hover {{ color: #fff !important; }}
        .lh-nav-links a:first-child {{ display: flex; align-items: center; gap: 7px; color: #fff !important; }}
        .lh-nav-links a:first-child::before {{ width: 5px; height: 5px; border-radius: 50%; background: #3b82f6; content: ''; }}
        .lh-nav-actions {{ display: flex; justify-content: flex-end; align-items: center; gap: 20px; white-space: nowrap; }}
        .lh-welcome .lh-nav-login {{ color: #cbd5e1 !important; font-size: 11px; }}
        .lh-nav-cta {{ padding: 9px 15px; border-radius: 999px; background: #fff; color: #0a0f1d !important; font-size: 11px; font-weight: 700; transition: transform 180ms ease, box-shadow 180ms ease; }}
        .lh-welcome .lh-nav-cta {{ color: #0a0f1d !important; }}
        .lh-nav-cta:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(255,255,255,0.2); }}

        .lh-hero-grid {{
            display: grid;
            grid-template-columns: minmax(140px, 0.8fr) minmax(440px, 2.2fr) minmax(140px, 0.8fr);
            align-items: center;
            gap: 28px;
            max-width: 1220px;
            margin: 46px auto 42px;
        }}

        .lh-metrics {{ display: grid; align-content: center; gap: 52px; }}
        .lh-metric {{ display: grid; gap: 7px; }}
        .lh-metrics-right .lh-metric {{ text-align: right; }}
        .lh-metric-value {{ color: #fff !important; font-family: 'Instrument Serif', serif; font-size: 32px; line-height: 1; }}
        .lh-metric-label {{ color: #64748b !important; font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.08em; line-height: 1.5; }}

        .lh-hero-copy {{ text-align: center; }}
        .lh-eyebrow {{ display: inline-flex; align-items: center; gap: 8px; margin-bottom: 20px; color: #94a3b8 !important; font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; }}
        .lh-eyebrow i {{ width: 6px; height: 6px; border-radius: 50%; background: #60a5fa; box-shadow: 0 0 12px rgba(96,165,250,0.9); }}
        .lh-hero-copy h1 {{ max-width: 760px; margin: 0 auto; color: #fff !important; font-family: 'Instrument Serif', Georgia, serif !important; font-size: clamp(50px, 6vw, 76px) !important; font-weight: 400 !important; line-height: 1.02 !important; letter-spacing: 0 !important; }}
        .lh-hero-copy h1 em {{ color: #fff !important; font-weight: 400; }}
        .lh-hero-copy h1 .lh-accent {{ color: #60a5fa !important; }}
        .lh-hero-copy p {{ max-width: 550px; margin: 18px auto 0; color: #94a3b8 !important; font-size: 14px; line-height: 1.75; }}
        .lh-hero-actions {{ display: flex; justify-content: center; gap: 12px; margin-top: 26px; }}
        .lh-hero-button {{ display: inline-flex; align-items: center; justify-content: center; min-height: 42px; padding: 0 19px; border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 999px; color: #dbeafe !important; font-size: 11px; font-weight: 600; transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease; }}
        .lh-welcome .lh-hero-button {{ color: #dbeafe !important; }}
        .lh-hero-button:hover {{ transform: translateY(-2px); border-color: rgba(96,165,250,0.65); box-shadow: 0 8px 24px rgba(59,130,246,0.2); }}
        .lh-hero-button-primary {{ border-color: transparent; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #fff !important; box-shadow: 0 8px 24px rgba(30,64,175,0.28); }}
        .lh-welcome .lh-hero-button-primary {{ color: #fff !important; }}

        .lh-preview-wrap {{ position: relative; max-width: 1250px; margin: 0 auto; scroll-margin-top: 32px; }}
        .lh-preview-kicker {{ margin: 0 0 12px 4px; color: #64748b !important; font-family: 'JetBrains Mono', monospace; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; }}
        .lh-preview-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; align-items: center; gap: 18px; perspective: 1300px; }}
        .lh-product-card {{ min-width: 0; min-height: 270px; padding: 20px; border: 1px solid rgba(59, 130, 246, 0.22); border-radius: 13px; background: rgba(16, 23, 42, 0.78); box-shadow: 0 22px 65px rgba(0,0,0,0.28); backdrop-filter: blur(16px); transition: transform 240ms ease, border-color 240ms ease, box-shadow 240ms ease; }}
        .lh-product-card:hover {{ transform: translateY(-5px) !important; border-color: rgba(96,165,250,0.55); box-shadow: 0 28px 70px rgba(14,48,116,0.3); }}
        .lh-card-leads {{ transform: perspective(1000px) rotateY(7deg) translateY(12px); }}
        .lh-card-timeline {{ transform: perspective(1000px) rotateY(-7deg) translateY(12px); }}
        .lh-card-center {{ position: relative; z-index: 1; min-height: 290px; border-color: rgba(96,165,250,0.4); background: rgba(16, 23, 42, 0.9); }}
        .lh-card-heading {{ display: flex; align-items: center; gap: 8px; margin-bottom: 18px; color: #cbd5e1 !important; font-size: 11px; font-weight: 600; }}
        .lh-card-heading i {{ width: 6px; height: 6px; border-radius: 50%; background: #60a5fa; box-shadow: 0 0 10px rgba(96,165,250,0.8); }}
        .lh-lead-row {{ display: grid; grid-template-columns: 27px minmax(0, 1fr) auto; align-items: center; gap: 9px; min-height: 43px; border-bottom: 1px solid rgba(148,163,184,0.09); }}
        .lh-lead-row:last-child {{ border-bottom: 0; }}
        .lh-avatar {{ display: grid; width: 25px; height: 25px; place-items: center; border: 1px solid rgba(96,165,250,0.28); border-radius: 50%; background: rgba(59,130,246,0.12); color: #bfdbfe !important; font-size: 9px; font-weight: 600; }}
        .lh-lead-name {{ overflow: hidden; color: #e2e8f0 !important; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }}
        .lh-lead-status {{ padding: 4px 7px; border: 1px solid rgba(96,165,250,0.22); border-radius: 999px; color: #93c5fd !important; font-size: 8px; white-space: nowrap; }}
        .lh-lead-status-muted {{ border-color: rgba(148,163,184,0.16); color: #94a3b8 !important; }}
        .lh-score-line {{ display: flex; align-items: baseline; gap: 10px; }}
        .lh-score-number {{ color: #fff !important; font-family: 'Instrument Serif', serif; font-size: 58px; line-height: 1; }}
        .lh-score-max {{ color: #64748b !important; font-size: 10px; }}
        .lh-agent-pill {{ display: inline-flex; align-items: center; gap: 6px; margin: 12px 0 4px; padding: 6px 9px; border: 1px solid rgba(59,130,246,0.25); border-radius: 999px; background: rgba(59,130,246,0.1); color: #bfdbfe !important; font-size: 9px; }}
        .lh-agent-pill i {{ width: 5px; height: 5px; border-radius: 50%; background: #60a5fa; box-shadow: 0 0 8px #3b82f6; }}
        .lh-chart {{ display: block; width: 100%; height: 98px; margin-top: 8px; overflow: visible; }}
        .lh-timeline-hours {{ display: grid; grid-template-columns: repeat(5, 1fr); margin: 2px 0 15px; color: #64748b !important; font-family: 'JetBrains Mono', monospace; font-size: 8px; }}
        .lh-timeline-hours span:last-child {{ text-align: right; }}
        .lh-timeline {{ position: relative; display: grid; gap: 16px; }}
        .lh-timeline::after {{ position: absolute; top: -4px; bottom: -5px; left: 58%; width: 1px; background: #60a5fa; box-shadow: 0 0 10px #3b82f6; content: ''; }}
        .lh-task {{ display: grid; grid-template-columns: 76px 1fr; align-items: center; gap: 8px; }}
        .lh-task-name {{ color: #94a3b8 !important; font-size: 9px; }}
        .lh-task-track {{ position: relative; height: 11px; border-radius: 3px; background: rgba(148,163,184,0.08); }}
        .lh-task-bar {{ position: absolute; top: 0; height: 11px; border-radius: 3px; background: linear-gradient(90deg, #1e40af, #3b82f6); }}
        .lh-task-bar-light {{ background: linear-gradient(90deg, #2563eb, #60a5fa); }}
        .lh-demo-note {{ margin: 16px 0 0; color: #64748b !important; font-family: 'JetBrains Mono', monospace; font-size: 8px; letter-spacing: 0.04em; text-align: center; }}

        @media (max-width: 1050px) {{
            .lh-hero-grid {{ grid-template-columns: 1fr; gap: 26px; margin: 40px auto 34px; }}
            .lh-metrics {{ display: flex; justify-content: center; gap: clamp(26px, 8vw, 80px); }}
            .lh-metric {{ min-width: 120px; }}
            .lh-metrics-right .lh-metric {{ text-align: left; }}
            .lh-hero-copy {{ grid-row: 1; }}
            .lh-metrics-left {{ grid-row: 2; }}
            .lh-metrics-right {{ grid-row: 2; }}
        }}

        @media (max-width: 760px) {{
            .lh-welcome {{ padding: 14px 18px 38px; }}
            .lh-nav {{ grid-template-columns: 1fr auto; padding: 0 12px; }}
            .lh-nav-links {{ display: none; }}
            .lh-nav-actions {{ gap: 12px; }}
            .lh-nav-login {{ font-size: 10px; }}
            .lh-nav-cta {{ padding: 8px 11px; font-size: 10px; }}
            .lh-hero-grid {{ grid-template-columns: 1fr 1fr; gap: 0 12px; margin: 34px auto 28px; }}
            .lh-hero-copy {{ grid-column: 1 / -1; grid-row: 1; margin-bottom: 28px; }}
            .lh-hero-copy h1 {{ font-size: clamp(46px, 12vw, 64px) !important; }}
            .lh-hero-copy p {{ max-width: 420px; font-size: 13px; }}
            .lh-eyebrow {{ margin-bottom: 14px; font-size: 8px; }}
            .lh-metrics {{ display: contents; }}
            .lh-metric {{ min-width: 0; gap: 5px; padding: 12px 8px; text-align: center !important; }}
            .lh-metric-value {{ font-size: 28px; }}
            .lh-metric-label {{ font-size: 8px; }}
            .lh-metrics-left .lh-metric:nth-child(1) {{ grid-column: 1; grid-row: 2; }}
            .lh-metrics-left .lh-metric:nth-child(2) {{ grid-column: 2; grid-row: 2; }}
            .lh-metrics-right .lh-metric:nth-child(1) {{ grid-column: 1; grid-row: 3; }}
            .lh-metrics-right .lh-metric:nth-child(2) {{ grid-column: 2; grid-row: 3; }}
            .lh-preview-grid {{ grid-template-columns: 1fr; gap: 14px; }}
            .lh-product-card, .lh-card-leads, .lh-card-timeline {{ transform: none; }}
            .lh-card-center {{ min-height: 270px; }}
            .lh-preview-kicker {{ margin-left: 0; }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .lh-welcome *, .lh-welcome *::before, .lh-welcome *::after {{ transition-duration: 0.01ms !important; }}
        }}
        </style>

        <div class="lh-welcome">
            <header class="lh-nav">
                <a class="lh-brand" href="#inicio" aria-label="LeadHunter AI, inicio">
                    <img src="data:image/svg+xml;base64,{logo_data}" alt="">
                    <span class="lh-brand-name">LeadHunter <span>AI</span></span>
                </a>
                <nav class="lh-nav-links" aria-label="Navegación principal">
                    <a href="#funciones">Funciones</a>
                    <a href="#agentes">Agentes IA</a>
                    <a href="#empezar">Precios</a>
                    <a href="#como-funciona">Docs</a>
                </nav>
                <div class="lh-nav-actions">
                    <a class="lh-nav-login" href="?welcome_action=login">Iniciar sesión</a>
                    <a class="lh-nav-cta" href="?welcome_action=signup">Empezar gratis</a>
                </div>
            </header>

            <section class="lh-hero-grid" id="inicio">
                <div class="lh-metrics lh-metrics-left">
                    <div class="lh-metric"><span class="lh-metric-value">10×</span><span class="lh-metric-label">PROSPECCIÓN MÁS RÁPIDA</span></div>
                    <div class="lh-metric"><span class="lh-metric-value">92%</span><span class="lh-metric-label">PRECISIÓN DE LEADS</span></div>
                </div>
                <div class="lh-hero-copy">
                    <span class="lh-eyebrow"><i></i> Inteligencia de prospección B2B</span>
                    <h1>Caza <em class="lh-accent">leads B2B</em><br>en <em>piloto automático.</em></h1>
                    <p>Identifica, califica y contacta clientes ideales antes de que tu competencia abra su CRM.</p>
                    <div class="lh-hero-actions" id="empezar">
                        <a class="lh-hero-button lh-hero-button-primary" href="?welcome_action=signup">Probar gratis <span aria-hidden="true">&nbsp;↗</span></a>
                        <a class="lh-hero-button" href="#funciones">Ver demo</a>
                    </div>
                </div>
                <div class="lh-metrics lh-metrics-right">
                    <div class="lh-metric"><span class="lh-metric-value">50K+</span><span class="lh-metric-label">EMPRESAS ANALIZADAS</span></div>
                    <div class="lh-metric"><span class="lh-metric-value">24/7</span><span class="lh-metric-label">AGENTE ACTIVO</span></div>
                </div>
            </section>

            <section class="lh-preview-wrap" id="funciones" aria-label="Vista previa del producto">
                <p class="lh-preview-kicker">LeadHunter workspace · Vista previa</p>
                <div class="lh-preview-grid">
                    <article class="lh-product-card lh-card-leads">
                        <div class="lh-card-heading"><i></i> Leads detectados</div>
                        <div class="lh-lead-row"><span class="lh-avatar">GA</span><span class="lh-lead-name">Grupo Inmobiliario Apex</span><span class="lh-lead-status">Calificado</span></div>
                        <div class="lh-lead-row"><span class="lh-avatar">AM</span><span class="lh-lead-name">AutoMotors RD</span><span class="lh-lead-status lh-lead-status-muted">Contactado</span></div>
                        <div class="lh-lead-row"><span class="lh-avatar">CN</span><span class="lh-lead-name">Clínica Dental Nova</span><span class="lh-lead-status lh-lead-status-muted">En análisis</span></div>
                        <div class="lh-lead-row"><span class="lh-avatar">TL</span><span class="lh-lead-name">TechCorp Latam</span><span class="lh-lead-status">Nuevo</span></div>
                    </article>

                    <article class="lh-product-card lh-card-center" id="agentes">
                        <div class="lh-card-heading"><i></i> Lead Score promedio</div>
                        <div class="lh-score-line"><span class="lh-score-number">96</span><span class="lh-score-max">/ 100 intención de compra</span></div>
                        <span class="lh-agent-pill"><i></i> Agente IA activo</span>
                        <svg class="lh-chart" viewBox="0 0 340 100" role="img" aria-label="Gráfica de intención ascendente">
                            <defs><linearGradient id="leadScoreFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#3b82f6" stop-opacity="0.34"/><stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/></linearGradient></defs>
                            <path d="M0 82 C24 76 25 68 47 72 S75 57 96 63 S124 47 145 54 S173 39 194 45 S222 33 244 38 S272 21 291 29 S322 12 340 15 V100 H0 Z" fill="url(#leadScoreFill)"/>
                            <path d="M0 82 C24 76 25 68 47 72 S75 57 96 63 S124 47 145 54 S173 39 194 45 S222 33 244 38 S272 21 291 29 S322 12 340 15" fill="none" stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round"/>
                            <circle cx="340" cy="15" r="4" fill="#bfdbfe"/>
                        </svg>
                    </article>

                    <article class="lh-product-card lh-card-timeline" id="como-funciona">
                        <div class="lh-card-heading"><i></i> Secuencia de outreach</div>
                        <div class="lh-timeline-hours"><span>09:00</span><span>10:00</span><span>11:00</span><span>12:00</span><span>13:00</span></div>
                        <div class="lh-timeline">
                            <div class="lh-task"><span class="lh-task-name">Extracción</span><span class="lh-task-track"><i class="lh-task-bar" style="left:0;width:42%"></i></span></div>
                            <div class="lh-task"><span class="lh-task-name">Enriquecimiento</span><span class="lh-task-track"><i class="lh-task-bar lh-task-bar-light" style="left:24%;width:48%"></i></span></div>
                            <div class="lh-task"><span class="lh-task-name">Email #1</span><span class="lh-task-track"><i class="lh-task-bar" style="left:45%;width:28%"></i></span></div>
                            <div class="lh-task"><span class="lh-task-name">Follow-up</span><span class="lh-task-track"><i class="lh-task-bar lh-task-bar-light" style="left:64%;width:34%"></i></span></div>
                        </div>
                    </article>
                </div>
                <p class="lh-demo-note">DATOS ILUSTRATIVOS · CADA BÚSQUEDA SE ADAPTA A TU NEGOCIO</p>
            </section>
        </div>
        """,
    )