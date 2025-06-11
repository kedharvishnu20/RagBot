from fastapi import APIRouter, HTTPException, Body
from typing import List
from src.services.session_service import SessionService
from src.models.schemas import SessionResponse, UsageStatsResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])
session_service = SessionService()

@router.get("/", response_model=List[SessionResponse])
def list_sessions():
    """Get list of all chat sessions"""
    try:
        print("🔍 [DEBUG] Starting list_sessions...")
        result = session_service.list_sessions()
        print(f"🔍 [DEBUG] Got {len(result)} sessions")
        return result
    except Exception as e:
        print(f"❌ [DEBUG] Error in list_sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """Get a specific session"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/", response_model=SessionResponse)
def create_session():
    """Create a new chat session"""
    return session_service.create_session()

@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(session_id: str, name: str = Body(...)):
    """Update session name"""
    session = session_service.update_session(session_id, name)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/rename", response_model=SessionResponse)
def rename_session(session_id: str, data: dict = Body(...)):
    """Rename a session"""
    name = data.get("name", "Unnamed")
    
    try:
        session = session_service.update_session(session_id, name)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename session: {str(e)}")

@router.delete("/{session_id}")
def delete_session(session_id: str):
    """Delete a session"""
    success = session_service.delete_session(session_id)
    return {"ok": success}

@router.get("/{session_id}/sources")
def get_session_sources(session_id: str):
    """Get sources for a specific session"""
    sources = session_service.get_session_sources(session_id)
    return [source.dict() for source in sources]

@router.get("/{session_id}/message_sources/{message_index}")
def get_message_sources(session_id: str, message_index: int):
    """Get sources for a specific message in a session"""
    try:
        sources = session_service.get_message_sources_by_index(session_id, message_index)
        
        if not sources:
            history = session_service.get_session_history(session_id)
            if (len(history) > message_index and 
                history[message_index].role == "assistant" and 
                history[message_index].ai_type in ["RAG", "MetaRAG"]):
                sources = session_service.get_session_sources(session_id)[:3]
        
        result = []
        for source in sources:
            if hasattr(source, 'dict'):
                source_dict = source.dict()
            elif isinstance(source, dict):
                source_dict = source
            else:
                source_dict = {
                    "name": getattr(source, 'name', 'Unknown'),
                    "content": getattr(source, 'content', ''),
                    "document_type": getattr(source, 'document_type', 'document')
                }
            
            if 'content' not in source_dict and 'preview' in source_dict:
                source_dict['content'] = source_dict['preview']
            elif 'preview' not in source_dict and 'content' in source_dict:
                source_dict['preview'] = source_dict['content'][:300]
            
            result.append(source_dict)
        
        return result
    except Exception as e:
        print(f"Error getting message sources: {e}")
        return []

@router.get("/{session_id}/history")
def get_session_history(session_id: str):
    """Get chat history for a session"""
    history = session_service.get_session_history(session_id)
    return [msg.dict() for msg in history]
