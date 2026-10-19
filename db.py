"""Base de datos SQLite. Novus Ops y NTO Productions comparten tabla pero SIEMPRE se filtra por 'business'."""
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "leadhunter.db"
BUSINESSES = ["Novus Ops", "NTO Productions"]
STATUSES = ["Nuevo", "Contactado", "Respondió", "Reunión", "Propuesta", "Ganado", "Perdido", "Descartado"]
FIELDS = ["name", "website", "phone", "email", "instagram", "country", "city", "sector", "source", "address"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  business TEXT NOT NULL, dedupe_key TEXT NOT NULL,
  name TEXT NOT NULL, website TEXT, phone TEXT, email TEXT, instagram TEXT,
  country TEXT, city TEXT, sector TEXT, source TEXT, address TEXT,
  score INTEGER DEFAULT 0, score_detail TEXT, evidence TEXT, inferences TEXT,
  status TEXT DEFAULT 'Nuevo', notes TEXT DEFAULT '', next_followup TEXT,
  analyzed INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(business, dedupe_key));
CREATE TABLE IF NOT EXISTS saved_searches(
  id INTEGER PRIMARY KEY AUTOINCREMENT, business TEXT, country TEXT, city TEXT,
  sector TEXT, sources TEXT, max_results INTEGER, last_run TEXT);
"""


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def domain_of(url):
    if not url:
        return ""
    if "//" not in url:
        url = "http://" + url
    host = urlparse(url).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def dedupe_key(lead):
    d = domain_of(lead.get("website"))
    if d:
        return "d:" + d
    norm = re.sub(r"[^a-z0-9]", "", (lead.get("name") or "").lower())
    return f"n:{norm}:{(lead.get('city') or '').lower().strip()}"


def upsert_lead(business, lead):
    """Inserta o completa un lead. Devuelve (id, creado:bool)."""
    key = dedupe_key(lead)
    with connect() as con:
        row = con.execute("SELECT * FROM leads WHERE business=? AND dedupe_key=?", (business, key)).fetchone()
        if row:  # completar solo campos vacíos
            for f in FIELDS:
                if lead.get(f) and not row[f]:
                    con.execute(f"UPDATE leads SET {f}=? WHERE id=?", (lead[f], row["id"]))
            return row["id"], False
        cols = ["business", "dedupe_key"] + FIELDS
        vals = [business, key] + [lead.get(f, "") or "" for f in FIELDS]
        cur = con.execute(f"INSERT INTO leads({','.join(cols)}) VALUES({','.join('?' * len(cols))})", vals)
        return cur.lastrowid, True


def get_lead(lead_id):
    with connect() as con:
        r = con.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        return dict(r) if r else None


def update_lead(lead_id, **fields):
    if not fields:
        return
    with connect() as con:
        sets = ",".join(f"{k}=?" for k in fields)
        con.execute(f"UPDATE leads SET {sets} WHERE id=?", [*fields.values(), lead_id])


def delete_lead(lead_id):
    with connect() as con:
        con.execute("DELETE FROM leads WHERE id=?", (lead_id,))


def leads_df(business, status=None, min_score=0, text=""):
    q, p = "SELECT * FROM leads WHERE business=? AND score>=?", [business, min_score]
    if status and status != "Todos":
        q += " AND status=?"
        p.append(status)
    if text:
        q += " AND (name LIKE ? OR city LIKE ? OR sector LIKE ?)"
        p += [f"%{text}%"] * 3
    q += " ORDER BY score DESC, id DESC"
    with connect() as con:
        return pd.read_sql_query(q, con, params=p)


def due_followups(business, today):
    with connect() as con:
        rows = con.execute(
            "SELECT id,name,next_followup,status FROM leads WHERE business=? AND next_followup!='' "
            "AND next_followup<=? AND status NOT IN ('Ganado','Perdido','Descartado') ORDER BY next_followup",
            (business, today)).fetchall()
        return [dict(r) for r in rows]


def save_search(business, country, city, sector, sources, max_results):
    with connect() as con:
        con.execute("INSERT INTO saved_searches(business,country,city,sector,sources,max_results) VALUES(?,?,?,?,?,?)",
                    (business, country, city, sector, ",".join(sources), max_results))


def saved_searches():
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM saved_searches")]


def delete_search(sid):
    with connect() as con:
        con.execute("DELETE FROM saved_searches WHERE id=?", (sid,))


def mark_search_run(sid, ts):
    with connect() as con:
        con.execute("UPDATE saved_searches SET last_run=? WHERE id=?", (ts, sid))
