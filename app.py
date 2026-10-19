import json
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from leadhunter import db, messages, pipeline
from leadhunter.sources import SECTORS

st.set_page_config(page_title="LeadHunter AI", page_icon="🎯", layout="wide")
LOGO = (Path(__file__).parent / "assets" / "logo.svg").read_text()
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
h1,h2,h3,h4{font-family:'Outfit',sans-serif!important;color:#1A202E!important;font-weight:600!important;letter-spacing:-.01em}
.block-container{padding-top:2rem;max-width:1280px}
[data-testid="stSidebar"]{background:#1A202E}
[data-testid="stSidebar"] *{color:#F7F9FC!important}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea{color:#1A202E!important}
[data-testid="stSidebar"] hr{border-color:#ffffff22}
.brand{display:flex;align-items:center;gap:10px;margin:4px 0 14px}
.brand svg{width:40px;height:40px}
.brand span{font-family:'Outfit',sans-serif;font-size:1.35rem;font-weight:700;color:#fff}
.brand b{color:#4D8DFF;font-weight:700}
[data-testid="stMetric"]{background:#fff;border:1px solid #E3E8EF;border-left:4px solid #0056FF;padding:14px 18px;border-radius:12px;box-shadow:0 1px 3px #1a202e0d}
[data-testid="stMetricLabel"]{color:#7A8C99!important}
[data-testid="stDataFrame"]{border:1px solid #E3E8EF;border-radius:12px;overflow:hidden}
.stButton>button,.stDownloadButton>button{border-radius:10px;font-weight:600}
.pill{padding:3px 12px;border-radius:999px;font-weight:600;font-size:.85rem;border:1px solid}
.tag-v{color:#00C2A0;font-weight:700}.tag-i{color:#FF7E45;font-weight:700}
</style>""", unsafe_allow_html=True)


def badge(score):
    c, l = ("#00C2A0", "Alto") if score >= 70 else ("#FF7E45", "Medio") if score >= 40 else ("#7A8C99", "Bajo")
    return f"<span class='pill' style='background:{c}1A;color:{c};border-color:{c}'>{score}/100 · {l}</span>"


SCORE_COL = st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")

db.connect().close()

with st.sidebar:
    st.markdown(f"<div class='brand'>{LOGO.replace('#1A202E', '#F7F9FC')}<span>Lead<b>Hunter</b> AI</span></div>", unsafe_allow_html=True)
    business = st.radio("Negocio", db.BUSINESSES, help="Cada negocio tiene sus leads totalmente separados.")
    page = st.radio("Sección", ["Dashboard", "Buscar", "Leads", "Importar CSV", "Programación"])
    sender = st.text_input("Tu nombre (para mensajes)", value="")
    st.caption("Solo se redactan mensajes: tú los envías personalmente.")


def parse(raw, default):
    try:
        return json.loads(raw) if raw else default
    except Exception:
        return default


# ---------------------------------------------------------------- Dashboard
if page == "Dashboard":
    st.header(f"Dashboard · {business}")
    df = db.leads_df(business)
    due = db.due_followups(business, date.today().isoformat())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leads", len(df))
    c2.metric("Calientes (≥70)", int((df.score >= 70).sum()) if len(df) else 0)
    c3.metric("Score medio", round(df.score.mean()) if len(df) else 0)
    c4.metric("Seguimientos pendientes", len(due))
    if due:
        st.subheader("Seguimientos para hoy o vencidos")
        st.table([{"Empresa": d["name"], "Fecha": d["next_followup"], "Estado": d["status"]} for d in due])
    if len(df):
        st.subheader("Embudo por estado")
        st.bar_chart(df.status.value_counts(), color="#0056FF")
        st.subheader("Top 10 leads")
        st.dataframe(df[["name", "sector", "city", "score", "status", "email", "phone"]].head(10), use_container_width=True,
                     hide_index=True, column_config={"score": SCORE_COL})
    else:
        st.info("Aún no hay leads. Ve a **Buscar** o **Importar CSV**.")

# ---------------------------------------------------------------- Buscar
elif page == "Buscar":
    st.header(f"Buscar empresas · {business}")
    c1, c2, c3 = st.columns(3)
    country = c1.text_input("País", "República Dominicana")
    city = c2.text_input("Ciudad", "Santo Domingo")
    sector = c3.selectbox("Sector", list(SECTORS))
    c4, c5 = st.columns(2)
    use = c4.multiselect("Fuentes gratuitas", ["OpenStreetMap", "DuckDuckGo"], default=["OpenStreetMap", "DuckDuckGo"])
    maxr = c5.slider("Máx. resultados por fuente", 5, 100, 30)
    analyze = st.checkbox("Analizar las webs y puntuar (más lento, con pausas de cortesía)", True)
    cA, cB = st.columns(2)
    if cA.button("🔎 Buscar ahora", type="primary"):
        bar = st.progress(0.0, "Buscando…")
        with st.spinner("Consultando fuentes públicas…"):
            new, old, errs = pipeline.run_search(business, country, city, sector, use, maxr, analyze,
                                                 progress=lambda p, m: bar.progress(p, m))
        bar.empty()
        st.success(f"{new} leads nuevos · {old} ya existían (duplicados omitidos).")
        for e in errs:
            st.warning(e)
        if new + old == 0 and not errs:
            st.info("Las fuentes no devolvieron resultados. Prueba otra ciudad/sector o usa **Importar CSV**.")
        if errs:
            st.info("Si una fuente falla, prueba la otra o importa tus empresas desde CSV.")
    if cB.button("💾 Guardar búsqueda para programarla"):
        db.save_search(business, country, city, sector, use, maxr)
        st.success("Guardada. Ejecútala en la sección Programación.")

# ---------------------------------------------------------------- Leads
elif page == "Leads":
    st.header(f"Leads · {business}")
    f1, f2, f3 = st.columns([2, 1, 1])
    text = f1.text_input("Filtrar por nombre / ciudad / sector")
    status = f2.selectbox("Estado", ["Todos"] + db.STATUSES)
    minscore = f3.slider("Score mínimo", 0, 100, 0)
    df = db.leads_df(business, status, minscore, text)
    st.download_button("⬇️ Exportar CSV", df.drop(columns=["dedupe_key", "score_detail"]).to_csv(index=False).encode("utf-8-sig"),
                       f"leads_{business.replace(' ', '_')}_{date.today()}.csv", "text/csv")
    st.dataframe(df[["id", "name", "sector", "city", "score", "status", "email", "phone", "instagram", "website", "next_followup"]],
                 use_container_width=True, hide_index=True, column_config={"score": SCORE_COL})
    if len(df):
        label = {int(r.id): f"{r.score:>3} · {r.name} ({r.city})" for r in df.itertuples()}
        lid = st.selectbox("Abrir lead", list(label), format_func=lambda i: label[i])
        lead = db.get_lead(lid)
        sd = parse(lead["score_detail"], {})
        st.subheader(lead["name"])
        st.markdown(badge(lead["score"]), unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            st.markdown("**Desglose del score**")
            for k, v in sd.get("detail", {}).items():
                st.progress(min(v / {"Encaje": 30, "Capacidad (est.)": 20, "Necesidad": 25, "Actividad": 15, "Calidad de datos": 10}[k], 1.0), f"{k}: {v}")
            st.markdown("**✅ Evidencias verificadas**")
            for e in parse(lead["evidence"], []):
                st.markdown(f"<span class='tag-v'>●</span> {e}", unsafe_allow_html=True)
            st.markdown("**🔶 Inferencias (no verificadas)**")
            for e in parse(lead["inferences"], []):
                st.markdown(f"<span class='tag-i'>●</span> {e}", unsafe_allow_html=True)
            if not lead["analyzed"]:
                st.caption("Web sin analizar o inaccesible.")
        with right:
            st.markdown(f"🌐 {lead['website'] or '—'}  \n📞 {lead['phone'] or '—'}  \n✉️ {lead['email'] or '—'}  \n"
                        f"📷 {lead['instagram'] or '—'}  \n📍 {lead['address'] or lead['city']}  \nFuente: {lead['source']}")
            ns = st.selectbox("Estado", db.STATUSES, index=db.STATUSES.index(lead["status"]) if lead["status"] in db.STATUSES else 0)
            fu = st.date_input("Próximo seguimiento", value=date.fromisoformat(lead["next_followup"]) if lead["next_followup"] else None)
            notes = st.text_area("Notas", lead["notes"] or "", height=120)
            b1, b2, b3 = st.columns(3)
            if b1.button("Guardar"):
                db.update_lead(lid, status=ns, notes=notes, next_followup=fu.isoformat() if fu else "")
                st.rerun()
            if b2.button("Re-analizar"):
                with st.spinner("Analizando…"):
                    pipeline.analyze_and_score(lid)
                st.rerun()
            if b3.button("Eliminar"):
                db.delete_lead(lid)
                st.rerun()
        st.markdown("**✍️ Mensaje personalizado (plantilla gratuita)**")
        m1, m2 = st.columns(2)
        lang = m1.radio("Idioma", ["es", "en"], horizontal=True)
        contact = m2.text_input("Nombre del contacto (opcional)", "") or "equipo de"
        st.text_area("Borrador — revísalo y envíalo tú", messages.build_message(
            business, lead, sd.get("signals"), lang, sender or "[Tu nombre]", contact), height=220, key=f"msg{lid}{lang}{contact}")

# ---------------------------------------------------------------- Importar CSV
elif page == "Importar CSV":
    st.header(f"Importar empresas desde CSV · {business}")
    st.caption("Columnas reconocidas: name/nombre, website/web, phone/telefono, email/correo, instagram, city/ciudad, country/pais, sector, address.")
    up = st.file_uploader("Archivo CSV", type="csv")
    c1, c2, c3 = st.columns(3)
    city = c1.text_input("Ciudad por defecto", "")
    country = c2.text_input("País por defecto", "República Dominicana")
    sector = c3.selectbox("Sector por defecto", list(SECTORS))
    an = st.checkbox("Analizar webs y puntuar", True)
    if up and st.button("Importar", type="primary"):
        bar = st.progress(0.0)
        try:
            new, old = pipeline.import_csv(business, up, city, country, sector, an, lambda p, m: bar.progress(p, m))
            st.success(f"{new} nuevos · {old} duplicados omitidos.")
        except Exception as e:
            st.error(str(e))

# ---------------------------------------------------------------- Programación
else:
    st.header("Búsquedas programadas")
    st.caption("Guarda búsquedas en **Buscar**. Se ejecutan aquí a mano o automáticamente con `scheduled.py` (ver README: Programador de tareas de Windows).")
    rows = [s for s in db.saved_searches() if s["business"] == business]
    for s in rows:
        c1, c2, c3 = st.columns([5, 1, 1])
        c1.write(f"**{s['sector']}** · {s['city']}, {s['country']} · {s['sources']} · última: {s['last_run'] or 'nunca'}")
        if c2.button("▶", key=f"r{s['id']}"):
            with st.spinner("Ejecutando…"):
                r = pipeline.run_search(business, s["country"], s["city"], s["sector"], s["sources"].split(","), s["max_results"], True)
                db.mark_search_run(s["id"], datetime.now().strftime("%Y-%m-%d %H:%M"))
            st.success(f"{r[0]} nuevos, {r[1]} existentes")
        if c3.button("🗑", key=f"d{s['id']}"):
            db.delete_search(s["id"])
            st.rerun()
    if not rows:
        st.info("No hay búsquedas guardadas para este negocio.")
