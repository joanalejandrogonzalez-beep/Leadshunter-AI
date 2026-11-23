"""Capa de conexión a base de datos relacional para LeadHunter AI SaaS.
Soporte dual: SQLite (desarrollo/testing) y PostgreSQL (producción/staging).
"""
import os
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models.schema import Base, User

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "leadhunter_v2.db"
LEGACY_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "leadhunter.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

# Argumentos de conexión según motor
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def init_db():
    Base.metadata.create_all(bind=engine)
    migrate_legacy_users()


def migrate_legacy_users(source_path=LEGACY_DB_PATH):
    """Carry over Streamlit users with existing password hashes into the SaaS database."""
    if not source_path.exists():
        return 0

    legacy = sqlite3.connect(source_path)
    legacy.row_factory = sqlite3.Row
    try:
        tables = legacy.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if not tables:
            return 0

        columns = {row["name"] for row in legacy.execute("PRAGMA table_info(users)")}
        required = {"email", "password_hash"}
        if not required.issubset(columns):
            return 0
        rows = legacy.execute(
            "SELECT email, password_hash, first_name, last_name FROM users"
            if {"first_name", "last_name"}.issubset(columns)
            else "SELECT email, password_hash, '' AS first_name, '' AS last_name FROM users"
        ).fetchall()
    finally:
        legacy.close()

    session = SessionLocal()
    migrated = 0
    try:
        for row in rows:
            email = str(row["email"] or "").strip().lower()
            password_hash = str(row["password_hash"] or "").strip()
            if not email or not password_hash:
                continue
            exists = session.query(User.id).filter(User.email == email).first()
            if exists:
                continue
            full_name = " ".join(
                part.strip()
                for part in (row["first_name"], row["last_name"])
                if part and part.strip()
            ) or "Usuario"
            session.add(User(email=email, password_hash=password_hash, full_name=full_name))
            migrated += 1
        session.commit()
        return migrated
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
