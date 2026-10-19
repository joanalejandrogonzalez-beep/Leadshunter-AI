"""Fuentes gratuitas y públicas, sin claves de API:
 - OpenStreetMap (Nominatim + Overpass): datos abiertos de empresas con etiquetas públicas.
 - DuckDuckGo (versión HTML, uso ligero y con pausas): descubre webs corporativas.
 - Importación CSV (siempre disponible como alternativa).
Nunca se inventa nada: solo se devuelve lo que la fuente entrega."""
import re
import time
from urllib.parse import parse_qs, unquote, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "LeadHunterAI/1.0 (investigacion comercial manual; contacto personal)"}

SECTORS = {
    "Constructoras": {
        "osm": ['["office"="construction_company"]', '["craft"="builder"]', '["name"~"constructora|construcciones",i]["office"]'],
        "web": "constructora",
    },
    "Inmobiliarias": {
        "osm": ['["office"="estate_agent"]', '["name"~"inmobiliaria|real estate|bienes ra",i]'],
        "web": "inmobiliaria",
    },
    "Distribuidoras": {
        "osm": ['["shop"="wholesale"]', '["name"~"distribuidora|distribuciones|importadora",i]'],
        "web": "distribuidora",
    },
    "Propiedades vacacionales": {
        "osm": ['["tourism"~"apartment|guest_house|chalet"]', '["name"~"villa|vacation rental|property management",i]["tourism"]'],
        "web": "villas alquiler vacacional administradora de propiedades",
    },
}

SKIP_DOMAINS = ("facebook.", "instagram.", "linkedin.", "youtube.", "twitter.", "x.com", "tiktok.", "wikipedia.",
                "tripadvisor.", "yelp.", "paginasamarillas", "airbnb.", "booking.com", "mercadolibre", "olx.",
                "corotos.", "pinterest.", "google.", "bing.", "duckduckgo.", "amazon.", "vrbo.", "expedia.")


def geocode(city, country):
    r = requests.get("https://nominatim.openstreetmap.org/search", headers=UA, timeout=20,
                     params={"q": f"{city}, {country}", "format": "json", "limit": 1})
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"No se encontró la ubicación '{city}, {country}' en OpenStreetMap.")
    s, n, w, e = (float(x) for x in data[0]["boundingbox"])
    return s, w, n, e


def _osm_lead(tags, city, country, sector):
    g = lambda *k: next((tags[x] for x in k if tags.get(x)), "")
    addr = " ".join(filter(None, [tags.get("addr:street"), tags.get("addr:housenumber")]))
    insta = g("contact:instagram", "instagram")
    if insta and not insta.startswith("http"):
        insta = "https://instagram.com/" + insta.lstrip("@")
    return {"name": tags.get("name", "").strip(), "website": g("website", "contact:website", "url"),
            "phone": g("phone", "contact:phone"), "email": g("email", "contact:email"), "instagram": insta,
            "address": addr, "city": city, "country": country, "sector": sector, "source": "OpenStreetMap"}


def search_osm(city, country, sector, limit=50):
    s, w, n, e = geocode(city, country)
    filters = SECTORS[sector]["osm"]
    body = "".join(f"nwr{f}({s},{w},{n},{e});" for f in filters)
    q = f"[out:json][timeout:40];({body});out tags center {limit * 3};"
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=UA, timeout=60)
    r.raise_for_status()
    out = []
    for el in r.json().get("elements", []):
        lead = _osm_lead(el.get("tags", {}), city, country, sector)
        if lead["name"]:
            out.append(lead)
    return out[:limit]


def _real_url(href):
    if "uddg=" in href:
        href = unquote(parse_qs(urlparse(href).query).get("uddg", [""])[0])
    return href


def search_web(city, country, sector, limit=20):
    """Descubre webs corporativas vía DuckDuckGo HTML (sin clave). Uso ligero."""
    out, seen = [], set()
    term = SECTORS[sector]["web"]
    for q in (f"{term} {city} {country}", f"{term} {city} contacto"):
        r = requests.post("https://html.duckduckgo.com/html/", data={"q": q}, headers=UA, timeout=25)
        if r.status_code != 200:
            continue
        for a in BeautifulSoup(r.text, "html.parser").select("a.result__a"):
            url = _real_url(a.get("href", ""))
            p = urlparse(url)
            host = p.netloc.lower()
            if not p.scheme.startswith("http") or any(sd in host for sd in SKIP_DOMAINS) or host in seen:
                continue
            seen.add(host)
            title = re.split(r"\s[\|\-–—]\s", a.get_text(" ", strip=True))[0][:80]
            out.append({"name": title or host, "website": f"{p.scheme}://{host}", "city": city, "country": country,
                        "sector": sector, "source": "DuckDuckGo"})
        time.sleep(2)
        if len(out) >= limit:
            break
    return out[:limit]


def read_csv(file_or_path, default_city="", default_country="", default_sector=""):
    """Importa empresas desde CSV. Columnas (cualquiera): name/nombre, website/web, phone/telefono,
    email/correo, instagram, city/ciudad, country/pais, sector, address/direccion."""
    df = pd.read_csv(file_or_path, dtype=str, keep_default_na=False, encoding_errors="replace", sep=None, engine="python")
    alias = {"nombre": "name", "empresa": "name", "company": "name", "web": "website", "sitio": "website",
             "url": "website", "telefono": "phone", "teléfono": "phone", "correo": "email", "ciudad": "city",
             "pais": "country", "país": "country", "sector": "sector", "direccion": "address", "dirección": "address"}
    df.columns = [alias.get(c.strip().lower(), c.strip().lower()) for c in df.columns]
    if "name" not in df.columns:
        raise ValueError("El CSV necesita al menos una columna 'name' (o 'nombre'/'empresa').")
    leads = []
    for _, r in df.iterrows():
        if not r["name"].strip():
            continue
        lead = {k: r.get(k, "").strip() for k in ("name", "website", "phone", "email", "instagram", "city", "country", "sector", "address")}
        lead["city"] = lead["city"] or default_city
        lead["country"] = lead["country"] or default_country
        lead["sector"] = lead["sector"] or default_sector
        lead["source"] = "CSV"
        leads.append(lead)
    return leads
