"""Herramientas y orquestación para descubrir y calificar prospectos B2B."""
from __future__ import annotations

import ipaddress
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from . import analyzer, db, messages, pipeline, scoring, sources
from .database import SessionLocal
from .models.schema import Lead as SqlLead


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

SEARCH_TIMEOUT = 12
MAX_RESULTS = 30
MIN_QUALIFIED_SCORE = 35
SEARCH_HEADERS = {
    "User-Agent": "LeadHunterAI/1.0 (public B2B prospect research)",
    "Accept-Language": "es,en;q=0.8",
}
EXCLUDED_RESULT_TERMS = (
    "directorio", "noticias", "noticia", "empleos", "vacantes", "bolsa de trabajo",
    "ranking", "top 10", "listado de empresas", "páginas amarillas", "paginas amarillas",
)


def _queries(service: str, sector: str, city: str, country: str) -> list[str]:
    location = f'"{city}" "{country}"'
    service_hint = f'"{service}"' if service and service.lower() != sector.lower() else ""
    exclusions = "-directorio -noticias -empleos -vacantes"
    return [
        f'"{sector}" {location} {service_hint} contacto empresa {exclusions}',
        f'{sector} {location} proyectos servicios empresa {exclusions}',
    ]


def _unwrap_url(url: str) -> str:
    parsed = urlparse(url)
    if "uddg" in parse_qs(parsed.query):
        return unquote(parse_qs(parsed.query)["uddg"][0])
    return url


def _normalize_candidate(raw: dict, city: str, country: str, sector: str, provider: str) -> dict | None:
    name = re.sub(r"\s+", " ", str(raw.get("name") or raw.get("title") or "")).strip()
    snippet = str(raw.get("snippet") or raw.get("content") or "")
    url = _unwrap_url(str(raw.get("website") or raw.get("url") or raw.get("link") or ""))
    parsed = urlparse(url)
    if not parsed.scheme and parsed.netloc == "" and "." in parsed.path:
        url = f"https://{url}"
        parsed = urlparse(url)
    host = parsed.hostname.lower().removeprefix("www.") if parsed.hostname else ""
    if parsed.scheme not in {"http", "https"} or not host or "." not in host:
        return None
    try:
        if not ipaddress.ip_address(host).is_global:
            return None
    except ValueError:
        pass
    if any(domain in host for domain in sources.SKIP_DOMAINS):
        return None
    if any(term in f"{name} {snippet}".lower() for term in EXCLUDED_RESULT_TERMS):
        return None
    if not name or len(name) < 3:
        return None
    return {
        "name": name[:160],
        "website": f"{parsed.scheme}://{host}",
        "city": city,
        "country": country,
        "sector": sector,
        "source": str(raw.get("source") or provider),
        "phone": str(raw.get("phone") or ""),
        "email": str(raw.get("email") or ""),
        "instagram": str(raw.get("instagram") or ""),
        "linkedin": str(raw.get("linkedin") or ""),
        "address": str(raw.get("address") or ""),
        "search_snippet": snippet[:500],
    }


def _serper_search(query: str, limit: int) -> list[dict]:
    response = requests.post(
        "https://google.serper.dev/search",
        json={"q": query, "num": min(limit, 20)},
        headers={"X-API-KEY": os.environ["SERPER_API_KEY"], "Content-Type": "application/json"},
        timeout=SEARCH_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("organic", [])


def _tavily_search(query: str, limit: int) -> list[dict]:
    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": os.environ["TAVILY_API_KEY"],
            "query": query,
            "search_depth": "basic",
            "max_results": min(limit, 20),
            "include_answer": False,
        },
        timeout=SEARCH_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("results", [])


def _duckduckgo_search(query: str, limit: int) -> list[dict]:
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query},
        headers=SEARCH_HEADERS,
        timeout=SEARCH_TIMEOUT,
    )
    response.raise_for_status()
    results = []
    for anchor in BeautifulSoup(response.text, "html.parser").select("a.result__a"):
        results.append({
            "title": anchor.get_text(" ", strip=True),
            "url": _unwrap_url(anchor.get("href", "")),
        })
        if len(results) >= limit:
            break
    return results


def search_b2b_prospects(
    service: str,
    sector: str,
    city: str,
    country: str,
    limit: int = 20,
) -> tuple[list[dict], list[str]]:
    """Busca sitios corporativos con Serper/Tavily y usa DuckDuckGo si no hay clave."""
    limit = max(1, min(int(limit), MAX_RESULTS * 2))
    providers = []
    if os.getenv("SERPER_API_KEY"):
        providers.append(("Serper", _serper_search))
    if os.getenv("TAVILY_API_KEY"):
        providers.append(("Tavily", _tavily_search))
    providers.append(("DuckDuckGo", _duckduckgo_search))

    errors = []
    for provider_name, search_fn in providers:
        found, seen = [], set()
        for query in _queries(service, sector, city, country):
            try:
                results = search_fn(query, limit)
            except (requests.RequestException, ValueError, KeyError) as exc:
                errors.append(f"{provider_name}: {type(exc).__name__}")
                break
            for raw in results:
                candidate = _normalize_candidate(raw, city, country, sector, provider_name)
                if candidate and candidate["website"] not in seen:
                    seen.add(candidate["website"])
                    found.append(candidate)
                    if len(found) >= limit:
                        break
            if len(found) >= limit:
                break
            if provider_name == "DuckDuckGo":
                time.sleep(0.5)
        if found:
            return found[:limit], errors
    return [], errors


def analyze_company_website(website: str) -> dict:
    """Lee una web pública respetando robots.txt y límites de páginas/tiempo."""
    try:
        return analyzer.analyze_site(website, max_pages=3)
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "facts": {}, "signals": {}}


def extract_contact_signals(candidate: dict, analysis: dict) -> dict:
    facts = analysis.get("facts", {})
    signals = analysis.get("signals", {})
    return {
        "email": candidate.get("email") or next(iter(facts.get("emails", [])), ""),
        "phone": candidate.get("phone") or next(iter(facts.get("phones", [])), ""),
        "linkedin": candidate.get("linkedin") or next(iter(facts.get("linkedin", [])), ""),
        "instagram": candidate.get("instagram") or facts.get("instagram", ""),
        "contact_form": bool(signals.get("has_form")),
    }


def _service_category(service: str) -> str:
    normalized = service.lower()
    if any(term in normalized for term in ("software", "desarrollo", "programación", "programacion", "web", "sistema", "automatiz")):
        return "software"
    if any(term in normalized for term in ("video", "audiovisual", "fotografía", "fotografia", "media")):
        return "media"
    if any(term in normalized for term in ("marketing", "publicidad", "captación", "captacion", "seo", "leads")):
        return "marketing"
    return "general"


def _diagnose_need(service: str, analysis: dict) -> str:
    facts = analysis.get("facts", {})
    signals = analysis.get("signals", {})
    category = _service_category(service)
    issues = []
    if category == "software":
        if not signals.get("has_form") and not signals.get("has_quote_cta"):
            issues.append("No se detectó un formulario ni una vía directa para cotizar en las páginas revisadas.")
        if not signals.get("has_viewport"):
            issues.append("La página analizada no declara configuración viewport para móviles.")
        if not signals.get("has_portal"):
            issues.append("No se encontró un portal de clientes; es una oportunidad posible, no una necesidad confirmada.")
        if signals.get("project_mentions", 0) >= 5 or signals.get("catalog_mentions", 0) >= 5:
            issues.append("El sitio muestra múltiples proyectos o productos, señal de procesos que podrían automatizarse.")
    elif category == "media":
        if not signals.get("has_video"):
            issues.append("No se detectó video incrustado en las páginas revisadas.")
        if signals.get("listing_mentions", 0) >= 3:
            issues.append("El sitio promociona varias propiedades o proyectos que podrían beneficiarse de contenido audiovisual.")
    elif category == "marketing":
        if not signals.get("has_form") and not signals.get("has_quote_cta"):
            issues.append("No se detectó un formulario ni una llamada clara a cotizar o agendar.")
        if not signals.get("has_social_instagram") and not signals.get("has_whatsapp"):
            issues.append("No se detectaron enlaces directos a Instagram o WhatsApp.")
    else:
        if not signals.get("has_form") and not signals.get("has_quote_cta"):
            issues.append("No se detectó un canal de conversión directo en las páginas revisadas.")
        if not signals.get("has_viewport"):
            issues.append("No se detectó configuración viewport para móviles.")
    if not issues and signals.get("text_len", 0) >= 80:
        return "La web está activa; la oportunidad requiere validación comercial antes del contacto."
    return " ".join(issues[:3])


def _persist_qualified_lead(
    business: str,
    service_profile: str,
    lead: dict,
    analysis: dict,
    score_result: dict,
    diagnosis: str,
    organization_id: str | None,
    session,
) -> bool:
    lead_for_storage = {
        key: lead.get(key, "")
        for key in ("name", "website", "phone", "email", "instagram", "city", "country", "sector", "source", "address")
    }
    lead_id, created = db.upsert_lead(business, lead_for_storage)
    existing = db.get_lead(lead_id) or {}
    updates = {
        "email": lead.get("email", ""),
        "phone": lead.get("phone", ""),
        "instagram": lead.get("instagram", ""),
        "score": score_result["score"],
        "score_detail": json.dumps({"detail": score_result["detail"], "signals": analysis.get("signals", {})}, ensure_ascii=False),
        "evidence": json.dumps(score_result["evidence"], ensure_ascii=False),
        "inferences": json.dumps(score_result["inferences"], ensure_ascii=False),
        "analyzed": 1,
    }
    if not existing.get("notes"):
        updates["notes"] = diagnosis
    db.update_lead(lead_id, **{key: value for key, value in updates.items() if value or key in {"score", "score_detail", "evidence", "inferences", "analyzed"}})

    if organization_id and session is not None:
        saas_lead = {**lead_for_storage, "business": service_profile}
        saas_lead_id, _ = pipeline.upsert_saas_lead(session, organization_id, saas_lead, analysis=analysis)
        saas_record = session.query(SqlLead).filter(
            SqlLead.id == saas_lead_id,
            SqlLead.organization_id == organization_id,
        ).first()
        if saas_record:
            saas_record.score = score_result["score"]
            saas_record.score_detail = updates["score_detail"]
            saas_record.evidence = updates["evidence"]
            saas_record.inferences = updates["inferences"]
            saas_record.analyzed = 1
            if not saas_record.notes:
                saas_record.notes = diagnosis
            session.commit()
    return created


def run_prospecting(
    business: str,
    interpretation: dict,
    service_profile: str = "",
    max_results: int = 10,
    progress_callback=None,
    organization_id: str | None = None,
    session=None,
    sender: str = "[Tu nombre]",
) -> dict:
    """Ejecuta búsqueda, análisis, cualificación, contacto y persistencia de leads."""
    city = interpretation.get("city", "Santo Domingo")
    country = interpretation.get("country", "República Dominicana")
    sector = interpretation.get("sector", "Constructoras")
    service = interpretation.get("service") or service_profile or business
    requested = interpretation.get("max_results") or max_results
    target = max(1, min(int(requested), MAX_RESULTS))
    candidate_limit = min(target * 3, MAX_RESULTS * 2)
    errors = []

    if progress_callback:
        progress_callback(0.02, "Buscando empresas en fuentes públicas…")
    candidates, search_errors = search_b2b_prospects(service, sector, city, country, candidate_limit)
    errors.extend(search_errors)
    if len(candidates) < target:
        try:
            candidates.extend(sources.search_osm(city, country, sector, candidate_limit - len(candidates)))
        except Exception as exc:
            errors.append(f"OpenStreetMap: {type(exc).__name__}")

    unique_candidates = []
    seen = set()
    for raw in candidates:
        candidate = _normalize_candidate(raw, city, country, sector, raw.get("source", "web"))
        if candidate and candidate["website"] not in seen:
            seen.add(candidate["website"])
            unique_candidates.append(candidate)

    qualified = []
    new_count = old_count = 0
    active_session = session
    close_session = False
    if organization_id and active_session is None:
        active_session = SessionLocal()
        close_session = True

    try:
        for index, candidate in enumerate(unique_candidates):
            if len(qualified) >= target:
                break
            if progress_callback:
                fraction = 0.08 + 0.88 * index / max(len(unique_candidates), 1)
                progress_callback(fraction, f"Analizando y calificando {index + 1}/{len(unique_candidates)} sitios…")
            analysis = analyze_company_website(candidate["website"])
            if not analysis.get("ok") or analysis.get("signals", {}).get("text_len", 0) < 60:
                continue

            contacts = extract_contact_signals(candidate, analysis)
            lead = {**candidate, **contacts}
            score_result = scoring.score_lead(service, lead, analysis)
            diagnosis = _diagnose_need(service, analysis)
            has_contact_path = any(contacts.get(key) for key in ("email", "phone", "linkedin", "instagram")) or contacts["contact_form"]
            if score_result["detail"].get("Necesidad", 0) <= 0 or score_result["score"] < MIN_QUALIFIED_SCORE or not has_contact_path:
                continue

            outreach = messages.build_message(
                business,
                lead,
                analysis.get("signals", {}),
                sender=sender,
                service_profile=service,
            )
            lead_result = {
                "name": lead["name"],
                "website": lead["website"],
                "sector": lead["sector"],
                "city": lead["city"],
                "country": lead["country"],
                "email": contacts["email"],
                "phone": contacts["phone"],
                "linkedin": contacts["linkedin"],
                "instagram": contacts["instagram"],
                "contact_form": contacts["contact_form"],
                "score": score_result["score"],
                "diagnosis": diagnosis,
                "outreach": outreach,
                "source": lead["source"],
                "evidence": score_result["evidence"],
                "inferences": score_result["inferences"],
            }
            created = _persist_qualified_lead(
                business,
                service,
                lead,
                analysis,
                score_result,
                diagnosis,
                organization_id,
                active_session,
            )
            new_count += int(created)
            old_count += int(not created)
            qualified.append(lead_result)
    finally:
        if close_session and active_session is not None:
            active_session.close()

    if progress_callback:
        progress_callback(1.0, f"Listos: {len(qualified)} prospectos calificados.")
    return {
        "service": service,
        "city": city,
        "country": country,
        "sector": sector,
        "new_leads": new_count,
        "existing_leads": old_count,
        "errors": errors,
        "leads": qualified,
    }