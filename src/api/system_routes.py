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
