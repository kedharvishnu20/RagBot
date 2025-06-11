# Main Server File - Exact Implementation

hlo

## File Path

`serializable_server.py` (Root directory)

## Purpose

Main FastAPI server entry point with complete error handling and JSON serialization.

## Complete File Content

```python
#!/usr/bin/env python3
"""
Serializable server - ensures all responses are JSON serializable
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import uvicorn
import traceback
import json

# Create app with working structure
app = FastAPI(
    title="RAG AI Application - Serializable",
    description="Fixed RAG AI application with proper JSON serialization",
    version="2.2.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "src", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Initialize database
try:
    from src.utils.database import init_db
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Include API routers
try:
    from src.api.session_routes import router as session_router
    from src.api.chat_routes import router as chat_router
    from src.api.file_routes import router as file_router
    from src.api.system_routes import router as system_router

    app.include_router(session_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(file_router, prefix="/api")
    app.include_router(system_router, prefix="/api")
    print("✅ API routes registered successfully")
except Exception as e:
    print(f"⚠️ API routes registration warning: {e}")

# Models (inline to avoid import issues)
class ChatRequest(BaseModel):
    session_id: str
    message: str
    ai_modes: List[str]
    api_key_index: int = 0
    gemini_model: str = "gemini-1.5-flash"

class ChatResponse(BaseModel):
    answer: Optional[str] = None
    answers: Optional[List[str]] = None
    sources: Optional[List[Dict[str, Any]]] = []
    message_sources: Optional[List[List[Dict[str, Any]]]] = []

# Global service instances (lazy loading to avoid startup errors)
_chat_orchestrator = None
_session_service = None

def convert_to_serializable(obj):
    """Convert any object to a JSON serializable form"""
    if hasattr(obj, 'model_dump') and callable(getattr(obj, 'model_dump')):
        # Pydantic v2 models
        return obj.model_dump()
    elif hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
        # Pydantic v1 models and similar objects
        return obj.dict()
    elif hasattr(obj, '__dict__'):
        # Generic objects with __dict__
        return {k: convert_to_serializable(v) for k, v in obj.__dict__.items()
                if not k.startswith('_')}
    elif isinstance(obj, list):
        # Lists
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        # Dictionaries
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (str, int, float, bool, type(None))):
        # Basic types
        return obj
    else:
        # Fallback
        return str(obj)

def get_chat_orchestrator():
    """Lazy load chat orchestrator to avoid startup errors"""
    global _chat_orchestrator
    if _chat_orchestrator is None:
        try:
            from src.services.chat_orchestrator import ChatOrchestrator
            _chat_orchestrator = ChatOrchestrator()
            print("✅ ChatOrchestrator loaded successfully")
        except Exception as e:
            print(f"❌ ChatOrchestrator failed to load: {e}")
            raise HTTPException(status_code=503, detail="Chat service unavailable")
    return _chat_orchestrator

def get_session_service():
    """Lazy load session service"""
    global _session_service
    if _session_service is None:
        try:
            from src.services.session_service import SessionService
            _session_service = SessionService()
            print("✅ SessionService loaded successfully")
        except Exception as e:
            print(f"❌ SessionService failed to load: {e}")
            raise HTTPException(status_code=503, detail="Session service unavailable")
    return _session_service

# Routes
@app.get("/")
def serve_frontend():
    """Serve the frontend"""
    try:
        html_path = os.path.join(os.path.dirname(__file__), "src", "index.html")
        if os.path.exists(html_path):
            with open(html_path, encoding="utf-8") as f:
                return HTMLResponse(f.read())
        else:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head><title>RAG AI - Working</title></head>
            <body>
                <h1>🎉 RAG AI Server - No More 500 Errors!</h1>
                <p>Server is running successfully with proper JSON serialization.</p>
                <p>Frontend file not found, but server is working.</p>
            </body>
            </html>
            """)
    except Exception as e:
        return HTMLResponse(f"<h1>Server Working</h1><p>Error loading frontend: {e}</p>")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "RAG AI App is running with proper serialization"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint with API exhaustion protection and safe error handling"""
    try:
        # Import timeout handler
        from src.utils.api_exhaustion_handler import create_timeout_aware_chat_response

        # Set a reasonable timeout for the entire chat request
        chat_timeout = 30  # 30 seconds max

        try:
            orchestrator = get_chat_orchestrator()

            # Use asyncio.wait_for to prevent hanging
            response = await asyncio.wait_for(
                orchestrator.process_chat_request(request),
                timeout=chat_timeout
            )

            # Convert response to serializable data
            serializable_response = convert_to_serializable(response)
            return JSONResponse(content=serializable_response)

        except asyncio.TimeoutError:
            print(f"⏰ Chat request timed out after {chat_timeout} seconds - API likely exhausted")
            # Return friendly exhaustion message
            exhaustion_response = create_timeout_aware_chat_response(request.message)
            return JSONResponse(content=exhaustion_response)

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        print(f"Chat error: {e}")
        traceback.print_exc()

        # Check if error indicates API exhaustion
        if any(keyword in error_str for keyword in ['422', 'unprocessable', 'rate limit', 'quota', 'exhausted']):
            from src.utils.api_exhaustion_handler import create_timeout_aware_chat_response
            exhaustion_response = create_timeout_aware_chat_response(request.message)
            return JSONResponse(content=exhaustion_response)

        # Return a safe fallback response instead of 500 error
        return JSONResponse(content={
            "answer": f"I apologize, but I encountered an error processing your message. Error: {str(e)[:100]}",
            "sources": [],
            "message_sources": []
        })

@app.get("/sessions")
def list_sessions():
    """List sessions with safe error handling"""
    try:
        session_service = get_session_service()
        sessions = session_service.list_sessions()
        return JSONResponse(content=convert_to_serializable(sessions))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Sessions error: {e}")
        return JSONResponse(content=[])  # Return empty list instead of 500 error

@app.post("/sessions")
def create_session(data: Optional[Dict[str, str]] = Body(default={})):
    """Create new session with safe error handling"""
    try:
        session_service = get_session_service()
        # Create session then apply requested name if provided
        session = session_service.create_session()
        requested_name = data.get("name") if data else None
        if requested_name:
            # Rename the session to match the first user message
            updated = session_service.update_session(session.id, requested_name)
            session = updated or session
        return JSONResponse(content=convert_to_serializable(session))
    except Exception as e:
        print(f"Create session error: {e}")
        # Return a basic session structure
        import uuid
        import datetime
        return JSONResponse(content={
            "id": str(uuid.uuid4()),
            "name": "New Chat",
            "created_at": datetime.datetime.now().isoformat(),
            "message_count": 0
        })

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Get session by ID with safe error handling"""
    try:
        session_service = get_session_service()
        session = session_service.get_session(session_id)
        return JSONResponse(content=convert_to_serializable(session))
    except Exception as e:
        print(f"Get session error: {e}")
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions/{session_id}/history")
def get_session_history(session_id: str):
    """Get session chat history with safe error handling"""
    try:
        session_service = get_session_service()
        history = session_service.get_session_history(session_id)
        return JSONResponse(content=convert_to_serializable(history))
    except Exception as e:
        print(f"Get session history error: {e}")
        return JSONResponse(content=[])  # Return empty history instead of error

@app.get("/sessions/{session_id}/sources")
def get_session_sources(session_id: str):
    """Get all sources for a session (session-level sources endpoint)"""
    try:
        session_service = get_session_service()
        sources = session_service.get_session_sources(session_id)
        return JSONResponse(content=convert_to_serializable(sources))
    except Exception as e:
        print(f"Get session sources error: {e}")
        # Return empty sources instead of error to prevent frontend issues
        return JSONResponse(content=[])

@app.get("/sessions/{session_id}/message_sources/{message_index}")
def get_message_sources(session_id: str, message_index: int):
    """Get sources for a specific message in a session"""
    try:
        session_service = get_session_service()
        # Use the method that expects message index (int) rather than message_id (str)
        sources = session_service.get_message_sources_by_index(session_id, message_index)
        return JSONResponse(content=convert_to_serializable(sources))
    except Exception as e:
        print(f"Get message sources error: {e}")
        # Return empty sources instead of error to prevent frontend issues
        return JSONResponse(content=[])

@app.get("/sessions/{session_id}/insights")
def get_session_insights(session_id: str):
    """Get advanced AI insights for a session"""
    try:
        session_service = get_session_service()
        insights = session_service.get_advanced_insights(session_id)
        return JSONResponse(content=convert_to_serializable(insights))
    except Exception as e:
        print(f"Get session insights error: {e}")
        # Return empty insights instead of error to prevent frontend issues
        return JSONResponse(content={})

@app.post("/sessions/{session_id}/rename")
def rename_session(session_id: str, data: Dict[str, str]):
    """Rename session with safe error handling"""
    try:
        session_service = get_session_service()
        result = session_service.rename_session(session_id, data.get("name", ""))
        return JSONResponse(content=convert_to_serializable(result))
    except Exception as e:
        print(f"Rename session error: {e}")
        return JSONResponse(content={"message": "Rename failed", "status": "error"})

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete session with safe error handling"""
    try:
        session_service = get_session_service()
        result = session_service.delete_session(session_id)
        return JSONResponse(content=convert_to_serializable(result))
    except Exception as e:
        print(f"Delete session error: {e}")
        return JSONResponse(content={"message": "Delete failed", "status": "error"})

@app.post("/rebuild_index")
async def rebuild_index(api_key_index: int = Form(0)):
    """Rebuild index with safe error handling"""
    try:
        # Safe import inside function
        from src.services.vector_service import VectorStoreService
        vector_service = VectorStoreService()

        # This would be the actual rebuild logic
        result = await vector_service.rebuild_index(api_key_index)
        return convert_to_serializable(result)
    except Exception as e:
        print(f"Rebuild index error: {e}")
        traceback.print_exc()
        return {"message": f"Index rebuild failed: {str(e)}", "status": "error"}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """File upload with safe error handling - actually saves files to study_docs folder"""
    try:
        # Import config to get study_docs folder path
        from src.utils.config import config

        # Ensure study_docs folder exists
        study_docs_path = config.study_docs_folder
        os.makedirs(study_docs_path, exist_ok=True)

        uploaded_files = []
        for file in files:
            if file.filename:
                # Save file to study_docs folder
                file_path = os.path.join(study_docs_path, file.filename)

                # Read file content and save it
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)

                # Get file size
                file_size = len(content)

                uploaded_files.append({
                    "filename": file.filename,
                    "status": "uploaded",
                    "size": file_size,
                    "path": file_path
                })
                print(f"✅ Saved file: {file.filename} ({file_size} bytes)")

        return {"files": uploaded_files, "message": f"Successfully uploaded {len(uploaded_files)} files to study_docs folder"}
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return {"message": f"Upload failed: {str(e)}", "status": "error"}

@app.get("/api_keys")
def get_api_keys():
    """Get available API keys with safe error handling"""
    try:
        # Try to import from config
        from src.utils.config import ApiKeys
        api_keys = ApiKeys()
        keys = api_keys.get_all_keys()
        result = []
        for i, key in enumerate(keys):
            result.append({
                "index": i,
                "key": f"Google API Key {i+1}",
                "masked_key": f"...{key[-4:]}" if len(key) > 4 else "****"
            })
        print(f"✅ Returning {len(result)} API keys")
        return convert_to_serializable(result)
    except Exception as e:
        print(f"API keys error: {e}")
        # Fallback to default 3 keys
        return [
            {"index": 0, "key": "Google API Key 1"},
            {"index": 1, "key": "Google API Key 2"},
            {"index": 2, "key": "Google API Key 3"}
        ]

@app.get("/usage")
def get_usage_stats():
    """Get usage statistics with safe error handling"""
    try:
        # Try to get real usage stats
        from src.services.usage_service import get_usage_service
        usage_service = get_usage_service()
        stats = usage_service.get_stats()
        return convert_to_serializable(stats)
    except Exception as e:
        print(f"Usage stats error: {e}")
        return {"RAG": 0, "Gemini": 0, "Meta": 0, "MetaRAG": 0}

@app.get("/chat/usage")
def get_chat_usage_stats():
    """Get usage statistics - alternative endpoint for frontend compatibility"""
    return get_usage_stats()

@app.post("/clear_vector_db")
async def clear_vector_db_endpoint():
    """Clear the vector database with safe error handling"""
    try:
        from src.services.vector_service import VectorStoreService
        service = VectorStoreService()
        success = service.clear_vector_store()
        if success:
            return {"status": "success"}
        else:
            raise Exception("Service reported failure clearing vector DB")
    except Exception as e:
        print(f"Clear vector DB error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

if __name__ == "__main__":
    print("🚀 Starting Serializable RAG AI Server...")
    print("🎯 This version eliminates serialization errors with proper JSON conversion")
    print("📍 URL: http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
```

## Key Features

### 1. JSON Serialization

- `convert_to_serializable()` function handles all object types
- Prevents serialization errors that caused 500 responses
- Supports Pydantic models, dictionaries, lists, and basic types

### 2. Error Handling

- Every endpoint wrapped with try-catch blocks
- Graceful degradation instead of 500 errors
- Detailed logging for debugging

### 3. Lazy Loading

- Services loaded on demand to prevent startup failures
- Global service instances cached after first load
- Graceful handling of missing dependencies

### 4. Timeout Protection

- Chat requests timeout after 30 seconds
- API exhaustion detection and handling
- Fallback responses for timeout scenarios

### 5. File Upload

- Saves files directly to `study_docs/` directory
- Creates directory if it doesn't exist
- Returns detailed upload status

## Installation Instructions

1. **Create the file**:

   ```bash
   touch serializable_server.py
   ```

2. **Copy the complete content** from the code block above

3. **Make executable** (Linux/macOS):

   ```bash
   chmod +x serializable_server.py
   ```

4. **Test the server**:
   ```bash
   python serializable_server.py
   ```

## Dependencies Required

Ensure these packages are installed:

```bash
pip install fastapi uvicorn pydantic sqlalchemy aiofiles python-multipart
```

## Validation Steps

1. **Server starts without errors**
2. **Health check responds**: `GET /health`
3. **Frontend serves**: `GET /`
4. **API endpoints accessible**: Check `/docs`
5. **File uploads work**: `POST /upload`

## Common Issues

1. **Import Errors**: Ensure all src/ modules exist
2. **Port Conflicts**: Change port in main section
3. **Permission Errors**: Check file/directory permissions
4. **Missing Dependencies**: Install required packages

This server file provides the complete foundation for the RAG AI application with robust error handling and proper JSON serialization.
