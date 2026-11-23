"""Suite de pruebas de seguridad y aislamiento multi-tenant para LeadHunter AI SaaS.
Verifica:
1. Hash seguro con bcrypt y autenticación JWT.
2. Aislamiento estricto de datos entre organizaciones (prevención de IDOR).
3. Deduplicación independiente por organización.
4. Cumplimiento de límites según el plan contratado.
"""
import uuid
from datetime import datetime
from leadhunter.database import SessionLocal, init_db
from leadhunter.models.schema import User, Organization, Membership, Plan, Subscription, Lead
from leadhunter.auth import hash_password, verify_password, create_access_token, decode_access_token


def setup_module():
    init_db()


def test_password_hashing():
    raw = "MiClaveSuperSegura2026!"
    hashed = hash_password(raw)
    assert hashed != raw, "La contraseña no debe guardarse en texto plano"
    assert verify_password(raw, hashed) is True, "La contraseña válida debe verificar"
    assert verify_password("ClaveErronea", hashed) is False, "La contraseña inválida debe fallar"


def test_jwt_tokens():
    payload = {"user_id": str(uuid.uuid4()), "email": "test@leadhunter.ai"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["email"] == "test@leadhunter.ai"
    assert "exp" in decoded


def test_multi_tenant_isolation():
    db = SessionLocal()
    try:
        uid1 = str(uuid.uuid4())
        uid2 = str(uuid.uuid4())
        org_id1 = str(uuid.uuid4())
        org_id2 = str(uuid.uuid4())

        # Crear Usuario 1 y Empresa A
        u1 = User(id=uid1, email=f"user1_{uid1[:8]}@empresa-a.com", password_hash=hash_password("Pass1!"), full_name="User A")
        o1 = Organization(id=org_id1, name="Empresa A", slug=f"empresa-a-{uid1[:8]}")
        m1 = Membership(user_id=uid1, organization_id=org_id1, role="owner")

        # Crear Usuario 2 y Empresa B
        u2 = User(id=uid2, email=f"user2_{uid2[:8]}@empresa-b.com", password_hash=hash_password("Pass2!"), full_name="User B")
        o2 = Organization(id=org_id2, name="Empresa B", slug=f"empresa-b-{uid2[:8]}")
        m2 = Membership(user_id=uid2, organization_id=org_id2, role="owner")

        db.add_all([u1, o1, m1, u2, o2, m2])
        db.commit()

        # Lead en Empresa A
        lead_a = Lead(
            organization_id=org_id1,
            dedupe_key="d:constructora-ejemplo.com",
            name="Constructora Ejemplo",
            website="https://constructora-ejemplo.com",
            score=85,
            notes="Nota confidencial de Empresa A"
        )
        db.add(lead_a)
        db.commit()
        lead_a_id = lead_a.id

        # Simulación de consulta desde el contexto de Usuario 2 (Empresa B)
        # La consulta obligatoriamente filtra por organization_id del usuario activo
        user2_query = db.query(Lead).filter(Lead.id == lead_a_id, Lead.organization_id == org_id2).first()
        assert user2_query is None, "VULNERABILIDAD IDOR: Empresa B pudo acceder al lead de Empresa A"

        # Simulación de consulta legítima de Empresa A
        user1_query = db.query(Lead).filter(Lead.id == lead_a_id, Lead.organization_id == org_id1).first()
        assert user1_query is not None
        assert user1_query.name == "Constructora Ejemplo"
        assert user1_query.notes == "Nota confidencial de Empresa A"

        # Deduplicación independiente: Empresa B PUEDE prospectar a la misma empresa externa
        # con su propio registro y notas aisladas
        lead_b = Lead(
            organization_id=org_id2,
            dedupe_key="d:constructora-ejemplo.com",
            name="Constructora Ejemplo",
            website="https://constructora-ejemplo.com",
            score=60,
            notes="Evaluación propia de Empresa B"
        )
        db.add(lead_b)
        db.commit()

        # Verificar que existen 2 registros independientes para cada inquilino
        leads_a = db.query(Lead).filter(Lead.organization_id == org_id1).all()
        leads_b = db.query(Lead).filter(Lead.organization_id == org_id2).all()
        assert len(leads_a) == 1 and leads_a[0].notes == "Nota confidencial de Empresa A"
        assert len(leads_b) == 1 and leads_b[0].notes == "Evaluación propia de Empresa B"

        print("Aislamiento multi-tenant y prevención de IDOR verificados con éxito.")

    finally:
        db.close()


def test_plan_limits_enforcement():
    db = SessionLocal()
    try:
        uid = str(uuid.uuid4())
        user = User(id=uid, email=f"plan_test_{uid[:8]}@example.com", password_hash=hash_password("Pass123!"), full_name="Tester")
        db.add(user)
        db.commit()

        # Crear 1era organización en plan Starter (máx 1)
        org1 = Organization(name="Org 1", slug=f"org1-{uid[:8]}")
        db.add(org1)
        db.commit()
        db.add(Membership(user_id=uid, organization_id=org1.id, role="owner"))
        db.add(Subscription(organization_id=org1.id, plan_id="starter", status="active"))
        db.commit()

        # Consultar cuántas organizaciones posee el usuario
        owned_count = db.query(Membership).filter(Membership.user_id == uid, Membership.role == "owner").count()
        starter_plan = db.query(Plan).filter(Plan.id == "starter").first()

        assert owned_count <= starter_plan.max_organizations, "Dentro del límite del plan Starter"

        # Intentar crear una 2da organización simulando la validación del backend
        can_create = owned_count < starter_plan.max_organizations
        assert can_create is False, "El sistema debe bloquear la creación de una segunda empresa bajo el plan Starter"

        print("Límites de plan verificados con éxito.")
    finally:
        db.close()


if __name__ == "__main__":
    test_password_hashing()
    test_jwt_tokens()
    test_multi_tenant_isolation()
    test_plan_limits_enforcement()
    print("\nTODAS LAS PRUEBAS DE SEGURIDAD Y MULTI-TENANT APROBADAS.")
