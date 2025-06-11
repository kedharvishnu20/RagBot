import uuid
from typing import Dict, List, Any, Optional
from threading import Lock
import time
import json
import os
from .db_models import Session as DBSession, Message as DBMessage, Source as DBSource, UsageStat, get_db_session
import datetime

class SessionManager:
    """Manages chat sessions and history using a database"""
    
    def __init__(self):
        # Remove persistent db session
        pass

    def get_or_create_session(self, session_id=None):
        """Get or create a session, returning a dictionary representation"""
        with get_db_session() as db:
            if session_id:
                session = db.query(DBSession).filter_by(id=session_id).first()
                if session:
                    # Return a dictionary with session data instead of the actual SQLAlchemy object
                    return {
                        "id": session.id,
                        "name": session.name,
                        "updated_at": session.updated_at,
                        "created_at": session.created_at,
                        "message_count": len(session.messages) if session.messages else 0
                    }
            
            # Create new session
            sid = session_id or str(uuid.uuid4())
            session = DBSession(id=sid, name="New Chat")
            db.add(session)
            db.flush()
            
            # Return a dictionary representation
            return {
                "id": session.id, 
                "name": session.name,
                "updated_at": session.updated_at,
                "created_at": session.created_at,
                "message_count": 0
            }

    def update_session(self, session_id, **kwargs):
        """Update a session and return a dictionary representation"""
        with get_db_session() as db:
            session = db.query(DBSession).filter_by(id=session_id).first()
            if not session:
                return None
                
            for key, value in kwargs.items():
                setattr(session, key, value)
            session.updated_at = datetime.datetime.utcnow()
            db.flush()
            
            # Return a dictionary representation
            return {
                "id": session.id,
                "name": session.name,
                "updated_at": session.updated_at,
                "created_at": session.created_at
            }

    def delete_session(self, session_id):
        with get_db_session() as db:
            session = db.query(DBSession).filter_by(id=session_id).first()
            if session:
                db.delete(session)
                return True
            return False

    def clear_all_sessions(self):
        with get_db_session() as db:
            db.query(DBSession).delete()

    def add_message(self, session_id, role, content, ai_type=None, sources=None):
        with get_db_session() as db:
            session = db.query(DBSession).filter_by(id=session_id).first()
            if not session:
                # Create session if it doesn't exist
                session = DBSession(id=session_id, name="New Chat")
                db.add(session)
                db.flush()
                
            message = DBMessage(session_id=session.id, role=role, content=content, ai_type=ai_type)
            
            # Add sources directly to the message if provided
            if sources:
                message.set_sources(sources)
            
            db.add(message)
            session.updated_at = datetime.datetime.utcnow()
            
            # Update usage stats
            if ai_type:
                stat = db.query(UsageStat).filter_by(ai_type=ai_type).first()
                if not stat:
                    stat = UsageStat(ai_type=ai_type, count=1)
                    db.add(stat)
                else:
                    stat.count += 1
                    
            return message.id

    def add_sources(self, session_id, sources):
        """Add sources to a session"""
        with get_db_session() as db:
            session = db.query(DBSession).filter_by(id=session_id).first()
            if not session:
                session = DBSession(id=session_id, name="New Chat")
                db.add(session)
                db.flush()
            
            # Ensure sources are accumulated, not overwritten
            existing_sources = db.query(DBSource).filter_by(session_id=session_id).all()
            # Use both name AND content for deduplication (not just name)
            existing_source_keys = {(source.name, source.content[:100]) for source in existing_sources}
            
            # Add new sources
            for source in sources:
                if hasattr(source, 'page_content') and hasattr(source, 'metadata'):
                    # Handle LangChain document type
                    name = os.path.basename(source.metadata.get("source", "Unknown"))
                    content = source.page_content
                    metadata = source.metadata
                    document_type = "document"  # Default type
                elif isinstance(source, dict):
                    # Handle dict format with type information
                    name = source.get('name', 'Unknown')
                    content = source.get('content', '') or source.get('preview', '')
                    metadata = source.get('metadata', {})
                    document_type = source.get('document_type', 'document')
                elif isinstance(source, str):
                    # Handle string format (likely from Meta AI)
                    name = "External Source"
                    content = source[:1000]  # Limit content length
                    metadata = {}
                    document_type = "meta_ai"  # Assume it's from Meta AI
                else:
                    continue
                
                # Check for duplicates using both name and content
                source_key = (name, content[:100])
                if source_key not in existing_source_keys:
                    db_source = DBSource(
                        session_id=session_id,
                        name=name,
                        content=content,
                        document_type=document_type
                    )
                    db_source.set_metadata(metadata)
                    db.add(db_source)
                    existing_source_keys.add(source_key)  # Add to set to prevent duplicates in same batch
        
    def get_sources(self, session_id):
        """Get sources for a session"""
        with get_db_session() as db:
            sources = db.query(DBSource).filter_by(session_id=session_id).all()
            return [
                {
                    "name": source.name,
                    "content": source.content,  # This was missing!                "preview": source.content[:300],
                    "metadata": source.get_metadata(),
                    "document_type": source.document_type
                }
                for source in sources
            ]

    def list_sessions(self):
        """List all sessions as dictionaries"""
        with get_db_session() as db:
            sessions = db.query(DBSession).all()
            result = []
            for s in sessions:
                result.append({
                    "id": s.id,
                    "name": s.name,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                    "message_count": 0  # Temporarily set to 0 to avoid expensive query
                })
            return result

    def get_usage_stats(self):
        with get_db_session() as db:
            stats = db.query(UsageStat).all()
            return {stat.ai_type: stat.count for stat in stats}

    def get_session_with_history(self, session_id):
        """Get a session with its complete message history"""
        with get_db_session() as db:
            session = db.query(DBSession).filter_by(id=session_id).first()
            if not session:
                return None
                
            return {
                "id": session.id,
                "name": session.name,
                "updated_at": session.updated_at,
                "created_at": session.created_at,
                "history": [
                    {
                        "role": m.role, 
                        "content": m.content, 
                        "ai_type": m.ai_type, 
                        "timestamp": m.timestamp,                        "sources": m.get_sources() if hasattr(m, 'get_sources') else []
                    }
                    for m in session.messages
                ]
            }
    
    def get_message_sources(self, session_id, message_index):
        """Get sources specifically for a message in the chat history"""
        print(f"DEBUG: get_message_sources called with session_id={session_id}, message_index={message_index}")
        with get_db_session() as db:
            # First get all messages for this session
            session = db.query(DBSession).filter_by(id=session_id).first()
            if not session:
                print(f"DEBUG: No session found with id {session_id}")
                return []
                
            print(f"DEBUG: Session found with {len(session.messages)} messages")
                
            # Get the messages ordered by timestamp to match the message_index
            messages = sorted(session.messages, key=lambda m: m.timestamp)
            
            # Check if message_index is valid
            if message_index < 0 or message_index >= len(messages):
                return []
                  # Only assistant messages have sources
            message = messages[message_index]
            if message.role != "assistant":
                return []
                
            # First, check if message has sources directly stored
            if hasattr(message, 'get_sources') and message.message_sources:
                sources = message.get_sources()
                print(f"DEBUG: Message {message_index} get_sources() returned {len(sources) if sources else 'None'}")
                if sources:
                    print(f"Found {len(sources)} sources for message {message_index} directly from message.")
                    # Ensure they have the required fields
                    for source in sources:
                        if isinstance(source, dict):
                            source["message_index"] = message_index
                            if "preview" not in source and "content" in source:
                                source["preview"] = source["content"][:300]
                            if "relevance" not in source:
                                source["relevance"] = "high"
                    return sources
            
            # If no direct sources, check for sources in the session that were added close to this message's timestamp
            all_sources = db.query(DBSource).filter_by(session_id=session_id).all()
            
            if not all_sources:
                print(f"No sources found in session {session_id}")
                return []
                
            # Get closest sources by timestamp proximity (improved)
            message_time = message.timestamp
            # Use a reasonable time window (15 minutes before and after the message)
            time_window = datetime.timedelta(minutes=15)
            
            # Get sources created around the same time as the message
            time_relevant_sources = [
                s for s in all_sources 
                if abs((message_time - s.created_at).total_seconds()) < time_window.total_seconds()
            ]
            
            # If we found sources in the time window, use them
            if time_relevant_sources:
                return [
                    {
                        "name": source.name,
                        "content": source.content,
                        "preview": source.content[:300],
                        "metadata": source.get_metadata(),
                        "document_type": source.document_type,
                        "message_index": message_index,
                        "relevance": "medium"
                    }
                    for source in time_relevant_sources
                ]
                
            # Last resort - fall back to using general session sources
            # Limit to newest 3 sources to avoid overwhelming the UI
            newest_sources = sorted(all_sources, key=lambda s: s.created_at, reverse=True)[:3]
            
            return [
                {
                    "name": source.name,
                    "content": source.content,
                    "preview": source.content[:300],
                    "metadata": source.get_metadata(),
                    "document_type": source.document_type,
                    "message_index": message_index,
                    "relevance": "low" 
                }
                for source in newest_sources
            ]
        
    def get_most_relevant_sources_for_message(self, session_id, message_index, max_sources=3):
        """Get the most relevant sources for a specific message based on content similarity"""
        with get_db_session() as db:
            # First get the message
            session = db.query(DBSession).filter_by(id=session_id).first()
            if not session or not session.messages:
                return []
                
            # Get messages ordered by timestamp
            messages = sorted(session.messages, key=lambda m: m.timestamp)
            
            # Check if message_index is valid
            if message_index < 0 or message_index >= len(messages):
                return []
                
            # Skip if not an assistant message
            message = messages[message_index]
            if message.role != "assistant":
                return []
                
            # Get all sources
            sources = db.query(DBSource).filter_by(session_id=session_id).all()
            if not sources:
                return []
            
            # Simple relevance scoring based on content overlap
            # This is a naive approach but works for basic matching
            message_content = message.content.lower()
            scored_sources = []
            
            for source in sources:
                source_content = source.content.lower()
                
                # Calculate a simple relevance score based on word overlap
                message_words = set(message_content.split())
                source_words = set(source_content.split())
                
                if not message_words or not source_words:
                    continue
                    
                # Intersection of words divided by union (Jaccard similarity)
                overlap = len(message_words.intersection(source_words))
                union = len(message_words.union(source_words))
                
                if union > 0:
                    score = overlap / union
                    scored_sources.append((source, score))
            
            # Sort by relevance score
            scored_sources.sort(key=lambda x: x[1], reverse=True)
            
            # Return top sources
            top_sources = [source for source, _ in scored_sources[:max_sources]]
            
            return [
                {
                    "name": source.name,
                    "content": source.content,
                    "preview": source.content[:300],
                    "metadata": source.get_metadata(),
                    "document_type": source.document_type,
                    "message_index": message_index,
                    "relevance": "high" if i == 0 else ("medium" if i == 1 else "low")
                }
                for i, source in enumerate(top_sources)
            ]
