from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.schemas import LoginRequest, RegisterRequest
from leadhunter.auth import create_access_token, decode_access_token, hash_password, verify_password
from leadhunter.database import get_db
from leadhunter.models.schema import Membership, Organization, User

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no suministrado o inválido",
        )

    try:
        payload = decode_access_token(authorization.removeprefix("Bearer ").strip())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido",
        ) from exc

    user = db.query(User).filter(
        User.id == payload.get("user_id"),
        User.is_active.is_(True),
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )
    return user


def _token_for_user(user: User, remember_me: bool) -> str:
    expires_delta = timedelta(days=30) if remember_me else None
    return create_access_token(
        {"user_id": user.id, "email": user.email},
        expires_delta=expires_delta,
    )


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya se encuentra registrado",
        )

    user = User(
        email=email,
        password_hash=hash_password(request.password),
        full_name=request.full_name.strip(),
    )
    db.add(user)
    db.flush()
    organization = Organization(
        name=request.organization_name.strip(),
        slug=f"{request.organization_name.strip().lower().replace(' ', '-')}-{user.id[:8]}",
    )
    db.add(organization)
    db.flush()
    db.add(Membership(user_id=user.id, organization_id=organization.id, role="owner"))
    db.commit()
    db.refresh(user)
    db.refresh(organization)

    return {
        "access_token": _token_for_user(user, request.remember_me),
        "token_type": "bearer",
        "user": _user_payload(user),
        "organizations": [{"id": organization.id, "name": organization.name, "role": "owner"}],
    }


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    return {
        "access_token": _token_for_user(user, request.remember_me),
        "token_type": "bearer",
        "user": _user_payload(user),
        "organizations": [
            {"id": item.organization.id, "name": item.organization.name, "role": item.role}
            for item in memberships
        ],
    }


@router.get("/me")
def current_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    return {
        "user": _user_payload(user),
        "organizations": [
            {"id": item.organization.id, "name": item.organization.name, "role": item.role}
            for item in memberships
        ],
    }
