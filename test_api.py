"""Pruebas funcionales y de seguridad de la API REST FastAPI.
Verifica autenticación, roles, prevención de IDOR y límites de planes mediante HTTP.
"""
import uuid
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from starlette.testclient import TestClient

from leadhunter.api import app
from leadhunter.database import init_db

client = TestClient(app)


def test_api_full_flow():
    init_db()

    # 1. Registro de Usuario 1
    uid1 = uuid.uuid4().hex[:8]
    email1 = f"carlos_{uid1}@ejemplo.com"
    r_reg1 = client.post("/api/auth/register", json={
        "email": email1,
        "password": "Password123!",
        "full_name": "Carlos Gomez",
        "organization_name": "Constructora Gomez"
    })
    assert r_reg1.status_code == 201, r_reg1.text
    data1 = r_reg1.json()
    token1 = data1["access_token"]
    org1_id = data1["organization"]["id"]
    assert data1["user"]["email"] == email1
    assert org1_id is not None
    print("OK 1: Registro de usuario y empresa inicial aprobado")

    # 2. Login
    r_login = client.post("/api/auth/login", json={
        "email": email1,
        "password": "Password123!"
    })
    assert r_login.status_code == 200
    assert len(r_login.json()["organizations"]) == 1

    r_login_bad = client.post("/api/auth/login", json={
        "email": email1,
        "password": "PasswordEquivocada"
    })
    assert r_login_bad.status_code == 401
    print("OK 2: Login con credenciales válidas e inválidas verificado")

    # 3. Registro de Usuario 2 (Inquilino diferente)
    uid2 = uuid.uuid4().hex[:8]
    email2 = f"maria_{uid2}@ejemplo.com"
    r_reg2 = client.post("/api/auth/register", json={
        "email": email2,
        "password": "Password456!",
        "full_name": "Maria Perez",
        "organization_name": "Agencia Digital Perez"
    })
    assert r_reg2.status_code == 201
    token2 = r_reg2.json()["access_token"]
    org2_id = r_reg2.json()["organization"]["id"]

    # 4. Prueba de Ataque IDOR (Usuario 2 intenta consultar datos de Empresa 1)
    headers_attack = {
        "Authorization": f"Bearer {token2}",
        "X-Organization-Id": org1_id
    }
    r_attack = client.get("/api/leads", headers=headers_attack)
    assert r_attack.status_code == 403, "VULNERABILIDAD IDOR: Usuario 2 pudo acceder con el header de Empresa 1"
    assert "Acceso denegado" in r_attack.json()["detail"]
    print("OK 3: Protección contra ataque IDOR verificada por API (HTTP 403 Forbidden)")

    # 5. Consulta legítima de Usuario 1
    headers_legit = {
        "Authorization": f"Bearer {token1}",
        "X-Organization-Id": org1_id
    }
    r_leads = client.get("/api/leads", headers=headers_legit)
    assert r_leads.status_code == 200
    print("OK 4: Consulta legítima autorizada exitosamente")

    # 6. Prueba de Límite de Plan (Plan Starter permite máximo 1 empresa)
    r_create_org = client.post("/api/organizations", json={
        "name": "Segunda Empresa No Autorizada"
    }, headers={"Authorization": f"Bearer {token1}"})
    assert r_create_org.status_code == 402, "El backend debe rechazar crear una 2da empresa si el plan es Starter"
    assert "límite máximo de empresas" in r_create_org.json()["detail"]
    print("OK 5: Control estricto de límites por plan verificado por API (HTTP 402 Payment Required)")

    # 7. Prueba de Prospección Conversacional y Persistencia Multi-Tenant (/api/chat -> /api/leads)
    from unittest.mock import patch
    test_lead_name = f"Constructora Test API {uuid.uuid4().hex[:6]}"
    mock_leads = [{
        "name": test_lead_name,
        "website": f"https://{test_lead_name.lower().replace(' ', '-')}.example",
        "phone": "+1 809 555 9999",
        "email": "contacto@constructora-test.example",
        "instagram": "https://instagram.com/constructora_test",
        "city": "Santo Domingo",
        "country": "República Dominicana",
        "sector": "Constructoras",
        "source": "OpenStreetMap"
    }]
    mock_analysis = {
        "ok": True,
        "error": "",
        "facts": {
            "emails": ["contacto@constructora-test.example"],
            "phones": ["18095559999"],
            "linkedin": [],
            "instagram": "https://instagram.com/constructora_test",
            "https": False,
            "cms": "",
            "pages_read": 2,
            "last_copyright_year": 2025,
        },
        "signals": {
            "has_viewport": False,
            "has_form": False,
            "has_whatsapp": False,
            "has_video": False,
            "has_portal": False,
            "has_quote_cta": False,
            "has_social_instagram": True,
            "listing_mentions": 10,
            "catalog_mentions": 0,
            "branch_mentions": 0,
            "luxury_mentions": 0,
            "project_mentions": 10,
            "text_len": 300,
        },
    }
    with patch("leadhunter.prospecting.search_b2b_prospects", return_value=([], [])), \
         patch("leadhunter.sources.search_osm", return_value=mock_leads), \
         patch("leadhunter.analyzer.analyze_site", return_value=mock_analysis):
        r_chat = client.post("/api/chat", json={
            "prompt": "Encuentra constructoras en Santo Domingo"
        }, headers=headers_legit)
        assert r_chat.status_code == 200, r_chat.text
        chat_data = r_chat.json()
        assert chat_data["new_leads"] >= 1 or chat_data["existing_leads"] >= 1

        # Verificar que el lead ahora APARECE en /api/leads
        r_check_leads = client.get("/api/leads", headers=headers_legit)
        assert r_check_leads.status_code == 200
        leads_list = r_check_leads.json()
        names = [l["name"] for l in leads_list]
        assert test_lead_name in names, "El lead obtenido vía /api/chat debe persistirse y consultarse en /api/leads"
        print("OK 6: Prospección conversacional /api/chat integrada y persistida en /api/leads exitosamente")

    # 8. Prueba del Asesor Estratégico de Cliente Ideal (ICP Advisor)
    r_icp = client.post("/api/icp-advisor", json={
        "service_text": "Desarrollo páginas web y software a medida en Santo Domingo",
        "location": "Santo Domingo"
    }, headers=headers_legit)
    assert r_icp.status_code == 200, r_icp.text
    icp_data = r_icp.json()
    assert "recommended_sector" in icp_data
    assert "reasoning" in icp_data
    assert len(icp_data.get("pain_points", [])) > 0
    assert "suggested_pitch" in icp_data
    print("OK 7: Asesor estratégico de Nicho e ICP (/api/icp-advisor) verificado exitosamente")

    # 9. Prueba de Descarga y Exportación en Excel (.xlsx) y CSV
    r_exp_xlsx = client.get("/api/leads/export?format=xlsx", headers=headers_legit)
    assert r_exp_xlsx.status_code == 200
    assert "openxmlformats" in r_exp_xlsx.headers.get("content-type", "")
    assert len(r_exp_xlsx.content) > 1000, "El binario Excel generado debe ser válido y contener datos"

    r_exp_csv = client.get("/api/leads/export?format=csv", headers=headers_legit)
    assert r_exp_csv.status_code == 200
    assert "text/csv" in r_exp_csv.headers.get("content-type", "")
    assert len(r_exp_csv.content) > 50
    print("OK 8: Exportación de leads en Excel (.xlsx) y CSV con codificación verificado")

    # 10. Consulta de empresas vinculadas al usuario
    r_orgs = client.get("/api/organizations", headers={"Authorization": f"Bearer {token1}"})
    assert r_orgs.status_code == 200
    org_list = r_orgs.json()
    assert any(o["id"] == org1_id for o in org_list)
    print("OK 9: Listado de empresas de usuario (/api/organizations) verificado")


if __name__ == "__main__":
    test_api_full_flow()
    print("\nTODAS LAS PRUEBAS DE LA API REST FASTAPI APROBADAS.")
