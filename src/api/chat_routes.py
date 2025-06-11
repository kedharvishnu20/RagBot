from fastapi import APIRouter, HTTPException
from src.services.chat_orchestrator import ChatOrchestrator
from src.models.schemas import ChatRequest, ChatResponse, UsageStatsResponse
from src.services.session_service import SessionService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_orchestrator = ChatOrchestrator()
session_service = SessionService()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for AI interactions"""
    try:
        response = await chat_orchestrator.process_chat_request(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/ai_modes")
def get_ai_modes():
    """Get available AI modes"""
    return session_service.get_available_ai_modes()

@router.get("/usage", response_model=UsageStatsResponse)
def get_usage_stats():
    """Get AI mode usage statistics"""
    return session_service.get_usage_stats()
