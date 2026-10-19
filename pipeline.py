import json
from datetime import datetime

from . import analyzer, db, scoring, sources


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


def run_search(business, country, city, sector, use_sources, max_results=30, analyze=True, progress=None):
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
    for lead in found:
        lid, created = db.upsert_lead(business, lead)
        new += created
        old += (not created)
        ids.append(lid)
    if analyze:
        for i, lid in enumerate(ids):
            if progress:
                progress((i + 1) / max(len(ids), 1), f"Analizando {i + 1}/{len(ids)}")
            try:
                analyze_and_score(lid)
            except Exception as e:
                errors.append(f"análisis #{lid}: {type(e).__name__}")
    return new, old, errors


def import_csv(business, file, city="", country="", sector="", analyze=True, progress=None):
    leads = sources.read_csv(file, city, country, sector)
    ids, new = [], 0
    for lead in leads:
        lid, created = db.upsert_lead(business, lead)
        new += created
        ids.append(lid)
    for i, lid in enumerate(ids):
        if progress:
            progress((i + 1) / len(ids), f"Procesando {i + 1}/{len(ids)}")
        if analyze:
            try:
                analyze_and_score(lid)
            except Exception:
                pass
        else:
            l = db.get_lead(lid)
            res = scoring.score_lead(business, l, {"ok": False, "error": "no analizada", "facts": {}, "signals": {}})
            db.update_lead(lid, score=res["score"])
    return new, len(ids) - new


def run_saved(progress=None):
    out = []
    for s in db.saved_searches():
        r = run_search(s["business"], s["country"], s["city"], s["sector"], s["sources"].split(","), s["max_results"], True, progress)
        db.mark_search_run(s["id"], datetime.now().strftime("%Y-%m-%d %H:%M"))
        out.append((s, r))
    return out
