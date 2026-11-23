"""Migración idempotente de la base de datos SQLite legacy (data/leadhunter.db)
al nuevo esquema relacional multi-tenant (data/leadhunter_v2.db / PostgreSQL).
No altera ni elimina los datos originales.
"""
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

from .database import SessionLocal, init_db
from .models.schema import User, Organization, Membership, Plan, Subscription, Lead, SavedSearch
from .auth import hash_password

LEGACY_DB = Path(__file__).resolve().parent.parent / "data" / "leadhunter.db"


def seed_default_plans(db):
    plans_data = [
        {"id": "starter", "name": "Plan Inicial", "max_organizations": 1, "monthly_searches": 50, "monthly_leads": 500, "price_usd": 29.00},
        {"id": "growth", "name": "Plan Crecimiento", "max_organizations": 3, "monthly_searches": 200, "monthly_leads": 2000, "price_usd": 79.00},
        {"id": "enterprise", "name": "Plan Avanzado", "max_organizations": 10, "monthly_searches": 1000, "monthly_leads": 10000, "price_usd": 199.00},
    ]
    for p in plans_data:
        existing = db.query(Plan).filter(Plan.id == p["id"]).first()
        if not existing:
            db.add(Plan(**p))
    db.commit()


def run_migration():
    if not LEGACY_DB.exists():
        print(f"Base de datos legacy {LEGACY_DB} no encontrada.")
        return 0, 0

    init_db()
    db = SessionLocal()

    try:
        seed_default_plans(db)

        # 1. Crear usuario y organizaciones por defecto para los negocios existentes
        admin_email = os.getenv("ADMIN_EMAIL", "admin@leadhunter.ai")
        admin_password = os.getenv("ADMIN_PASSWORD", "AdminLeadHunter2026!")
        user = db.query(User).filter(User.email == admin_email).first()
        if not user:
            user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                full_name="Administrador LeadHunter",
                is_superuser=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Conectar a SQLite legacy
        con = sqlite3.connect(LEGACY_DB)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Obtener nombres de negocios en la BD legacy
        biz_rows = cur.execute("SELECT DISTINCT business FROM leads").fetchall()
        biz_names = [r["business"] for r in biz_rows] or ["Novus Ops", "NTO Productions"]

        org_map = {}
        for b_name in biz_names:
            slug = b_name.lower().replace(" ", "-")
            org = db.query(Organization).filter(Organization.slug == slug).first()
            if not org:
                org = Organization(
                    name=b_name,
                    slug=slug,
                    commercial_profile=f"Perfil comercial para {b_name}",
                    country="República Dominicana",
                    city="Santo Domingo"
                )
                db.add(org)
                db.commit()
                db.refresh(org)

                # Vincular membresía
                mem = Membership(user_id=user.id, organization_id=org.id, role="owner")
                db.add(mem)

                # Asignar suscripción Starter por defecto
                sub = Subscription(organization_id=org.id, plan_id="starter", status="active")
                db.add(sub)
                db.commit()

            org_map[b_name] = org.id

        # 2. Migrar Leads
        legacy_leads = cur.execute("SELECT * FROM leads").fetchall()
        leads_migrated = 0
        leads_skipped = 0

        for r in legacy_leads:
            biz = r["business"]
            org_id = org_map.get(biz)
            if not org_id:
                continue

            dedupe = r["dedupe_key"]
            existing = db.query(Lead).filter(Lead.organization_id == org_id, Lead.dedupe_key == dedupe).first()
            if existing:
                leads_skipped += 1
                continue

            # Crear lead
            new_lead = Lead(
                organization_id=org_id,
                dedupe_key=dedupe,
                name=r["name"],
                website=r["website"] or "",
                phone=r["phone"] or "",
                email=r["email"] or "",
                instagram=r["instagram"] or "",
                country=r["country"] or "",
                city=r["city"] or "",
                sector=r["sector"] or "",
                source=r["source"] or "",
                address=r["address"] or "",
                score=r["score"] or 0,
                score_detail=r["score_detail"] or "{}",
                evidence=r["evidence"] or "[]",
                inferences=r["inferences"] or "[]",
                status=r["status"] or "Nuevo",
                notes=r["notes"] or "",
                next_followup=r["next_followup"] or "",
                analyzed=r["analyzed"] or 0,
            )
            db.add(new_lead)
            leads_migrated += 1

        # 3. Migrar Búsquedas Guardadas
        try:
            legacy_searches = cur.execute("SELECT * FROM saved_searches").fetchall()
            for s in legacy_searches:
                org_id = org_map.get(s["business"])
                if not org_id:
                    continue
                exists = db.query(SavedSearch).filter(
                    SavedSearch.organization_id == org_id,
                    SavedSearch.sector == s["sector"],
                    SavedSearch.city == s["city"]
                ).first()
                if not exists:
                    ss = SavedSearch(
                        organization_id=org_id,
                        country=s["country"] or "",
                        city=s["city"] or "",
                        sector=s["sector"] or "",
                        sources=s["sources"] or "OpenStreetMap,DuckDuckGo",
                        max_results=s["max_results"] or 30,
                        last_run=s["last_run"]
                    )
                    db.add(ss)
        except Exception as e:
            print("Aviso al migrar búsquedas:", e)

        db.commit()
        con.close()

        print(f"Migración completada con éxito:")
        print(f" - {leads_migrated} leads migrados.")
        print(f" - {leads_skipped} leads omitidos por ya existir.")
        return leads_migrated, leads_skipped

    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
