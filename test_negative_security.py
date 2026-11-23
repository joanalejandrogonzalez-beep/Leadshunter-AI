"""Script de pruebas negativas de seguridad y control de acceso multi-inquilino.
Simula ataques de intrusión y acceso no autorizado (IDOR, Cross-Tenant Tampering,
Header Forging y Data Leakage) entre Usuario A (Víctima) y Usuario B (Atacante).
"""
import uuid
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from starlette.testclient import TestClient
from leadhunter.api import app
from leadhunter.database import SessionLocal, init_db
from leadhunter.models.schema import Lead, Organization, Membership, User

client = TestClient(app)


def run_negative_security_tests():
    init_db()
    db = SessionLocal()

    print("=" * 70)
    print("INICIANDO SUITE DE PRUEBAS NEGATIVAS DE SEGURIDAD (IDOR & MULTI-TENANT)")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # 1. PREPARACIÓN DE ENTORNOS: Usuario A (Víctima) y Usuario B (Atacante)
    # -------------------------------------------------------------------------
    tag_a = uuid.uuid4().hex[:6]
    email_a = f"alice_{tag_a}@empresa-alpha.com"
    r_a = client.post("/api/auth/register", json={
        "email": email_a,
        "password": "PasswordAlice123!",
        "full_name": "Alice Gomez",
        "organization_name": "Empresa Alpha Corp"
    })
    assert r_a.status_code == 201, f"Fallo al registrar Usuario A: {r_a.text}"
    data_a = r_a.json()
    token_a = data_a["access_token"]
    org_a_id = data_a["organization"]["id"]
    user_a_id = data_a["user"]["id"]

    tag_b = uuid.uuid4().hex[:6]
    email_b = f"bob_{tag_b}@empresa-beta.com"
    r_b = client.post("/api/auth/register", json={
        "email": email_b,
        "password": "PasswordBob456!",
        "full_name": "Bob Martinez (Atacante)",
        "organization_name": "Empresa Beta Hackers"
    })
    assert r_b.status_code == 201, f"Fallo al registrar Usuario B: {r_b.text}"
    data_b = r_b.json()
    token_b = data_b["access_token"]
    org_b_id = data_b["organization"]["id"]
    user_b_id = data_b["user"]["id"]

    # Crear Lead confidencial de Usuario A directamente en DB para asegurar datos sensibles
    secret_note = "CONFIDENCIAL: Cliente en cierre final por $120,000 USD."
    lead_a = Lead(
        organization_id=org_a_id,
        dedupe_key="d:constructora-secreta.com",
        name="Constructora Alpha Secreta",
        website="https://constructora-secreta.com",
        phone="+1 809 555 7777",
        email="ceo@constructora-secreta.com",
        score=95,
        status="Propuesta",
        notes=secret_note
    )
    db.add(lead_a)
    db.commit()
    db.refresh(lead_a)
    lead_a_id = lead_a.id
    print(f"[OK] Entorno preparado: Lead sensible creado en Org Alpha (ID: {lead_a_id})")

    # Headers de Usuario B atacante
    headers_b_legit = {"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_b_id}
    headers_b_spoofing_org_a = {"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_a_id}

    # -------------------------------------------------------------------------
    # ATAQUE 1: Suplantación de Header de Organización (Header Forging / IDOR)
    # Bob intenta listar los leads de Alpha enviando el Org ID de Alpha con su propio token.
    # -------------------------------------------------------------------------
    print("\n[Ataque 1] Bob intenta listar los leads de Alpha falsificando el header X-Organization-Id...")
    r_atk1 = client.get("/api/leads", headers=headers_b_spoofing_org_a)
    assert r_atk1.status_code == 403, f"FALLO DE SEGURIDAD: Bob debió ser rechazado con 403, obtuvo {r_atk1.status_code}"
    assert "Acceso denegado" in r_atk1.json()["detail"]
    print(" -> APROBADO: Acceso denegado con HTTP 403 Forbidden. La membresía del usuario es validada contra el inquilino.")

    # -------------------------------------------------------------------------
    # ATAQUE 2: Lectura Directa de Objeto por ID (IDOR GET /api/leads/{id})
    # Bob intenta leer la ficha confidencial del Lead A usando el ID exacto y su propio espacio de trabajo.
    # -------------------------------------------------------------------------
    print("\n[Ataque 2] Bob intenta leer el detalle del lead privado de Alice usando el UUID exacto...")
    r_atk2 = client.get(f"/api/leads/{lead_a_id}", headers=headers_b_legit)
    assert r_atk2.status_code == 404, f"FALLO DE SEGURIDAD: Bob no debe ver el lead de Alice. Obtuvo {r_atk2.status_code}"
    # Verificar que el cuerpo no contenga la nota confidencial
    assert "CONFIDENCIAL" not in r_atk2.text
    print(" -> APROBADO: Acceso bloqueado con HTTP 404 Not Found. Ningún dato confidencial filtrado.")

    # -------------------------------------------------------------------------
    # ATAQUE 3: Modificación no autorizada de datos (IDOR PATCH /api/leads/{id})
    # Bob intenta alterar las notas o el estado comercial del lead de Alice.
    # -------------------------------------------------------------------------
    print("\n[Ataque 3] Bob intenta modificar el estado y las notas del lead de Alice (Sabotaje comercial)...")
    r_atk3 = client.patch(
        f"/api/leads/{lead_a_id}",
        json={"notes": "HACKEADO: Lead cancelado por Bob", "status": "Descartado"},
        headers=headers_b_legit
    )
    assert r_atk3.status_code == 404, f"FALLO DE SEGURIDAD: Bob pudo modificar un lead ajeno. Código: {r_atk3.status_code}"

    # Verificación en base de datos: Los datos de Alice deben estar INTACTOS
    db_lead = db.query(Lead).filter(Lead.id == lead_a_id).first()
    assert db_lead.notes == secret_note, "VULNERABILIDAD CRÍTICA: La nota del lead fue alterada en la base de datos!"
    assert db_lead.status == "Propuesta", "VULNERABILIDAD CRÍTICA: El estado del lead fue alterado!"
    print(" -> APROBADO: Modificación rechazada. Los datos en base de datos permanecieron íntegros e inalterados.")

    # -------------------------------------------------------------------------
    # ATAQUE 4: Eliminación no autorizada de datos (IDOR DELETE /api/leads/{id})
    # Bob intenta borrar el prospecto clave de Alice.
    # -------------------------------------------------------------------------
    print("\n[Ataque 4] Bob intenta eliminar el lead de Alice de la base de datos...")
    r_atk4 = client.delete(f"/api/leads/{lead_a_id}", headers=headers_b_legit)
    assert r_atk4.status_code == 404, f"FALLO DE SEGURIDAD: Bob pudo borrar el lead ajeno. Código: {r_atk4.status_code}"

    # Verificación en base de datos: El registro aún debe existir
    db_lead_check = db.query(Lead).filter(Lead.id == lead_a_id).first()
    assert db_lead_check is not None, "VULNERABILIDAD CRÍTICA: El lead de Alice fue eliminado por Bob!"
    print(" -> APROBADO: Eliminación bloqueada con HTTP 404 Not Found. El lead sigue existiendo intacto.")

    # -------------------------------------------------------------------------
    # ATAQUE 5: Intento de Filtración y Descarga Masiva (IDOR en Exportación)
    # Bob intenta exportar en Excel/CSV los leads de Alpha.
    # -------------------------------------------------------------------------
    print("\n[Ataque 5] Bob intenta exportar en Excel (.xlsx) los prospectos de Alpha...")
    r_atk5_xlsx = client.get("/api/leads/export?format=xlsx", headers=headers_b_spoofing_org_a)
    assert r_atk5_xlsx.status_code == 403, f"FALLO DE SEGURIDAD en exportación Excel: {r_atk5_xlsx.status_code}"

    r_atk5_csv = client.get("/api/leads/export?format=csv", headers=headers_b_spoofing_org_a)
    assert r_atk5_csv.status_code == 403, f"FALLO DE SEGURIDAD en exportación CSV: {r_atk5_csv.status_code}"

    # Bob exporta legítimamente su propia empresa: La exportación de Bob NO debe contener datos de Alice
    r_b_own_export = client.get("/api/leads/export?format=csv", headers=headers_b_legit)
    assert r_b_own_export.status_code == 200
    assert "Constructora Alpha Secreta" not in r_b_own_export.text, "FUGA DE DATOS: El archivo de Bob contiene leads de Alice!"
    print(" -> APROBADO: Exportaciones cruzadas bloqueadas con HTTP 403 y archivo propio completamente aislado.")

    # -------------------------------------------------------------------------
    # ATAQUE 6: Petición sin Token de Autenticación o con Token Falsificado
    # -------------------------------------------------------------------------
    print("\n[Ataque 6] Intento de acceso sin token o con firma manipulada...")
    r_no_auth = client.get(f"/api/leads/{lead_a_id}", headers={"X-Organization-Id": org_a_id})
    assert r_no_auth.status_code == 401, f"FALLO: Petición sin token respondió {r_no_auth.status_code}"

    r_fake_jwt = client.get(f"/api/leads/{lead_a_id}", headers={"Authorization": "Bearer token_falsificado_invalido"})
    assert r_fake_jwt.status_code == 401, f"FALLO: Token inválido respondió {r_fake_jwt.status_code}"
    print(" -> APROBADO: Acceso denegado con HTTP 401 Unauthorized para solicitudes no autenticadas.")

    # -------------------------------------------------------------------------
    # ATAQUE 7: Asesor de ICP / Prospección sin pertenencia a la empresa activa
    # -------------------------------------------------------------------------
    print("\n[Ataque 7] Bob intenta usar el asesor de ICP o chat forzando la organización de Alice...")
    r_atk7 = client.post("/api/icp-advisor", json={"service_text": "Marketing"}, headers=headers_b_spoofing_org_a)
    assert r_atk7.status_code == 403
    print(" -> APROBADO: Operaciones de IA y prospección protegidas por membresía (HTTP 403).")

    print("\n" + "=" * 70)
    print("RESULTADO FINAL: 7 DE 7 PRUEBAS DE SEGURIDAD NEGATIVAS APROBADAS.")
    print("EL CONTROL DE ACCESO MULTI-INQUILINO Y LA PREVENCIÓN DE IDOR FUNCIONAN CORRECTAMENTE.")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_negative_security_tests()
