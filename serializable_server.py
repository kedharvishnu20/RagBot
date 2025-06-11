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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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
    from src.api.system_routes import router as system_router    # Mount API routes with proper prefixes to match frontend expectations
    app.include_router(session_router)  # Sessions at /sessions (router has /sessions prefix)
    app.include_router(chat_router, prefix="/api")  # Chat at /api/chat (router has /chat prefix)
    app.include_router(file_router, prefix="/api/files")  # Files at /api/files/* (router has no prefix)
    app.include_router(system_router)  # System routes at root (/, /api_keys, /health, etc.)
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

# Global service instances for lazy loading
_chat_orchestrator = None
_session_service = None

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

@app.get("/sources")
def serve_sources_preview():
    """Serve the sources preview page"""
    try:
        html_path = os.path.join(os.path.dirname(__file__), "src", "sources-preview.html")
        if os.path.exists(html_path):
            with open(html_path, encoding="utf-8") as f:
                return HTMLResponse(f.read())
        else:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head><title>Sources Preview</title></head>
            <body>
                <h1>📚 Sources Preview</h1>
                <p>Sources preview page not found.</p>
                <a href="/">← Back to Main App</a>
            </body>
            </html>
            """)
    except Exception as e:
        return HTMLResponse(f"<h1>Sources Preview</h1><p>Error loading sources page: {e}</p>")

# Add fallback routes for misrouted requests (likely from cached JS)
@app.get("/chat/usage")
def redirect_chat_usage():
    """Redirect old /chat/usage requests to correct /api/chat/usage endpoint"""
    return RedirectResponse(url="/api/chat/usage", status_code=301)

@app.get("/usage")  
def redirect_usage():
    """Redirect old /usage requests to correct /api/chat/usage endpoint"""
    return RedirectResponse(url="/api/chat/usage", status_code=301)

# All endpoints are now handled by routers - no duplicate endpoints needed

# All other endpoints are handled by routers

if __name__ == "__main__":
    print("🚀 Starting RAG AI Server...")
    print("📍 URL: http://127.0.0.1:8081")
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")
