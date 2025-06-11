#!/usr/bin/env python3
"""
Usage statistics service for tracking AI mode usage
Uses database storage for persistent stats
"""
from typing import Dict, Any
from src.utils.db_models import UsageStat, get_db_session

class UsageService:
    """Usage statistics service using database storage"""
    
    def __init__(self):        # Default AI modes - ensures these always exist in stats
        self.default_modes = ["RAG", "Gemini", "Meta", "MetaRAG"]
        self._initialize_stats()
    
    def _initialize_stats(self):
        """Initialize usage statistics in database if needed"""
        with get_db_session() as db:
            # Check if stats exist for default modes
            for mode in self.default_modes:
                stat = db.query(UsageStat).filter_by(ai_type=mode).first()
                if not stat:
                    # Create initial stat record
                    db.add(UsageStat(ai_type=mode, count=0))
    
    def increment_usage(self, ai_mode: str):
        """Increment usage count for an AI mode"""
        with get_db_session() as db:
            stat = db.query(UsageStat).filter_by(ai_type=ai_mode).first()
            if stat:
                stat.count += 1
            else:
                # Create new stat entry if it doesn't exist
                db.add(UsageStat(ai_type=ai_mode, count=1))
    
    def get_stats(self) -> Dict[str, int]:
        """Get current usage statistics"""
        with get_db_session() as db:
            stats = db.query(UsageStat).all()
            return {stat.ai_type: stat.count for stat in stats}
    
    def reset_stats(self):
        """Reset all usage statistics"""
        with get_db_session() as db:
            stats = db.query(UsageStat).all()
            for stat in stats:
                stat.count = 0

# Global instance
_usage_service = None

def get_usage_service() -> UsageService:
    """Get or create usage service instance"""
    global _usage_service
    if _usage_service is None:
        _usage_service = UsageService()
    return _usage_service
