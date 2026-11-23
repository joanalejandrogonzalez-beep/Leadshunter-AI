"""Base de datos SQLite. Novus Ops y NTO Productions comparten tabla pero SIEMPRE se filtra por 'business'."""
import hashlib
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from leadhunter.auth import hash_password, verify_password

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "leadhunter.db"
BUSINESSES = ["Novus Ops", "NTO Productions"]
STATUSES = ["Nuevo", "Contactado", "Respondió", "Reunión", "Propuesta", "Ganado", "Perdido", "Descartado"]
FIELDS = ["name", "website", "phone", "email", "instagram", "country", "city", "sector", "source", "address"]


def get_available_businesses():
    """Devuelve las empresas registradas en la base de datos o una lista por defecto."""
    try:
        with connect() as con:
            rows = con.execute("""
                SELECT name FROM businesses
                UNION
                SELECT DISTINCT business AS name FROM leads WHERE business != ''
                ORDER BY name
            """).fetchall()
            names = [r["name"] for r in rows if r["name"]]
            return names if names else BUSINESSES.copy()
    except Exception:
        return BUSINESSES.copy()


def get_user_by_email(email):
    """Devuelve el perfil del usuario registrado o None si no existe."""
    if not email:
        return None
    normalized = str(email).strip().lower()
    if not normalized:
        return None
    with connect() as con:
        row = con.execute(
            "SELECT * FROM users WHERE lower(email)=?",
            (normalized,),
        ).fetchone()
        return dict(row) if row else None


def create_user_account(email, password, first_name="", last_name="", role="", age=0):
    """Crea una cuenta con contraseña segura usando bcrypt."""
    if not email or not password:
        return None
    normalized = str(email).strip().lower()
    if not normalized:
        return None
    with connect() as con:
        existing = con.execute("SELECT * FROM users WHERE lower(email)=?", (normalized,)).fetchone()
        if existing:
            if existing["password_hash"]:
                return dict(existing)
            con.execute(
                "UPDATE users SET password_hash=?, first_name=?, last_name=?, role=?, age=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (hash_password(password), str(first_name or existing["first_name"] or "").strip(), str(last_name or existing["last_name"] or "").strip(), str(role or existing["role"] or "").strip(), int(age or existing["age"] or 0), existing["id"]),
            )
            con.commit()
            updated = con.execute("SELECT * FROM users WHERE id=?", (existing["id"],)).fetchone()
            return dict(updated)

        cur = con.execute(
            "INSERT INTO users(email, password_hash, first_name, last_name, role, age) VALUES (?, ?, ?, ?, ?, ?)",
            (normalized, hash_password(password), str(first_name or "").strip(), str(last_name or "").strip(), str(role or "").strip(), int(age or 0)),
        )
        con.commit()
        saved = con.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(saved)


def authenticate_user(email, password):
    """Valida credenciales de login y devuelve el usuario si coincide."""
    if not email or not password:
        return None
    normalized = str(email).strip().lower()
    if not normalized:
        return None
    with connect() as con:
        row = con.execute("SELECT * FROM users WHERE lower(email)=?", (normalized,)).fetchone()
        if not row or not row["password_hash"]:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        return dict(row)


def create_remembered_session(email, ttl_days=30):
    """Create a revocable persistent session; only its token digest is stored."""
    normalized = str(email or "").strip().lower()
    if not normalized:
        raise ValueError("A valid user email is required to create a session.")

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.blake2b(token.encode("utf-8"), digest_size=32).hexdigest()
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=ttl_days)).isoformat()

    with connect() as con:
        user = con.execute(
            "SELECT id FROM users WHERE lower(email)=?",
            (normalized,),
        ).fetchone()
        if not user:
            raise LookupError("Cannot create a remembered session for an unknown user.")

        con.execute(
            "DELETE FROM remembered_sessions WHERE expires_at<=?",
            (now.isoformat(),),
        )
        con.execute(
            "INSERT INTO remembered_sessions(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (token_hash, user["id"], expires_at),
        )
    return token


def get_user_by_remembered_session(token):
    """Return a user for a valid, unexpired remembered-session token."""
    if not token:
        return None
    token_hash = hashlib.blake2b(str(token).encode("utf-8"), digest_size=32).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    with connect() as con:
        row = con.execute(
            "SELECT users.* FROM users "
            "JOIN remembered_sessions ON remembered_sessions.user_id=users.id "
            "WHERE remembered_sessions.token_hash=? AND remembered_sessions.expires_at>?",
            (token_hash, now),
        ).fetchone()
        return dict(row) if row else None


def revoke_remembered_session(token):
    """Revoke a remembered session by deleting its token digest."""
    if not token:
        return
    token_hash = hashlib.blake2b(str(token).encode("utf-8"), digest_size=32).hexdigest()
    with connect() as con:
        con.execute("DELETE FROM remembered_sessions WHERE token_hash=?", (token_hash,))


def upsert_user(email, first_name="", last_name="", role="", age=0):
    """Crea o actualiza un usuario en la base de datos y devuelve su perfil."""
    if not email:
        return None
    normalized = str(email).strip().lower()
    if not normalized:
        return None
    with connect() as con:
        row = con.execute("SELECT * FROM users WHERE lower(email)=?", (normalized,)).fetchone()
        if row:
            con.execute(
                "UPDATE users SET first_name=?, last_name=?, role=?, age=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(first_name or row["first_name"] or "").strip(),
                 str(last_name or row["last_name"] or "").strip(),
                 str(role or row["role"] or "").strip(),
                 int(age or row["age"] or 0),
                 row["id"]),
            )
            con.commit()
            updated = con.execute("SELECT * FROM users WHERE id=?", (row["id"],)).fetchone()
            return dict(updated)

        cur = con.execute(
            "INSERT INTO users(email, password_hash, first_name, last_name, role, age) VALUES (?, ?, ?, ?, ?, ?)",
            (normalized, "", str(first_name or "").strip(), str(last_name or "").strip(), str(role or "").strip(), int(age or 0)),
        )
        con.commit()
        saved = con.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(saved)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT DEFAULT '',
  first_name TEXT DEFAULT '',
  last_name TEXT DEFAULT '',
  role TEXT DEFAULT '',
  age INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS remembered_sessions(
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS businesses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
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


def register_business(name: str):
    """Registra una nueva empresa en la base de datos de manera persistente."""
    if not name or not name.strip():
        return
    clean_name = name.strip()
    with connect() as con:
        con.execute("INSERT OR IGNORE INTO businesses(name) VALUES (?)", (clean_name,))


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    user_cols = con.execute("PRAGMA table_info(users)").fetchall()
    existing_cols = {row[1] for row in user_cols}
    if "password_hash" not in existing_cols:
        con.execute("ALTER TABLE users ADD COLUMN password_hash TEXT DEFAULT ''")
    if "first_name" not in existing_cols:
        con.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT ''")
    if "last_name" not in existing_cols:
        con.execute("ALTER TABLE users ADD COLUMN last_name TEXT DEFAULT ''")
    if "role" not in existing_cols:
        con.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT ''")
    if "age" not in existing_cols:
        con.execute("ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 0")
    # Sembrar empresas iniciales si businesses está vacía
    for b in BUSINESSES:
        con.execute("INSERT OR IGNORE INTO businesses(name) VALUES (?)", (b,))
    con.commit()
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
