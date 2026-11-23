"""Puntuación 0-100 por negocio. Cada punto se apoya en una EVIDENCIA (observada en la web o en la fuente)
o en una INFERENCIA (interpretación mía, marcada como tal). La capacidad económica es siempre una estimación."""
from datetime import datetime

# Ajustes de encaje sectorial por tipo de propuesta de valor comercial
SOFTWARE_SECTOR_FIT = {"Constructoras": 28, "Distribuidoras": 28, "Inmobiliarias": 25, "Propiedades vacacionales": 18}
MEDIA_SECTOR_FIT = {"Inmobiliarias": 30, "Constructoras": 26, "Propiedades vacacionales": 30, "Distribuidoras": 4}
GENERAL_SECTOR_FIT = {"Constructoras": 25, "Inmobiliarias": 25, "Distribuidoras": 25, "Propiedades vacacionales": 25}

# Mapeos históricos preservados para retrocompatibilidad
NOVUS_SECTOR_FIT = SOFTWARE_SECTOR_FIT
NTO_SECTOR_FIT = MEDIA_SECTOR_FIT


def _get_business_category(business):
    b = (business or "").lower()
    if "nto" in b or any(k in b for k in ("video", "media", "audiovisual", "produccion", "producción")):
        return "media"
    if "novus" in b or any(k in b for k in ("software", "web", "tech", "ops", "sistemas", "dev")):
        return "software"
    return "general"


def score_lead(business, lead, analysis):
    f, s = analysis.get("facts", {}), analysis.get("signals", {})
    ok = analysis.get("ok", False)
    ev, inf = [], []  # evidencias verificadas / inferencias
    d = {"Encaje": 0, "Capacidad (est.)": 0, "Necesidad": 0, "Actividad": 0, "Calidad de datos": 0}
    sector = lead.get("sector", "")
    cat = _get_business_category(business)

    # --- Encaje (30)
    if cat == "media" or business == "NTO Productions":
        table = MEDIA_SECTOR_FIT
    elif cat == "software" or business == "Novus Ops":
        table = SOFTWARE_SECTOR_FIT
    else:
        table = GENERAL_SECTOR_FIT

    d["Encaje"] = table.get(sector, 15)
    ev.append(f"Sector indicado en la búsqueda/fuente: {sector or 'sin definir'} (fuente: {lead.get('source') or 'n/d'}).")

    # --- Calidad de datos (10)
    q = 0
    q += 3 if lead.get("website") else 0
    q += 3 if (lead.get("email") or f.get("emails")) else 0
    q += 2 if (lead.get("phone") or f.get("phones")) else 0
    q += 2 if (lead.get("instagram") or f.get("instagram")) else 0
    d["Calidad de datos"] = q

    if not ok:
        inf.append(f"Web no analizada ({analysis.get('error') or 'sin web'}): necesidad y actividad no se pueden estimar.")
        d["Capacidad (est.)"], d["Necesidad"], d["Actividad"] = 6, 5, 3
        return _pack(d, ev, inf)

    ev.append(f"Se leyeron {f.get('pages_read', 1)} página(s) de la web.")
    cap, need, act = 0, 0, 0

    # --- Capacidad económica estimada (20): proxies de tamaño/complejidad
    if s["listing_mentions"] >= 15 or s["catalog_mentions"] >= 15 or s["project_mentions"] >= 15:
        cap += 8
        inf.append("Inferencia: la web menciona muchos proyectos/propiedades/productos → operación de volumen relevante.")
    elif s["listing_mentions"] + s["catalog_mentions"] + s["project_mentions"] >= 5:
        cap += 4
    if s["branch_mentions"] >= 2:
        cap += 5
        inf.append("Inferencia: menciona varias sucursales/oficinas → estructura más grande.")
    if f.get("pages_read", 1) >= 3:
        cap += 2
    if (cat == "media" or business == "NTO Productions") and s["luxury_mentions"] >= 2:
        cap += 5
        ev.append("Observado: lenguaje de producto premium/lujo/frente al mar en la web.")
    if len([x for x in (lead.get("email") or f["emails"], lead.get("phone") or f["phones"], lead.get("instagram") or f["instagram"]) if x]) == 3:
        cap += 2
    d["Capacidad (est.)"] = min(cap, 20)
    inf.append("La capacidad de inversión es una estimación indirecta basada en proxies de volumen; confírmala en la conversación.")

    # --- Necesidad (25)
    if cat == "software" or business == "Novus Ops":
        if not f["https"]:
            need += 5; ev.append("Observado: la web no usa HTTPS.")
        if not s["has_viewport"]:
            need += 5; ev.append("Observado: la web no declara versión móvil (sin meta viewport).")
        if not s["has_form"] and not s["has_quote_cta"]:
            need += 6; ev.append("Observado: no se detectó formulario ni llamada a cotizar/agendar.")
        if not s["has_portal"]:
            need += 4; inf.append("Inferencia: sin portal/área de clientes → posible oportunidad de software o automatización.")
        if s["catalog_mentions"] >= 5 or s["project_mentions"] >= 5 or s["branch_mentions"] >= 2:
            need += 5; inf.append("Inferencia: operación con inventario/proyectos/sucursales → procesos candidatos a automatizar.")
    elif cat == "media" or business == "NTO Productions":
        if not s["has_video"]:
            need += 12; ev.append("Observado: no se detectó vídeo incrustado (YouTube/Vimeo/<video>) en las páginas leídas.")
        else:
            need -= 0; ev.append("Observado: la web ya incluye vídeo; la oportunidad es mejorar calidad/volumen.")
        if s["listing_mentions"] >= 5:
            need += 8; ev.append("Observado: la web promociona propiedades/proyectos (material que se beneficia de vídeo).")
        if s["has_social_instagram"]:
            need += 5; ev.append("Observado: tiene Instagram enlazado (canal donde el vídeo rinde).")
    else:
        # Perfil comercial general / agencias / consultoría
        if not f["https"] or not s["has_viewport"]:
            need += 8; ev.append("Observado: oportunidad de optimización técnica y móvil en la presencia web.")
        if not s["has_form"] and not s["has_quote_cta"]:
            need += 8; ev.append("Observado: sin formulario de contacto directo o llamada a la acción clara.")
        if not s["has_social_instagram"] and not s["has_whatsapp"]:
            need += 6; inf.append("Inferencia: canales directos de captación limitados.")
    d["Necesidad"] = max(0, min(need, 25))

    # --- Actividad (15)
    yr = f.get("last_copyright_year")
    now = datetime.now().year
    if yr:
        if yr >= now - 1:
            act += 8; ev.append(f"Observado: copyright del pie de página {yr} (web mantenida).")
        elif yr >= now - 3:
            act += 4; ev.append(f"Observado: copyright {yr} (actualización no reciente).")
        else:
            ev.append(f"Observado: copyright {yr} (web posiblemente abandonada).")
            if cat == "software" or business == "Novus Ops":
                d["Necesidad"] = min(25, d["Necesidad"] + 3)
    else:
        act += 3
    if s["has_social_instagram"]:
        act += 4; ev.append("Observado: enlaza Instagram.")
    if s["has_whatsapp"]:
        act += 3; ev.append("Observado: ofrece contacto por WhatsApp.")
    d["Actividad"] = min(act, 15)
    return _pack(d, ev, inf)


def _pack(d, ev, inf):
    return {"score": max(0, min(100, sum(d.values()))), "detail": d, "evidence": ev, "inferences": inf}
