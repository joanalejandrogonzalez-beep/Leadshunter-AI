"""Prueba de humo sin internet: servidor local + fuentes simuladas. Ejecuta: python test_smoke.py"""
import json, tempfile, threading, http.server, functools, pathlib
from leadhunter import db, pipeline, sources, messages

tmp = pathlib.Path(tempfile.mkdtemp())
db.DB_PATH = tmp / "t.db"

SITE = tmp / "site"; SITE.mkdir()
(SITE / "index.html").write_text("""<html><head><meta name="generator" content="WordPress 6"></head><body>
<a href="/contacto.html">Contacto</a><a href="https://instagram.com/constructora_demo/">IG</a>
<p>Proyectos residenciales, 20 proyectos entregados. Proyecto proyecto proyecto proyecto proyecto obra obra construcción construcción.
Sucursales: dos sucursales y oficinas. propiedades propiedades propiedades propiedades propiedades</p>
<footer>© 2019 Demo SRL</footer></body></html>""")
(SITE / "contacto.html").write_text("""<html><body><a href="tel:+18095550123">Llamar</a> ventas@demo-srl.do info@wixpress.com</body></html>""")
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
handler.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_port}"

# 1. Duplicados y separación por negocio
a, c1 = db.upsert_lead("Novus Ops", {"name": "Demo SRL", "website": url, "city": "SD", "sector": "Constructoras"})
b, c2 = db.upsert_lead("Novus Ops", {"name": "Demo S.R.L.", "website": url + "/", "phone": "809-555-0123"})
assert c1 and not c2 and a == b, "dedupe falló"
assert db.get_lead(a)["phone"] == "809-555-0123", "no completó campo vacío"
n, _ = db.upsert_lead("NTO Productions", {"name": "Demo SRL", "website": url, "sector": "Inmobiliarias"})
assert len(db.leads_df("Novus Ops")) == 1 and len(db.leads_df("NTO Productions")) == 1
print("OK duplicados + separación de negocios")

# 2. Análisis real contra servidor local + scoring
pipeline.analyze_and_score(a); pipeline.analyze_and_score(n)
l1, l2 = db.get_lead(a), db.get_lead(n)
assert l1["email"] == "ventas@demo-srl.do", l1["email"]          # filtra wixpress
assert l1["instagram"].endswith("constructora_demo") and l1["analyzed"] == 1
assert 0 < l1["score"] <= 100 and 0 < l2["score"] <= 100
sd = json.loads(l1["score_detail"]); assert sum(sd["detail"].values()) == l1["score"]
assert any("copyright 2019" in e for e in json.loads(l1["evidence"]))
print("OK análisis+scoring: Novus", l1["score"], "NTO", l2["score"], sd["detail"])

# 3. Mensajes
for biz, l in (("Novus Ops", l1), ("NTO Productions", l2)):
    for lang in ("es", "en"):
        m = messages.build_message(biz, l, json.loads(l["score_detail"])["signals"], lang, "Yo")
        assert biz in m and "{" not in m
print("OK mensajes\n---\n" + messages.build_message("NTO Productions", l2, json.loads(l2["score_detail"])["signals"], "es", "Yo") + "\n---")

# 4. CSV
csvp = tmp / "x.csv"; csvp.write_text("nombre;web;ciudad\nAcme Inmob;;Santiago\nDemo SRL;" + url + ";SD\n", encoding="utf-8")
new, old = pipeline.import_csv("Novus Ops", str(csvp), country="RD", sector="Inmobiliarias", analyze=False)
assert (new, old) == (1, 1), (new, old)
print("OK import CSV (1 nuevo, 1 duplicado)")

# 5. Fuentes simuladas (sin red)
class R:
    def __init__(s, j=None, t="", code=200): s._j, s.text, s.status_code = j, t, code
    def json(s): return s._j
    def raise_for_status(s): pass
sources.requests.get = lambda *a, **k: R([{"boundingbox": ["18.4", "18.6", "-70.0", "-69.8"]}])
sources.requests.post = lambda u, **k: R({"elements": [
    {"tags": {"name": "Inmob Real OSM", "website": "https://inmob.example", "contact:instagram": "@inmob", "phone": "+1 809 555 0000"}},
    {"tags": {"office": "estate_agent"}}]}) if "overpass" in u else R(t='<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.buscada.example%2Fx">Buscada Inmobiliaria | Santo Domingo</a><a class="result__a" href="https://facebook.com/x">fb</a>')
o = sources.search_osm("Santo Domingo", "RD", "Inmobiliarias"); w = sources.search_web("Santo Domingo", "RD", "Inmobiliarias")
assert len(o) == 1 and o[0]["instagram"] == "https://instagram.com/inmob" and o[0]["source"] == "OpenStreetMap"
assert len(w) == 1 and w[0]["website"] == "https://www.buscada.example" and w[0]["name"] == "Buscada Inmobiliaria"
print("OK parseo OSM y DuckDuckGo (simulado)")

# 6. Programadas
db.save_search("Novus Ops", "RD", "SD", "Inmobiliarias", ["OpenStreetMap"], 5)
assert len(db.saved_searches()) == 1
print("\nTODAS LAS PRUEBAS OK")
