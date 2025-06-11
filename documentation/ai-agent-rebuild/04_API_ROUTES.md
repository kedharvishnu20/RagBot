# AI Agent Rebuild Guide - Part 4: API Routes Implementation

This document provides exact implementations for all API route files in the RAG AI Application.

## Directory Structure

```
src/api/
├── __init__.py
├── chat_routes.py
├── session_routes.py
├── file_routes.py
└── system_routes.py
```

## 1. API Package Initialization

**File: `src/api/__init__.py`**

```python
# This file makes the api directory a Python package
```

## 2. Chat Routes Implementation

**File: `src/api/chat_routes.py`**

```python
# filepath: src/api/chat_routes.py
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
```

## 3. Session Routes Implementation

**File: `src/api/session_routes.py`**

```python
# filepath: src/api/session_routes.py
from fastapi import APIRouter, HTTPException, Body
from typing import List
from src.services.session_service import SessionService
from src.models.schemas import SessionResponse, UsageStatsResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])
session_service = SessionService()

@router.get("/", response_model=List[SessionResponse])
def list_sessions():
    """Get list of all chat sessions"""
    return session_service.list_sessions()

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
```

## 4. File Routes Implementation

**File: `src/api/file_routes.py`**

```python
# filepath: src/api/file_routes.py
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List
from src.services.file_service import FileService
from src.services.chat_orchestrator import ChatOrchestrator
from src.models.schemas import UploadResponse

router = APIRouter(prefix="/files", tags=["files"])
file_service = FileService()
chat_orchestrator = ChatOrchestrator()

@router.post("/upload", response_model=List[UploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload documents for RAG processing"""
    try:
        results = await file_service.upload_files(files)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/rebuild_index")
async def rebuild_index(api_key_index: int = Form(0)):
    """Rebuild the vector index from uploaded documents"""
    try:
        result = await chat_orchestrator.rebuild_vector_index(api_key_index)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")

@router.post("/clear_vector_db")
async def clear_vector_db():
    """Clear the vector database"""
    try:
        result = chat_orchestrator.clear_vector_database()
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear operation failed: {str(e)}")

@router.get("/vector_status")
def get_vector_status():
    """Get vector store status and statistics"""
    try:
        return chat_orchestrator.get_vector_store_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/uploaded")
def list_uploaded_files():
    """Get list of uploaded files"""
    try:
        files = file_service.get_uploaded_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/clear_uploads")
def clear_uploads():
    """Clear all uploaded files"""
    try:
        success = file_service.clear_uploads()
        if success:
            return {"status": "success", "message": "All uploads cleared"}
        else:
            return {"status": "error", "message": "Failed to clear uploads"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear operation failed: {str(e)}")
```

## 5. System Routes Implementation

**File: `src/api/system_routes.py`**

```python
# filepath: src/api/system_routes.py
# Fixed system_routes.py - Addresses API key exposure and security issues
from fastapi import APIRouter, HTTPException
from src.utils.config import api_keys, GEMINI_MODELS
from src.models.schemas import ApiKeyResponse, HealthResponse
from typing import List
import datetime
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

@router.get("/", response_class=None)
def serve_frontend():
    """Serve the main frontend application"""
    try:
        from fastapi.responses import HTMLResponse

        html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")

        if os.path.exists(html_path):
            with open(html_path, encoding="utf-8") as f:
                content = f.read()
                logger.debug("✅ Frontend served successfully")
                return HTMLResponse(content)
        else:
            logger.warning("❌ Frontend HTML file not found")
            return HTMLResponse(
                "<h1>Frontend not found</h1><p>Please ensure index.html exists in the src directory</p>",
                status_code=404
            )
    except Exception as e:
        logger.error(f"Error serving frontend: {e}")
        return HTMLResponse(
            f"<h1>Error loading frontend</h1><p>Error: {str(e)}</p>",
            status_code=500
        )

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint for monitoring"""
    try:
        return HealthResponse(
            status="healthy",
            message="RAG AI App is running",
            timestamp=datetime.datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/api_keys", response_model=List[ApiKeyResponse])
def get_api_keys():
    """FIXED: Get available API keys WITHOUT exposing actual key values"""
    try:
        valid_keys = [key for key in api_keys.google_api_keys if key and key.strip()]

        safe_response = []
        for i in range(len(valid_keys)):
            safe_response.append(
                ApiKeyResponse(
                    index=i,
                    name=f"API Key {i + 1}"
                )
            )

        logger.debug(f"✅ Returned metadata for {len(safe_response)} API keys")
        return safe_response

    except Exception as e:
        logger.error(f"Error getting API keys metadata: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve API key metadata"
        )

@router.get("/models")
def get_available_models():
    """Get available Gemini models"""
    try:
        models_info = {
            "gemini_models": GEMINI_MODELS,
            "default_model": "gemini-1.5-flash",
            "count": len(GEMINI_MODELS)
        }
        logger.debug(f"✅ Returned {len(GEMINI_MODELS)} available models")
        return models_info
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")

@router.get("/config")
def get_app_config():
    """FIXED: Get application configuration (non-sensitive information only)"""
    try:
        from src.utils.config import config

        safe_config = {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "max_content_length": config.max_content_length,
            "supported_file_types": ["pdf", "docx", "txt"],
            "ai_modes": ["RAG", "Gemini", "Meta", "MetaRAG"],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "default_model": config.default_model
        }

        logger.debug("✅ Returned safe application configuration")
        return safe_config

    except Exception as e:
        logger.error(f"Error getting app config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get application configuration")
```

## Implementation Notes

### Dependencies

Each route file depends on:

- **FastAPI components**: `APIRouter`, `HTTPException`, `File`, `UploadFile`, etc.
- **Service layer**: Business logic services for handling requests
- **Models**: Pydantic schemas for request/response validation
- **Utility modules**: Configuration and helper functions

### Security Considerations

- **API Key Protection**: The system routes hide actual API key values
- **Error Handling**: Comprehensive exception handling with appropriate HTTP status codes
- **Input Validation**: All inputs are validated through Pydantic schemas

### Route Organization

- **Chat Routes**: Handle AI chat interactions and mode management
- **Session Routes**: Manage chat session lifecycle and history
- **File Routes**: Handle document uploads and vector index operations
- **System Routes**: Provide system information and serve the frontend

### API Integration Points

These routes integrate with:

1. Service layer classes for business logic
2. Database models for data persistence
3. Configuration management for system settings
4. Frontend application through the system routes

## Next Steps

After implementing these API routes, proceed to Part 5: Service Layer Implementation.
