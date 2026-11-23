"""Motor de IA conversacional para prospección B2B en lenguaje natural.
Interpreta solicitudes, extrae filtros estructurados y explica prospectos reales sin inventar datos.
"""
import os
import re
import json
import requests
from typing import Dict, Any, List

from . import pipeline, sources, db, prospecting


import unicodedata

def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")


def _extract_requested_results(prompt: str):
    match = re.search(r"\b(\d{1,2})\s+(?:leads?|prospectos?|empresas?)\b", _norm(prompt))
    return max(1, min(int(match.group(1)), 30)) if match else None


def _extract_service(prompt: str) -> str:
    patterns = (
        r"(?:mis\s+servicios\s+como|servicios\s+como|ofrezco|vendo|hago|soy|como)\s+([^,.!?]+)",
        r"servicios\s+de\s+([^,.!?]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, prompt, re.I)
        if match:
            return match.group(1).strip()[:100]
    normalized = _norm(prompt)
    if any(term in normalized for term in ("software", "desarrollo web", "programacion", "automatizacion")):
        return "Desarrollo Web y Software"
    if any(term in normalized for term in ("video", "audiovisual", "fotografia")):
        return "Producción Audiovisual y Fotografía"
    if any(term in normalized for term in ("marketing", "publicidad", "captacion", "seo")):
        return "Marketing Digital y Captación"
    return ""


def parse_prompt_heuristic(prompt: str) -> Dict[str, Any]:
    """Extractor semántico por reglas heurísticas cuando no hay clave de API externa configurada."""
    p_norm = _norm(prompt)
    p_lower = prompt.lower()

    # Detección de sectores
    sector = "Constructoras"
    for s in sources.SECTORS:
        if _norm(s) in p_norm:
            sector = s
            break
    if any(k in p_norm for k in ("constructora", "construccion", "obra", "edificaci")):
        sector = "Constructoras"
    elif any(k in p_norm for k in ("inmobiliaria", "bienes raices", "real estate", "propiedad")):
        sector = "Inmobiliarias"
    elif any(k in p_norm for k in ("distribuidora", "al por mayor", "importadora", "mayorista")):
        sector = "Distribuidoras"
    elif any(k in p_norm for k in ("dental", "dentista", "odontolog", "diente")):
        sector = "Clínicas dentales"
    elif any(k in p_norm for k in ("marketing", "publicidad", "agencia digital")):
        sector = "Agencias de marketing"
    elif any(k in p_norm for k in ("restaurante", "comida", "gastronom")):
        sector = "Restaurantes"
    elif any(k in p_norm for k in ("hotel", "turismo", "resort")):
        sector = "Hoteles"
    elif any(k in p_norm for k in ("abogado", "legal", "bufete", "despacho")):
        sector = "Abogados / Legal"
    elif any(k in p_norm for k in ("gimnasio", "fitness", "gym", "entrenam")):
        sector = "Gimnasios / Fitness"

    # Detección de ciudades y países comunes
    country = "República Dominicana"
    city = "Santo Domingo"

    geo_map = [
        ("santo domingo", "Santo Domingo", "República Dominicana"),
        ("santiago de los caballeros", "Santiago de los Caballeros", "República Dominicana"),
        ("punta cana", "Punta Cana", "República Dominicana"),
        ("madrid", "Madrid", "España"),
        ("barcelona", "Barcelona", "España"),
        ("valencia", "Valencia", "España"),
        ("ciudad de panama", "Ciudad de Panamá", "Panamá"),
        ("panama", "Ciudad de Panamá", "Panamá"),
        ("ciudad de mexico", "Ciudad de México", "México"),
        ("cdmx", "Ciudad de México", "México"),
        ("mexico", "Ciudad de México", "México"),
        ("guadalajara", "Guadalajara", "México"),
        ("monterrey", "Monterrey", "México"),
        ("bogota", "Bogotá", "Colombia"),
        ("medellin", "Medellín", "Colombia"),
        ("buenos aires", "Buenos Aires", "Argentina"),
        ("lima", "Lima", "Perú"),
        ("santiago", "Santiago", "Chile"),
        ("miami", "Miami", "Estados Unidos"),
    ]

    for trigger, c, co in geo_map:
        if trigger in p_norm:
            city = c
            country = co
            break

    # Si se menciona explícitamente "en [Ciudad]" o "en [Ciudad], [País]"
    m_en = re.search(r"\ben\s+([a-záéíóúñ\s]+?)(?:\s*,\s*([a-záéíóúñ\s]+))?(?:\s+que|\s+con|\s+para|\s*$)", p_lower)
    if m_en:
        extracted_city = m_en.group(1).strip().title()
        if len(extracted_city) > 2 and extracted_city.lower() not in ("varios", "varias", "este", "esta", "todo"):
            city = extracted_city
        if m_en.group(2):
            country = m_en.group(2).strip().title()

    criteria = []
    if any(k in p_lower for k in ("web", "software", "portal", "automatiza", "digital", "presencia")):
        criteria.append("Oportunidad de digitalización / software / presencia web")
    if any(k in p_lower for k in ("video", "audiovisual", "foto", "multimedia")):
        criteria.append("Oportunidad de producción de video y contenido visual")
    if any(k in p_lower for k in ("volumen", "varios proyectos", "grande", "sucursales")):
        criteria.append("Operación de volumen o múltiples proyectos")

    return {
        "intent": "search",
        "city": city,
        "country": country,
        "sector": sector,
        "service": _extract_service(prompt),
        "max_results": _extract_requested_results(prompt) or 10,
        "criteria": criteria,
        "explanation": f"He interpretado tu solicitud para buscar empresas del sector **{sector}** en **{city}, {country}**.",
        "used_ai": False
    }


def parse_prompt_gemini(prompt: str, api_key: str) -> Dict[str, Any]:
    """Utiliza la API oficial de Google Gemini para interpretar solicitudes con razonamiento semántico."""
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    system_instruction = (
        "Eres el asistente de prospección B2B de LeadHunter AI. "
        "Tu tarea es analizar el prompt del usuario y extraer filtros estructurados estrictos en JSON. "
        "No inventes datos. Campos requeridos en el JSON: "
        "'city' (nombre de la ciudad), 'country' (nombre del país), 'sector' (sector comercial B2B), "
        "'service' (servicio que ofrece el usuario), 'max_results' (cantidad solicitada), "
        "'criteria' (lista de criterios como 'presencia digital mejorable', 'necesidad de video', etc.), "
        "'explanation' (breve explicación en español de qué se buscará)."
    )
    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\nSolicitud del usuario: {prompt}"}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=12)
    r.raise_for_status()
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)
    parsed["intent"] = "search"
    parsed["used_ai"] = True
    return parsed


def interpret_prompt(prompt: str) -> Dict[str, Any]:
    """Interpreta filtros con Gemini opcional y completa servicio/cantidad con reglas locales."""
    heuristic = parse_prompt_heuristic(prompt)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            parsed = parse_prompt_gemini(prompt, api_key)
            return {
                **heuristic,
                **parsed,
                "service": parsed.get("service") or heuristic["service"],
                "max_results": _extract_requested_results(prompt) or heuristic["max_results"],
            }
        except Exception:
            pass
    return heuristic


def detect_intent(prompt: str) -> str:
    normalized = _norm(prompt)
    if re.search(r"\b(busca|buscar|encuentra|encontrar|prospecta|prospectar|dame|lista|listado|leads?|prospectos?)\b", normalized):
        return "search"
    if any(term in normalized for term in (
        "cliente ideal", "que nicho", "que sector", "ofrezco", "vendo", "mis servicios",
        "servicios como", "me conviene", "recomiendame", "recomienda un nicho",
        "analiza mi nicho", "analiza mi oferta", "orientame",
    )):
        return "advice"
    return "general"


def reply_general(prompt: str) -> str:
    """Responde preguntas generales con Gemini si existe clave o guía al usuario sin inventar."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": (
                    "Eres el asistente de LeadHunter AI. Responde en español, de forma breve y útil. "
                    "No afirmes haber buscado empresas si no se ejecutó una búsqueda.\n\n"
                    f"Consulta: {prompt}"
                )}]}]
            }
            response = requests.post(url, json=payload, timeout=12)
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass
    return (
        "Puedo ayudarte a definir tu cliente ideal o buscar empresas reales y analizar sus sitios. "
        "Cuéntame qué servicio ofreces, qué tipo de empresa buscas y en qué ciudad."
    )


def run_conversational_search(
    business: str,
    prompt: str,
    progress_callback=None,
    organization_id: str = None,
    session=None,
    service_profile: str = "",
    max_results: int = 10,
    sender: str = "[Tu nombre]",
) -> Dict[str, Any]:
    """Interpreta y ejecuta el pipeline agéntico compartido por Streamlit y FastAPI."""
    interpretation = interpret_prompt(prompt)
    interpretation["max_results"] = _extract_requested_results(prompt) or max_results
    if service_profile and not interpretation.get("service"):
        interpretation["service"] = service_profile
    result = prospecting.run_prospecting(
        business=business,
        interpretation=interpretation,
        service_profile=service_profile,
        max_results=max_results,
        progress_callback=progress_callback,
        organization_id=organization_id,
        session=session,
        sender=sender,
    )
    return {"interpretation": interpretation, **result}


def advise_icp_heuristic(service_text: str, location_hint: str = "") -> Dict[str, Any]:
    """Asesor estratégico heurístico de Cliente Ideal (ICP) según el servicio ofrecido."""
    s_norm = _norm(service_text + " " + location_hint)
    s_lower = (service_text + " " + location_hint).lower()

    # Detección geográfica si se menciona
    city = "Santo Domingo"
    country = "República Dominicana"
    geo_map = [
        ("santo domingo", "Santo Domingo", "República Dominicana"),
        ("santiago de los caballeros", "Santiago de los Caballeros", "República Dominicana"),
        ("punta cana", "Punta Cana", "República Dominicana"),
        ("madrid", "Madrid", "España"),
        ("barcelona", "Barcelona", "España"),
        ("ciudad de mexico", "Ciudad de México", "México"),
        ("cdmx", "Ciudad de México", "México"),
        ("guadalajara", "Guadalajara", "México"),
        ("monterrey", "Monterrey", "México"),
        ("bogota", "Bogotá", "Colombia"),
        ("medellin", "Medellín", "Colombia"),
        ("buenos aires", "Buenos Aires", "Argentina"),
        ("lima", "Lima", "Perú"),
        ("santiago", "Santiago", "Chile"),
        ("miami", "Miami", "Estados Unidos"),
        ("panama", "Ciudad de Panamá", "Panamá"),
    ]
    for trigger, c, co in geo_map:
        if trigger in s_norm:
            city = c
            country = co
            break

    # Diagnóstico de oferta y nicho recomendado
    if any(k in s_norm for k in ("video", "audiovisual", "foto", "camara", "produccion", "drone", "filmmak", "multimedia")):
        service = "Producción audiovisual y contenido de video"
        sector = "Inmobiliarias"
        reasoning = (
            "Para producción audiovisual, tu cliente de mayor retorno y presupuesto son las **Inmobiliarias y Desarrolladores**. "
            "Un video profesional para una propiedad acelera las ventas y alquileres, por lo que tienen un ROI inmediato."
        )
        pains = [
            "Presentan propiedades y proyectos solo con fotos estáticas en su web",
            "Tienen catálogo amplio pero no aprovechan video para captar compradores internacionales o de alto ticket"
        ]
        pitch = "Vi que su catálogo de proyectos se presenta sin video profesional en su web; producimos recorridos que aceleran las ventas."

    elif any(k in s_norm for k in ("web", "software", "sistema", "programaci", "app", "automatiz", "digital", "crm", "erp")):
        service = "Desarrollo web, software y automatización"
        sector = "Constructoras"
        reasoning = (
            "Para servicios de software y páginas web, tu mejor nicho son las **Constructoras y Empresas de Obras**. "
            "Manejan presupuestos de gran escala pero con frecuencia tienen presencia web desactualizada, sin versión móvil óptima "
            "ni formularios interactivos para cotizar."
        )
        pains = [
            "Páginas web obsoletas o sin optimización para celulares",
            "Falta de formularios directos para solicitud de presupuesto",
            "Procesos manuales de atención a clientes y contratistas"
        ]
        pitch = "Noté que su web corporativa no cuenta con formulario directo para cotizaciones ni optimización móvil; podemos modernizar su captación."

    elif any(k in s_norm for k in ("marketing", "publicidad", "redes", "social media", "seo", "anuncios", "pauta", "leads")):
        service = "Marketing digital y captación de clientes"
        sector = "Clínicas dentales"
        reasoning = (
            "Para agencias de marketing y captación, las **Clínicas dentales y Centros de Salud estética** son ideales: "
            "tienen tickets recurrentes altos, margen para invertir y necesidad constante de pacientes locales."
        )
        pains = [
            "Canales de agendamiento directo poco visibles",
            "Oportunidad de campañas locales de captación de pacientes nuevos"
        ]
        pitch = "Ayudamos a clínicas del sector de salud a llenar sus agendas mediante campañas locales y automatización de citas."

    elif any(k in s_norm for k in ("abogad", "legal", "contab", "fiscal", "auditor", "financ", "tributar")):
        service = "Servicios legales, contables o financieros"
        sector = "Distribuidoras"
        reasoning = (
            "Para consultoría legal y contable, las **Distribuidoras y Empresas mayoristas** son un objetivo prioritario: "
            "manejan alto volumen de facturación, contratos comerciales y requisitos fiscales exigentes."
        )
        pains = [
            "Gestión compleja de contratos y cobranzas",
            "Necesidad de optimización fiscal y cumplimiento normativo"
        ]
        pitch = "Asesoramos a empresas de distribución comercial para blindar sus contratos y optimizar su gestión financiera."

    else:
        service = "Servicios profesionales B2B"
        sector = "Constructoras"
        reasoning = (
            "Para servicios comerciales B2B, las **Constructoras e Inmobiliarias** representan el nicho con mayor "
            "capacidad de inversión y volumen de proyectos en tu mercado."
        )
        pains = [
            "Presencia digital mejorable y oportunidades de modernización comercial",
            "Múltiples obras activas que requieren proveedores de confianza"
        ]
        pitch = "Brindamos soluciones especializadas para impulsar la presencia y eficiencia comercial de su empresa."

    return {
        "service_detected": service,
        "recommended_sector": sector,
        "target_city": city,
        "target_country": country,
        "reasoning": reasoning,
        "pain_points": pains,
        "suggested_pitch": pitch,
        "ready_search_prompt": f"Encuentra empresas del sector {sector} en {city}, {country} con oportunidad de {service.lower()}."
    }


def advise_icp_gemini(service_text: str, location_hint: str, api_key: str) -> Dict[str, Any]:
    """Asesor estratégico de Cliente Ideal utilizando Google Gemini API."""
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    system_instruction = (
        "Eres el consultor senior de estrategia comercial B2B de LeadHunter AI. "
        "El usuario te dirá qué servicio o producto vende y opcionalmente su ubicación. "
        "Tu misión es recomendar el nicho de clientes con MAYOR NECESIDAD y CAPACIDAD DE PAGO para su oferta. "
        "Los sectores admitidos deben mapearse a uno de: Constructoras, Inmobiliarias, Distribuidoras, Clínicas dentales, "
        "Agencias de marketing, Restaurantes, Hoteles, Abogados / Legal, Gimnasios / Fitness, o Propiedades vacacionales. "
        "Devuelve estrictamente un JSON con las claves: "
        "'service_detected', 'recommended_sector', 'target_city', 'target_country', 'reasoning', "
        "'pain_points' (lista de 2 textos), 'suggested_pitch', 'ready_search_prompt'."
    )
    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\nServicio ofrecido: {service_text}\nUbicación preferida: {location_hint}"}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=12)
    r.raise_for_status()
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def advise_icp(service_text: str, location_hint: str = "") -> Dict[str, Any]:
    """Punto de entrada unificado para asesoría de cliente ideal y nicho."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            return advise_icp_gemini(service_text, location_hint, api_key)
        except Exception:
            pass
    return advise_icp_heuristic(service_text, location_hint)
