from typing import List, Dict, Any, Optional
from src.utils.session_manager import SessionManager
from src.models.schemas import (
    SessionResponse, 
    MessageResponse, 
    UsageStatsResponse,
    SourceItem
)
from src.utils.config import AI_MODES

class SessionService:
    """Service for managing chat sessions"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.usage_stats = {"RAG": 0, "Gemini": 0, "Meta": 0, "MetaRAG": 0}
    
    def list_sessions(self) -> List[SessionResponse]:
        """Get list of all sessions"""
        sessions_data = self.session_manager.list_sessions()
        return [
            SessionResponse(
                id=session["id"],
                name=session["name"],
                created_at=session.get("created_at").isoformat() if session.get("created_at") else None,
                updated_at=session.get("updated_at").isoformat() if session.get("updated_at") else None,
                message_count=session.get("message_count", 0)
            )
            for session in sessions_data
        ]
    
    def get_session(self, session_id: str) -> Optional[SessionResponse]:
        """Get a specific session"""
        session_data = self.session_manager.get_session_with_history(session_id)
        if not session_data:
            return None
        
        return SessionResponse(
            id=session_data["id"],
            name=session_data["name"],
            created_at=session_data.get("created_at").isoformat() if session_data.get("created_at") else None,
            updated_at=session_data.get("updated_at").isoformat() if session_data.get("updated_at") else None,
            message_count=len(session_data.get("history", []))
        )
    
    def create_session(self) -> SessionResponse:
        """Create a new session"""
        session_data = self.session_manager.get_or_create_session()
        
        return SessionResponse(
            id=session_data["id"],
            name=session_data["name"],
            created_at=session_data.get("created_at").isoformat() if session_data.get("created_at") else None,
            updated_at=session_data.get("updated_at").isoformat() if session_data.get("updated_at") else None,
            message_count=session_data.get("message_count", 0)
        )
    
    def update_session(self, session_id: str, name: str) -> Optional[SessionResponse]:
        """Update session name"""
        session_data = self.session_manager.update_session(session_id, name=name)
        if not session_data:
            return None
        
        return SessionResponse(
            id=session_data["id"],
            name=session_data["name"],
            created_at=session_data.get("created_at").isoformat() if session_data.get("created_at") else None,
            updated_at=session_data.get("updated_at").isoformat() if session_data.get("updated_at") else None,
            message_count=session_data.get("message_count", 0)
        )
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        return self.session_manager.delete_session(session_id)
    
    def rename_session(self, session_id: str, name: str) -> Optional[SessionResponse]:
        """Rename a session (alias for update_session for compatibility)"""
        return self.update_session(session_id, name)
    
    def add_user_message(self, session_id: str, message: str) -> None:
        """Add user message to session"""
        self.session_manager.add_message(session_id, "user", message, ai_type=None)
    
    def add_assistant_message(self, session_id: str, message: str, ai_type: str, sources: List[SourceItem] = None) -> None:
        """Add assistant message to session"""
        self.session_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=message,
            ai_type=ai_type,
            sources=sources or []
        )
        
        # Update usage stats
        if ai_type in self.usage_stats:
            self.usage_stats[ai_type] += 1
    
    def get_session_history(self, session_id: str) -> List[MessageResponse]:
        """Get session chat history"""
        session_data = self.session_manager.get_session_with_history(session_id)
        if not session_data or "history" not in session_data:
            return []
        
        messages = []        
        for msg in session_data["history"]:
            # Convert timestamp to string if it's a datetime object
            timestamp = msg.get("timestamp")
            if timestamp and hasattr(timestamp, 'isoformat'):
                timestamp = timestamp.isoformat()
            
            message_response = MessageResponse(
                role=msg["role"],
                content=msg["content"],
                ai_type=msg.get("ai_type"),
                timestamp=timestamp,
                sources=msg.get("sources", [])
            )
            messages.append(message_response)
        
        return messages
    
    def get_session_sources(self, session_id: str) -> List[SourceItem]:
        """Get all sources for a session"""
        sources_data = self.session_manager.get_sources(session_id)
        if not sources_data:
            return []
        
        sources = []
        for source in sources_data:
            if isinstance(source, dict):
                sources.append(SourceItem(**source))
            else:                # Handle legacy string sources
                sources.append(SourceItem(
                    name="Legacy Source",
                    content=str(source)[:500],
                    document_type="legacy"
                ))
        
        return sources
    
    def add_sources_to_session(self, session_id: str, sources: List[Any]) -> None:
        """Add sources to session"""
        # Convert sources to dictionaries (handle both SourceItem objects and dictionaries)
        sources_data = []
        for source in sources:
            if hasattr(source, 'dict') and callable(getattr(source, 'dict')):
                # SourceItem object
                sources_data.append(source.dict())
            elif isinstance(source, dict):
                # Already a dictionary
                sources_data.append(source)
            else:
                # Convert other types to dictionary
                sources_data.append({                    "name": str(source)[:100],
                    "content": str(source)[:500],
                    "metadata": {},
                    "document_type": "unknown"
                })
        self.session_manager.add_sources(session_id, sources_data)
    
    def get_message_sources_by_index(self, session_id: str, message_index: int) -> List[SourceItem]:
        """Get sources for a specific message by index"""
        sources_data = self.session_manager.get_message_sources(session_id, message_index)
        if not sources_data:
            return []
        
        sources = []
        for source in sources_data:
            if isinstance(source, dict):
                sources.append(SourceItem(**source))
            else:
                sources.append(SourceItem(
                    name="Message Source",
                    content=str(source)[:500],
                    document_type="message"
                ))
        
        return sources
    
    def get_usage_stats(self) -> UsageStatsResponse:
        """Get AI mode usage statistics"""
        db_stats = self.session_manager.get_usage_stats()
          # Merge with in-memory stats
        for mode in self.usage_stats:
            if mode in db_stats:
                self.usage_stats[mode] = max(self.usage_stats[mode], db_stats[mode])
        
        return UsageStatsResponse(**self.usage_stats)
    
    def get_available_ai_modes(self) -> List[str]:
        """Get list of available AI modes"""
        return AI_MODES.copy()
    
    def validate_ai_modes(self, ai_modes: List[str]) -> bool:
        """Validate that all AI modes are supported"""
        return all(mode in AI_MODES for mode in ai_modes)
    
    def get_message_sources(self, session_id: str, message_id: str) -> List[Dict[str, Any]]:
        """Get sources for a specific message in a session"""
        try:
            # Get session with history
            session_data = self.session_manager.get_session_with_history(session_id)
            if not session_data:
                return []
            
            # Look for the message in the session history
            history = session_data.get("history", [])
            for message in history:
                if str(message.get("id", "")) == str(message_id):
                    # Return message sources if they exist
                    sources = message.get("sources", [])
                    # Convert sources to dictionaries if they're not already
                    result = []
                    for source in sources:
                        if isinstance(source, dict):
                            result.append(source)
                        elif hasattr(source, 'dict') and callable(getattr(source, 'dict')):
                            result.append(source.dict())
                        else:
                            # Convert any other object to dict representation
                            result.append({
                                "name": getattr(source, 'name', 'Unknown'),
                                "url": getattr(source, 'url', ''),
                                "type": getattr(source, 'type', 'document'),
                                "content": getattr(source, 'content', '')
                            })
                    return result
            
            # Message not found
            return []
            
        except Exception as e:
            print(f"Error getting message sources: {e}")
            return []
    def add_advanced_insights(self, session_id: str, insights: Dict[str, Any]) -> None:
        """Add advanced AI insights to session for future reference"""
        try:
            session_data = self.session_manager.get_or_create_session(session_id)
            if "advanced_insights" not in session_data:
                session_data["advanced_insights"] = []
            
            # Add timestamp to insights
            insights["timestamp"] = self.session_manager._get_timestamp()
            session_data["advanced_insights"].append(insights)
            
            # Keep only last 10 insights to prevent memory bloat
            if len(session_data["advanced_insights"]) > 10:
                session_data["advanced_insights"] = session_data["advanced_insights"][-10:]
            
            self.session_manager.save_session(session_id, session_data)
        except Exception as e:
            print(f"⚠️ Failed to store advanced insights: {str(e)}")
    
    def get_advanced_insights(self, session_id: str) -> Dict[str, Any]:
        """Get the latest advanced AI insights for a session"""
        try:
            session_data = self.session_manager.get_session_with_history(session_id)
            if not session_data:
                return {}
            
            insights = session_data.get("advanced_insights", [])
            if insights:
                # Return the most recent insights
                return insights[-1]
            return {}
        except Exception as e:
            print(f"⚠️ Failed to retrieve advanced insights: {str(e)}")
            return {}
