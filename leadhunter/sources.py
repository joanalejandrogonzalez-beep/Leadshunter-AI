"""Fuentes gratuitas y públicas, sin claves de API:
 - OpenStreetMap (Nominatim + Overpass): datos abiertos de empresas con etiquetas públicas.
 - DuckDuckGo (versión HTML, uso ligero y con pausas): descubre webs corporativas.
 - Importación CSV (siempre disponible como alternativa).
Nunca se inventa nada: solo se devuelve lo que la fuente entrega."""
import json
import random
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "LeadHunterAI/1.0 (+https://leadhunter.ai; contact: ops@leadhunter.ai)"}

GEO_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "geo_cache.json"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

_last_nominatim_call = 0.0
_geo_cache = None


def _load_geo_cache():
    global _geo_cache
    if _geo_cache is not None:
        return _geo_cache
    if GEO_CACHE_FILE.exists():
        try:
            _geo_cache = json.loads(GEO_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _geo_cache = {}
    else:
        _geo_cache = {}
    return _geo_cache


def _save_geo_cache():
    if _geo_cache is not None:
        try:
            GEO_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            GEO_CACHE_FILE.write_text(json.dumps(_geo_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

SECTORS = {
    "Constructoras": {
        "osm": ['["office"="construction_company"]', '["craft"="builder"]'],
        "web": "constructora",
    },
    "Inmobiliarias": {
        "osm": ['["office"="estate_agent"]', '["shop"="estate_agent"]'],
        "web": "inmobiliaria",
    },
    "Distribuidoras": {
        "osm": ['["shop"="wholesale"]'],
        "web": "distribuidora",
    },
    "Propiedades vacacionales": {
        "osm": ['["tourism"~"apartment|guest_house|chalet"]'],
        "web": "villas alquiler vacacional administradora de propiedades",
    },
    "Clínicas dentales": {
        "osm": ['["amenity"="dentist"]', '["healthcare"="dentist"]'],
        "web": "clinica dental odontologia",
    },
    "Agencias de marketing": {
        "osm": ['["office"="advertising_agency"]', '["office"="marketing"]'],
        "web": "agencia marketing digital",
    },
    "Restaurantes": {
        "osm": ['["amenity"="restaurant"]'],
        "web": "restaurante",
    },
    "Hoteles": {
        "osm": ['["tourism"="hotel"]'],
        "web": "hotel",
    },
    "Abogados / Legal": {
        "osm": ['["office"="lawyer"]'],
        "web": "abogados bufete legal",
    },
    "Gimnasios / Fitness": {
        "osm": ['["leisure"="fitness_centre"]'],
        "web": "gimnasio fitness",
    },
}


def get_sector_config(sector_name):
    if sector_name in SECTORS:
        return SECTORS[sector_name]
    norm = re.sub(r"[^a-zA-Z0-9\s]", "", sector_name or "").strip().lower()
    first_word = norm.split()[0] if norm else "comercial"
    return {
        "osm": [f'["office"~"{first_word}",i]', f'["shop"~"{first_word}",i]', f'["name"~"{first_word}",i]["office"]'],
        "web": sector_name.lower() if sector_name else "empresa"
    }

SKIP_DOMAINS = ("facebook.", "instagram.", "linkedin.", "youtube.", "twitter.", "x.com", "tiktok.", "wikipedia.",
                "tripadvisor.", "yelp.", "paginasamarillas", "airbnb.", "booking.com", "mercadolibre", "olx.",
                "corotos.", "pinterest.", "google.", "bing.", "duckduckgo.", "amazon.", "vrbo.", "expedia.")


def geocode(city, country):
    global _last_nominatim_call
    cache = _load_geo_cache()
    key = f"{city.strip().lower()}:{country.strip().lower()}"
    if key in cache:
        return tuple(cache[key])

    now = time.time()
    elapsed = now - _last_nominatim_call
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)

    _last_nominatim_call = time.time()
    r = None
    for attempt in range(2):
        try:
            r = requests.get("https://nominatim.openstreetmap.org/search", headers=UA, timeout=20,
                             params={"q": f"{city}, {country}", "format": "json", "limit": 1})
            if r.status_code == 429:
                if attempt == 0:
                    time.sleep(2.0)
                    continue
                raise RuntimeError("Límite de solicitudes de geocodificación (HTTP 429). Espera unos segundos o usa CSV.")
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 1:
                raise
            time.sleep(1.5)

    data = r.json()
    if not data:
        raise ValueError(f"No se encontró la ubicación '{city}, {country}' en OpenStreetMap.")
    first = data[0]
    s, n, w, e = (float(x) for x in first["boundingbox"])
    res = (s, w, n, e)
    cache[key] = res
    _save_geo_cache()
    return res


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
    filters = get_sector_config(sector)["osm"]
    dlat = abs(n - s)
    dlon = abs(e - w)
    
    # En grandes metrópolis (área > ~15km), una búsqueda radial al centro urbano evita timeouts en servidores públicos
    if dlat > 0.15 or dlon > 0.15:
        lat = (s + n) / 2
        lon = (w + e) / 2
        body = "".join(f"nwr{f}(around:12000,{lat},{lon});" for f in filters)
    else:
        body = "".join(f"nwr{f}({s},{w},{n},{e});" for f in filters)
    
    q = f"[out:json][timeout:25];({body});out tags center {limit * 2};"

    data = None
    last_err = ""
    for mirror in OVERPASS_ENDPOINTS:
        try:
            r = requests.post(mirror, data={"data": q}, headers=UA, timeout=25)
            if r.status_code == 200:
                data = r.json()
                break
            elif r.status_code in (429, 502, 503, 504):
                last_err = f"Mirror {mirror} status {r.status_code}"
                time.sleep(0.3 + random.random() * 0.3)
                continue
            else:
                r.raise_for_status()
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue

    if data is None:
        # Reintento con backoff breve
        time.sleep(1.5 + random.random())
        for mirror in OVERPASS_ENDPOINTS:
            try:
                r = requests.post(mirror, data={"data": q}, headers=UA, timeout=25)
                if r.status_code == 200:
                    data = r.json()
                    break
            except Exception:
                continue

    if data is None:
        raise RuntimeError(f"Servidores de OpenStreetMap saturados ({last_err}). Prueba DuckDuckGo o importa tu CSV.")

    out = []
    for el in data.get("elements", []):
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
    term = get_sector_config(sector)["web"]
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
