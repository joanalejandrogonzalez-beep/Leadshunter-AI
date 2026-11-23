from fastapi import APIRouter

from backend.app.schemas import ChatRequest, ChatResponse
from leadhunter import ai_agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    intent = ai_agent.detect_intent(request.message)
    if intent == "general":
        return ChatResponse(
            reply=ai_agent.reply_general(request.message),
            business=request.business,
        )
    if intent == "advice":
        advice = ai_agent.advise_icp(request.message)
        reply = (
            f"Nicho recomendado: {advice['recommended_sector']} en "
            f"{advice['target_city']}, {advice['target_country']}.\n\n"
            f"{advice['reasoning']}\n\n{advice['suggested_pitch']}"
        )
        return ChatResponse(reply=reply, business=request.business)

    result = ai_agent.run_conversational_search(
        business=request.business,
        prompt=request.message,
        max_results=10,
    )
    leads = result["leads"]
    reply = (
        f"Encontré {len(leads)} prospectos calificados de {result['sector']} "
        f"en {result['city']}, {result['country']}."
        if leads
        else f"No encontré prospectos que superaran los filtros para {result['sector']} en {result['city']}."
    )

    return ChatResponse(
        reply=reply,
        business=request.business,
        status="ok" if leads else "no_results",
        leads=leads,
        errors=result["errors"],
    )
