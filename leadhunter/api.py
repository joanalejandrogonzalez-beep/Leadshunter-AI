"""FastAPI REST API para LeadHunter AI SaaS.
Provee endpoints de autenticación, gestión multi-tenant, prospección IA y facturación.
"""
import os
import io
from datetime import date
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import pandas as pd

from .database import get_db, init_db
from .models.schema import User, Organization, Membership, Plan, Subscription, Lead
from .auth import hash_password, verify_password, create_access_token, decode_access_token
from . import ai_agent, pipeline

app = FastAPI(
    title="LeadHunter AI API",
    description="API RESTful comercial para prospección B2B global y gestión multi-empresa",
    version="2.0.0"
)

origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://localhost:3000,http://127.0.0.1:8501")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
allow_all = "*" in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if not allow_all else ["*"],
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# --- Esquemas Pydantic
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CreateOrgRequest(BaseModel):
    name: str
    commercial_profile: Optional[str] = ""
    country: Optional[str] = ""
    city: Optional[str] = ""


class ChatPromptRequest(BaseModel):
    prompt: str
    max_results: Optional[int] = 15


class ICPAdvisorRequest(BaseModel):
    service_text: str
    location: Optional[str] = ""


class UpdateLeadRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    next_followup: Optional[str] = None


# --- Dependencias de Seguridad
def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no suministrado o inválido")
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado o inválido")


def get_current_membership(
    organization_id: str = Header(..., alias="X-Organization-Id"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Membership:
    mem = db.query(Membership).filter(
        Membership.user_id == user.id,
        Membership.organization_id == organization_id
    ).first()
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: no formas parte de esta organización"
        )
    return mem


# --- Endpoints de Autenticación
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya se encuentra registrado")

    user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        full_name=req.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear su primera empresa
    slug = req.organization_name.lower().replace(" ", "-") + f"-{user.id[:6]}"
    org = Organization(name=req.organization_name, slug=slug)
    db.add(org)
    db.commit()
    db.refresh(org)

    # Crear membresía owner
    mem = Membership(user_id=user.id, organization_id=org.id, role="owner")
    db.add(mem)

    # Asignar suscripción Starter por defecto
    sub = Subscription(organization_id=org.id, plan_id="starter", status="active")
    db.add(sub)
    db.commit()

    token = create_access_token({"user_id": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
        "organization": {"id": org.id, "name": org.name}
    }


@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    orgs = [{"id": m.organization.id, "name": m.organization.name, "role": m.role} for m in memberships]

    token = create_access_token({"user_id": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
        "organizations": orgs
    }


# --- Endpoints de Organizaciones
@app.get("/api/organizations")
def list_organizations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mems = db.query(Membership).filter(Membership.user_id == user.id).all()
    return [{"id": m.organization.id, "name": m.organization.name, "role": m.role} for m in mems]


@app.post("/api/organizations", status_code=status.HTTP_201_CREATED)
def create_organization(
    req: CreateOrgRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validar límite de empresas del plan del usuario
    owned_count = db.query(Membership).filter(Membership.user_id == user.id, Membership.role == "owner").count()
    # Tomar el plan más alto de sus organizaciones actuales
    starter_plan = db.query(Plan).filter(Plan.id == "starter").first()
    max_allowed = starter_plan.max_organizations if starter_plan else 1

    if owned_count >= max_allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Has alcanzado el límite máximo de empresas para tu plan ({max_allowed}). Actualiza a un plan superior para gestionar más empresas."
        )

    slug = req.name.lower().replace(" ", "-") + f"-{user.id[:6]}"
    org = Organization(
        name=req.name,
        slug=slug,
        commercial_profile=req.commercial_profile or "",
        country=req.country or "",
        city=req.city or ""
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    mem = Membership(user_id=user.id, organization_id=org.id, role="owner")
    db.add(mem)
    db.commit()

    return {"id": org.id, "name": org.name, "slug": org.slug}


# --- Endpoints de Leads y Prospección
@app.get("/api/leads")
def list_leads(
    status_filter: Optional[str] = None,
    min_score: int = 0,
    search: Optional[str] = None,
    mem: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    q = db.query(Lead).filter(
        Lead.organization_id == mem.organization_id,
        Lead.score >= min_score
    )
    if status_filter:
        q = q.filter(Lead.status == status_filter)
    if search:
        s_term = f"%{search}%"
        q = q.filter((Lead.name.ilike(s_term)) | (Lead.city.ilike(s_term)) | (Lead.sector.ilike(s_term)))

    leads = q.order_by(Lead.score.desc(), Lead.created_at.desc()).limit(100).all()
    return [
        {
            "id": l.id,
            "name": l.name,
            "website": l.website,
            "phone": l.phone,
            "email": l.email,
            "instagram": l.instagram,
            "city": l.city,
            "country": l.country,
            "sector": l.sector,
            "score": l.score,
            "status": l.status,
            "source": l.source,
            "next_followup": l.next_followup
        }
        for l in leads
    ]


@app.get("/api/leads/export")
def export_leads_endpoint(
    format: str = "xlsx",
    status_filter: Optional[str] = None,
    min_score: int = 0,
    search: Optional[str] = None,
    mem: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Descarga de leads en formato nativo Excel (.xlsx) o CSV (con codificación UTF-8 BOM)."""
    q = db.query(Lead).filter(
        Lead.organization_id == mem.organization_id,
        Lead.score >= min_score
    )
    if status_filter:
        q = q.filter(Lead.status == status_filter)
    if search:
        s_term = f"%{search}%"
        q = q.filter((Lead.name.ilike(s_term)) | (Lead.city.ilike(s_term)) | (Lead.sector.ilike(s_term)))

    leads = q.order_by(Lead.score.desc(), Lead.created_at.desc()).all()
    rows = [
        {
            "ID Lead": l.id,
            "Nombre de Empresa": l.name,
            "Score (0-100)": l.score,
            "Estado Comercial": l.status,
            "Sector": l.sector,
            "Ciudad": l.city,
            "País": l.country,
            "Teléfono": l.phone,
            "Email": l.email,
            "Instagram": l.instagram,
            "Sitio Web": l.website,
            "Dirección": l.address,
            "Notas Comerciales": l.notes,
            "Próximo Seguimiento": l.next_followup,
            "Fuente": l.source
        }
        for l in leads
    ]
    df = pd.DataFrame(rows)
    org_slug = mem.organization.slug or "empresa"
    today_str = date.today().isoformat()

    if format.lower() == "csv":
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="leads_{org_slug}_{today_str}.csv"'}
        )
    else:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Prospectos B2B")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="leads_{org_slug}_{today_str}.xlsx"'}
        )


@app.get("/api/leads/{lead_id}")
def get_lead_detail(
    lead_id: str,
    mem: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.organization_id == mem.organization_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado")
    return lead


@app.patch("/api/leads/{lead_id}")
def update_lead(
    lead_id: str,
    req: UpdateLeadRequest,
    mem: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.organization_id == mem.organization_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado")
    if req.status is not None:
        lead.status = req.status
    if req.notes is not None:
        lead.notes = req.notes
    if req.next_followup is not None:
        lead.next_followup = req.next_followup
    db.commit()
    return {"ok": True, "lead_id": lead.id}


@app.delete("/api/leads/{lead_id}")
def delete_lead(
    lead_id: str,
    mem: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.organization_id == mem.organization_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado")
    db.delete(lead)
    db.commit()
    return {"ok": True, "deleted": lead_id}


# --- Endpoint de Chat Conversacional de Prospección
@app.post("/api/chat")
def chat_prospecting(
    req: ChatPromptRequest,
    mem: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    org = mem.organization
    res = ai_agent.run_conversational_search(
        business=org.name,
        prompt=req.prompt,
        service_profile=org.commercial_profile or org.name,
        max_results=req.max_results or 15,
        organization_id=org.id,
        session=db
    )
    return res


@app.post("/api/icp-advisor")
def advise_icp_endpoint(
    req: ICPAdvisorRequest,
    mem: Membership = Depends(get_current_membership)
):
    return ai_agent.advise_icp(req.service_text, req.location or "")
