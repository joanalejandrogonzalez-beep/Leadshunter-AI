import json
from datetime import datetime

from . import analyzer, db, scoring, sources
from .models.schema import Lead as SqlLead
from .database import SessionLocal


def upsert_saas_lead(session, organization_id, lead, analysis=None):
    """Inserta o actualiza un lead en el esquema relacional multi-tenant (leads_v2)."""
    key = db.dedupe_key(lead)
    existing = session.query(SqlLead).filter(
        SqlLead.organization_id == organization_id,
        SqlLead.dedupe_key == key
    ).first()

    fields = ["name", "website", "phone", "email", "instagram", "country", "city", "sector", "source", "address"]
    if existing:
        for f in fields:
            val = lead.get(f)
            if val and not getattr(existing, f, None):
                setattr(existing, f, val)
        if analysis and analysis.get("ok"):
            res = scoring.score_lead(lead.get("business", ""), lead, analysis)
            existing.score = res["score"]
            existing.score_detail = json.dumps({"detail": res["detail"], "signals": analysis.get("signals", {})}, ensure_ascii=False)
            existing.evidence = json.dumps(res["evidence"], ensure_ascii=False)
            existing.inferences = json.dumps(res["inferences"], ensure_ascii=False)
            existing.analyzed = 1
        session.commit()
        return existing.id, False

    new_lead = SqlLead(
        organization_id=organization_id,
        dedupe_key=key,
        name=lead.get("name", "") or "Empresa",
        website=lead.get("website", "") or "",
        phone=lead.get("phone", "") or "",
        email=lead.get("email", "") or "",
        instagram=lead.get("instagram", "") or "",
        country=lead.get("country", "") or "",
        city=lead.get("city", "") or "",
        sector=lead.get("sector", "") or "",
        source=lead.get("source", "") or "",
        address=lead.get("address", "") or "",
        score=0,
        status="Nuevo"
    )
    if analysis and analysis.get("ok"):
        res = scoring.score_lead(lead.get("business", ""), lead, analysis)
        new_lead.score = res["score"]
        new_lead.score_detail = json.dumps({"detail": res["detail"], "signals": analysis.get("signals", {})}, ensure_ascii=False)
        new_lead.evidence = json.dumps(res["evidence"], ensure_ascii=False)
        new_lead.inferences = json.dumps(res["inferences"], ensure_ascii=False)
        new_lead.analyzed = 1
    session.add(new_lead)
    session.commit()
    return new_lead.id, True


def analyze_and_score(lead_id):
    """Analiza la web (si existe), completa contactos públicos vacíos y puntúa. Devuelve el análisis."""
    lead = db.get_lead(lead_id)
    analysis = analyzer.analyze_site(lead["website"])
    return apply_analysis(lead_id, lead, analysis)


def apply_analysis(lead_id, lead, analysis):
    f = analysis.get("facts", {})
    upd = {}
    if not lead["email"] and f.get("emails"):
        upd["email"] = f["emails"][0]
    if not lead["phone"] and f.get("phones"):
        upd["phone"] = f["phones"][0]
    if not lead["instagram"] and f.get("instagram"):
        upd["instagram"] = f["instagram"]
    lead.update(upd)
    res = scoring.score_lead(lead["business"], lead, analysis)
    # las señales se guardan junto al desglose para generar mensajes sin volver a analizar
    upd.update(score=res["score"],
               score_detail=json.dumps({"detail": res["detail"], "signals": analysis.get("signals", {})}, ensure_ascii=False),
               evidence=json.dumps(res["evidence"], ensure_ascii=False),
               inferences=json.dumps(res["inferences"], ensure_ascii=False),
               analyzed=1 if analysis.get("ok") else 0)
    db.update_lead(lead_id, **upd)
    return analysis


def run_search(business, country, city, sector, use_sources, max_results=30, analyze=True, progress=None, organization_id=None, session=None):
    """Busca, guarda sin duplicar, analiza y puntúa. Devuelve (nuevos, existentes, errores)."""
    found, errors = [], []
    for name, fn in (("OpenStreetMap", sources.search_osm), ("DuckDuckGo", sources.search_web)):
        if name in use_sources:
            try:
                found += fn(city, country, sector, max_results)
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {e}")
    new = old = 0
    ids = []
    
    close_session = False
    active_session = session
    if organization_id and active_session is None:
        active_session = SessionLocal()
        close_session = True

    try:
        for lead in found:
            lid, created = db.upsert_lead(business, lead)
            new += created
            old += (not created)
            ids.append(lid)

            if organization_id and active_session:
                lead_with_biz = dict(lead)
                lead_with_biz["business"] = business
                upsert_saas_lead(active_session, organization_id, lead_with_biz)

        if analyze:
            for i, lid in enumerate(ids):
                if progress:
                    progress((i + 1) / max(len(ids), 1), f"Analizando {i + 1}/{len(ids)}")
                try:
                    analysis = analyze_and_score(lid)
                    if organization_id and active_session:
                        updated_lead = db.get_lead(lid)
                        upsert_saas_lead(active_session, organization_id, updated_lead, analysis=analysis)
                except Exception as e:
                    errors.append(f"análisis #{lid}: {type(e).__name__}")
    finally:
        if close_session and active_session:
            active_session.close()

    return new, old, errors


def import_csv(business, file, city="", country="", sector="", analyze=True, progress=None, organization_id=None, session=None):
    leads = sources.read_csv(file, city, country, sector)
    ids, new = [], 0

    close_session = False
    active_session = session
    if organization_id and active_session is None:
        active_session = SessionLocal()
        close_session = True

    try:
        for lead in leads:
            lid, created = db.upsert_lead(business, lead)
            new += created
            ids.append(lid)
            if organization_id and active_session:
                lead_with_biz = dict(lead)
                lead_with_biz["business"] = business
                upsert_saas_lead(active_session, organization_id, lead_with_biz)

        for i, lid in enumerate(ids):
            if progress:
                progress((i + 1) / len(ids), f"Procesando {i + 1}/{len(ids)}")
            if analyze:
                try:
                    analysis = analyze_and_score(lid)
                    if organization_id and active_session:
                        updated_lead = db.get_lead(lid)
                        upsert_saas_lead(active_session, organization_id, updated_lead, analysis=analysis)
                except Exception:
                    pass
            else:
                l = db.get_lead(lid)
                res = scoring.score_lead(business, l, {"ok": False, "error": "no analizada", "facts": {}, "signals": {}})
                db.update_lead(lid, score=res["score"])
                if organization_id and active_session:
                    upsert_saas_lead(active_session, organization_id, l)
    finally:
        if close_session and active_session:
            active_session.close()

    return new, len(ids) - new


def run_saved(progress=None):
    out = []
    for s in db.saved_searches():
        r = run_search(s["business"], s["country"], s["city"], s["sector"], s["sources"].split(","), s["max_results"], True, progress)
        db.mark_search_run(s["id"], datetime.now().strftime("%Y-%m-%d %H:%M"))
        out.append((s, r))
    return out
