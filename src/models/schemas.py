from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    session_id: str
    message: str
    ai_modes: List[str]
    api_key_index: int = 0
    gemini_model: str = "gemini-1.5-flash"

class SourceItem(BaseModel):
    """Model for source document information"""
    name: Optional[str] = None
    content: Optional[str] = None
    preview: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            'object': lambda obj: str(obj)
        }

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: Optional[str] = None
    answers: Optional[List[str]] = None
    sources: Optional[List[Union[str, Dict[str, Any]]]] = None
    message_sources: Optional[List[List[Union[str, Dict[str, Any]]]]] = None
    
    class Config:
        arbitrary_types_allowed = True

class SessionResponse(BaseModel):
    """Response model for session data"""
    id: str
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    message_count: int = 0

class MessageResponse(BaseModel):
    """Response model for individual messages"""
    role: str
    content: str
    ai_type: Optional[str] = None
    timestamp: Optional[str] = None
    sources: Optional[List[SourceItem]] = None

class UploadResponse(BaseModel):
    """Response model for file upload"""
    filename: str
    status: str
    message: Optional[str] = None

class ApiKeyResponse(BaseModel):
    """Response model for API key information"""
    index: int
    name: str

class UsageStatsResponse(BaseModel):
    """Response model for usage statistics"""
    RAG: int = 0
    Gemini: int = 0
    Meta: int = 0
    MetaRAG: int = 0

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    message: str
    timestamp: Optional[str] = None
