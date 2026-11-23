"""Módulo de autenticación y seguridad para LeadHunter AI SaaS.
Gestión de contraseñas con bcrypt y generación/validación de JWT.
"""
import os
import secrets
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

_DEV_SECRET_KEY = None


def _get_secret_key() -> str:
    global _DEV_SECRET_KEY
    key = os.getenv("JWT_SECRET_KEY")
    if key:
        return key
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        raise RuntimeError("CRITICAL SECURITY ERROR: JWT_SECRET_KEY must be set in production environment!")
    if _DEV_SECRET_KEY is None:
        _DEV_SECRET_KEY = secrets.token_urlsafe(32)
    return _DEV_SECRET_KEY


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días


def hash_password(password: str) -> str:
    """Genera un hash seguro mediante bcrypt con sal aleatoria."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con su hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Crea un token JWT firmado."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Valida y decodifica un token JWT. Lanza excepciones de JWT si es inválido o expiró."""
    return jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
