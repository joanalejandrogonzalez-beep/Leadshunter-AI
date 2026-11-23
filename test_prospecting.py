"""Pruebas offline del motor de descubrimiento y calificación B2B."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app as next_api_app
from leadhunter import ai_agent, analyzer, db, prospecting


def _analysis_fixture():
    return {
        "ok": True,
        "error": "",
        "facts": {
            "emails": ["contacto@constructora-demo.example"],
            "phones": ["18095550123"],
            "linkedin": ["https://www.linkedin.com/company/constructora-demo"],
            "instagram": "https://instagram.com/constructora_demo",
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
            "listing_mentions": 0,
            "catalog_mentions": 0,
            "branch_mentions": 2,
            "luxury_mentions": 0,
            "project_mentions": 8,
            "text_len": 320,
        },
    }


def test_intent_and_request_extraction():
    prompt = "Dame 10 leads calificados de constructoras que requieran mis servicios como desarrollador de software"
    interpreted = ai_agent.interpret_prompt(prompt)
    assert ai_agent.detect_intent(prompt) == "search"
    assert interpreted["max_results"] == 10
    assert "software" in interpreted["service"].lower()
    assert ai_agent.detect_intent("Hola, ¿qué puedes hacer?") == "general"


def test_search_query_and_provider_fallback():
    with patch.dict(os.environ, {"SERPER_API_KEY": "", "TAVILY_API_KEY": ""}):
        with patch.object(
            prospecting,
            "_duckduckgo_search",
            return_value=[{"title": "Constructora Demo", "url": "https://constructora-demo.example"}],
        ) as search_mock:
            results, errors = prospecting.search_b2b_prospects(
                "Desarrollo Web y Software", "Constructoras", "Madrid", "España", limit=1
            )

    assert not errors
    assert results[0]["name"] == "Constructora Demo"
    query = search_mock.call_args.args[0]
    assert "Constructoras" in query and "Madrid" in query and "software" in query.lower()
    assert "-directorio" in query


def test_analyzer_extracts_public_linkedin():
    html = """
    <html><head><meta name="viewport" content="width=device-width"></head>
    <body><a href="https://www.linkedin.com/company/constructora-demo">LinkedIn</a>
    <a href="mailto:contacto@demo.example">Email</a></body></html>
    """
    result = analyzer.analyze_html({"https://demo.example": html}, "https://demo.example", True)
    assert result["facts"]["linkedin"] == ["https://www.linkedin.com/company/constructora-demo"]
    assert result["facts"]["emails"] == ["contacto@demo.example"]


def test_qualified_pipeline_and_persistence():
    original_db_path = db.DB_PATH
    candidate = {
        "name": "Constructora Demo",
        "website": "https://constructora-demo.example",
        "city": "Santo Domingo",
        "country": "República Dominicana",
        "sector": "Constructoras",
        "source": "Serper",
    }
    try:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            db.DB_PATH = Path(temp_dir) / "prospecting-test.db"
            with patch.object(prospecting, "search_b2b_prospects", return_value=([candidate], [])), \
                 patch.object(prospecting, "analyze_company_website", return_value=_analysis_fixture()):
                result = prospecting.run_prospecting(
                    business="Novus Ops",
                    interpretation={
                        "service": "Desarrollo Web y Software",
                        "max_results": 1,
                        "sector": "Constructoras",
                        "city": "Santo Domingo",
                        "country": "República Dominicana",
                    },
                    service_profile="Desarrollo Web y Software",
                    sender="Ana",
                )

            assert len(result["leads"]) == 1
            lead = result["leads"][0]
            assert lead["score"] >= prospecting.MIN_QUALIFIED_SCORE
            assert lead["email"] and lead["linkedin"] and lead["website"]
            assert "formulario" in lead["diagnosis"].lower()
            assert "Ana" in lead["outreach"]
            stored = db.leads_df("Novus Ops").iloc[0]
            assert stored["score"] == lead["score"]
            assert stored["notes"] == lead["diagnosis"]
    finally:
        db.DB_PATH = original_db_path


def test_next_api_returns_structured_leads():
    expected_lead = {
        "name": "Constructora Demo",
        "website": "https://constructora-demo.example",
        "email": "contacto@constructora-demo.example",
        "phone": "18095550123",
        "linkedin": "https://www.linkedin.com/company/constructora-demo",
        "instagram": "https://instagram.com/constructora_demo",
        "score": 78,
        "diagnosis": "No se detectó una vía directa para cotizar.",
        "outreach": "Hola equipo, vi una oportunidad concreta.",
    }
    with patch(
        "backend.app.routers.chat.ai_agent.run_conversational_search",
        return_value={
            "sector": "Constructoras",
            "city": "Santo Domingo",
            "country": "República Dominicana",
            "leads": [expected_lead],
            "errors": [],
        },
    ):
        response = TestClient(next_api_app).post(
            "/api/chat",
            json={"business": "LeadHunter", "message": "Dame 1 lead de constructoras"},
        )

    assert response.status_code == 200, response.text
    assert response.json()["leads"] == [expected_lead]
    assert response.json()["status"] == "ok"


if __name__ == "__main__":
    test_intent_and_request_extraction()
    test_search_query_and_provider_fallback()
    test_analyzer_extracts_public_linkedin()
    test_qualified_pipeline_and_persistence()
    test_next_api_returns_structured_leads()
    print("TODAS LAS PRUEBAS DE PROSPECCIÓN OK")