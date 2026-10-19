"""Analiza la web de una empresa. Separa HECHOS observados (verificados en la página)
de SEÑALES que luego se interpretan como inferencias en scoring.py."""
import re
import time
from datetime import datetime
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "LeadHunterAI/1.0 (+investigacion comercial manual)"
HEAD = {"User-Agent": UA, "Accept-Language": "es,en;q=0.8"}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?\(?(?:809|829|849)\)?[\s.-]?\d{3}[\s.-]?\d{4}")
BAD_EMAIL = ("sentry", "example.", "wixpress", "domain.com", "email.com", ".png", ".jpg", ".webp", ".svg", ".gif", "u003e")
PAGE_HINTS = ("contact", "nosotros", "about", "servicio", "proyecto", "propiedad", "listing", "catalogo", "productos")
INSTA_RE = re.compile(r"instagram\.com/([A-Za-z0-9._]{2,30})/?")


def _allowed(url):
    try:
        p = urlparse(url)
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch(UA, url)
    except Exception:
        return True  # sin robots.txt accesible: se permite una lectura ligera


def _get(url):
    r = requests.get(url, headers=HEAD, timeout=15, allow_redirects=True)
    r.raise_for_status()
    return r


def analyze_site(website, max_pages=4):
    """Devuelve dict con 'ok', 'facts' (observado), 'signals' y 'error'."""
    if not website:
        return {"ok": False, "error": "Sin web", "facts": {}, "signals": {}}
    url = website if website.startswith("http") else "https://" + website
    if not _allowed(url):
        return {"ok": False, "error": "robots.txt no permite el análisis", "facts": {}, "signals": {}}
    try:
        first = _get(url)
    except Exception as e:
        return {"ok": False, "error": f"No se pudo abrir la web: {type(e).__name__}", "facts": {}, "signals": {}}

    pages = {first.url: first.text}
    soup0 = BeautifulSoup(first.text, "html.parser")
    host = urlparse(first.url).netloc
    links = []
    for a in soup0.find_all("a", href=True):
        u = urljoin(first.url, a["href"]).split("#")[0]
        if urlparse(u).netloc == host and any(h in u.lower() for h in PAGE_HINTS) and u not in links:
            links.append(u)
    for u in links[: max_pages - 1]:
        try:
            time.sleep(1)
            if _allowed(u):
                pages[u] = _get(u).text
        except Exception:
            pass
    return analyze_html(pages, final_url=first.url, https=first.url.startswith("https"))


def analyze_html(pages, final_url="", https=True):
    """pages: {url: html}. Separado de la red para poder probarlo offline."""
    all_html = "\n".join(pages.values())
    soups = [BeautifulSoup(h, "html.parser") for h in pages.values()]
    text = " ".join(s.get_text(" ", strip=True) for s in soups).lower()
    lower_html = all_html.lower()
    host = re.sub(r"^www\.", "", urlparse(final_url).netloc) if final_url else ""

    emails = {e.lower() for e in EMAIL_RE.findall(all_html) if not any(b in e.lower() for b in BAD_EMAIL)}
    emails = sorted(emails, key=lambda e: (host not in e, e))
    phones = []
    for s in soups:
        for a in s.select('a[href^="tel:"]'):
            phones.append(re.sub(r"[^\d+]", "", a["href"][4:]))
    phones += [re.sub(r"\D", "", m) for m in PHONE_RE.findall(text)]
    phones = list(dict.fromkeys(p for p in phones if len(p) >= 10))
    instas = [h for h in INSTA_RE.findall(all_html) if h.lower() not in ("p", "reel", "explore", "accounts", "sharer")]
    insta = f"https://instagram.com/{instas[0]}" if instas else ""

    years = [int(y) for y in re.findall(r"(?:©|copyright|&copy;)[^0-9]{0,30}((?:19|20)\d\d)", lower_html)]
    generator = ""
    for s in soups:
        m = s.find("meta", attrs={"name": "generator"})
        if m and m.get("content"):
            generator = m["content"][:40]
            break
    cms = next((n for n, k in (("WordPress", "wp-content"), ("Wix", "wixstatic"), ("Squarespace", "squarespace"),
                               ("Shopify", "cdn.shopify"), ("Webflow", "webflow")) if k in lower_html), "")

    kw = lambda *w: sum(text.count(x) for x in w)
    facts = {
        "emails": emails[:3], "phones": phones[:3], "instagram": insta,
        "https": https, "cms": cms or generator, "pages_read": len(pages),
        "last_copyright_year": max(years) if years else None,
    }
    signals = {
        "has_viewport": 'name="viewport"' in lower_html or "name='viewport'" in lower_html,
        "has_form": any(s.find("form") for s in soups),
        "has_whatsapp": "wa.me" in lower_html or "api.whatsapp" in lower_html or "whatsapp" in text,
        "has_video": ("<video" in lower_html or "youtube.com/embed" in lower_html or "player.vimeo" in lower_html
                      or "youtu.be" in lower_html),
        "has_portal": any(w in text for w in ("portal de clientes", "área de clientes", "area de clientes", "mi cuenta", "iniciar sesión", "login")),
        "has_quote_cta": any(w in text for w in ("cotiza", "solicita", "agenda", "reserva", "book now", "request a quote")),
        "has_social_instagram": bool(insta),
        "listing_mentions": kw("propiedades", "proyectos", "apartamentos", "villas", "listings", "inmuebles", "residencial"),
        "catalog_mentions": kw("productos", "catálogo", "catalogo", "inventario", "marcas", "distribuidor"),
        "branch_mentions": kw("sucursal", "sucursales", "sedes", "oficinas", "branch"),
        "luxury_mentions": kw("lujo", "luxury", "frente al mar", "beachfront", "pre-venta", "preventa", "premium", "exclusiv"),
        "project_mentions": kw("proyecto", "obra", "construcción", "construccion", "entregado", "en construcción"),
        "text_len": len(text),
    }
    return {"ok": True, "error": "", "facts": facts, "signals": signals,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
