"""
Gemini API Manager with Random Selection and Quota Handling
Implements random API key selection with 1-minute timeout tracking
"""
import time
import random
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from src.utils.config import api_keys
import logging

logger = logging.getLogger(__name__)

@dataclass
class ApiKeyStatus:
    """Track status of each API key"""
    index: int
    key: str
    last_used: float = 0.0
    quota_exhausted_at: Optional[float] = None
    consecutive_failures: int = 0
    is_available: bool = True
    
    def is_quota_exhausted(self) -> bool:
        """Check if API key is currently quota exhausted"""
        if self.quota_exhausted_at is None:
            return False
        
        # Check if 1 minute has passed since quota exhaustion
        return (time.time() - self.quota_exhausted_at) < 60.0
    
    def mark_quota_exhausted(self):
        """Mark API key as quota exhausted"""
        self.quota_exhausted_at = time.time()
        self.consecutive_failures += 1
        logger.warning(f"🚫 API key {self.index} quota exhausted, will retry after 1 minute")
    
    def mark_success(self):
        """Mark API key as successful"""
        self.quota_exhausted_at = None
        self.consecutive_failures = 0
        self.last_used = time.time()
        self.is_available = True
        logger.info(f"✅ API key {self.index} successful")
    
    def mark_failure(self):
        """Mark API key as failed (non-quota error)"""
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.is_available = False
            logger.warning(f"⚠️ API key {self.index} disabled after {self.consecutive_failures} failures")

class GeminiApiManager:
    """Manages Gemini API keys with random selection and quota handling"""
    
    def __init__(self):
        self.api_statuses: Dict[int, ApiKeyStatus] = {}
        self._initialize_api_keys()
        self._lock = asyncio.Lock()
    
    def _initialize_api_keys(self):
        """Initialize API key statuses"""
        valid_keys = api_keys.get_all_keys()
        
        for i, key in enumerate(valid_keys):
            self.api_statuses[i] = ApiKeyStatus(
                index=i,
                key=key[:8] + "..." if len(key) > 8 else key  # Store masked key for logging
            )
        
        logger.info(f"🔑 Initialized {len(self.api_statuses)} Gemini API keys")
    
    def get_available_keys(self) -> List[int]:
        """Get list of currently available API key indices"""
        available = []
        
        for index, status in self.api_statuses.items():
            if status.is_available and not status.is_quota_exhausted():
                available.append(index)
        
        return available
    
    def select_random_api_key(self) -> Optional[int]:
        """Select a random available API key"""
        available_keys = self.get_available_keys()
        
        if not available_keys:
            logger.warning("⚠️ No available API keys found")
            return None
        
        # Prefer keys that haven't been used recently
        now = time.time()
        weighted_keys = []
        
        for key_index in available_keys:
            status = self.api_statuses[key_index]
            # Weight by time since last use (prefer less recently used keys)
            time_since_use = now - status.last_used
            weight = max(1.0, time_since_use / 10.0)  # More weight for keys not used in last 10 seconds
            weighted_keys.extend([key_index] * int(weight))
        
        if weighted_keys:
            selected = random.choice(weighted_keys)
            logger.info(f"🎲 Selected random API key: {selected}")
            return selected
        
        # Fallback to simple random selection
        selected = random.choice(available_keys)
        logger.info(f"🎲 Selected fallback API key: {selected}")
        return selected
    
    async def get_api_key_with_fallback(self) -> Tuple[int, bool]:
        """
        Get an API key with fallback logic
        Returns: (api_key_index, is_fallback_used)
        """
        async with self._lock:
            # Try to get a random available key
            selected_index = self.select_random_api_key()
            
            if selected_index is not None:
                return selected_index, False
            
            # If no keys available, wait for the earliest quota-exhausted key to become available
            earliest_available = self._find_earliest_quota_recovery()
            
            if earliest_available is not None:
                recovery_time = earliest_available[1]
                wait_time = max(0, recovery_time - time.time())
                
                if wait_time > 0:
                    logger.info(f"⏳ Waiting {wait_time:.1f}s for API key {earliest_available[0]} quota recovery")
                    await asyncio.sleep(wait_time)
                
                # Clear quota exhaustion status
                self.api_statuses[earliest_available[0]].quota_exhausted_at = None
                return earliest_available[0], True
            
            # If all else fails, return the first available key (even if quota exhausted)
            if self.api_statuses:
                fallback_index = list(self.api_statuses.keys())[0]
                logger.warning(f"🆘 Using fallback API key {fallback_index}")
                return fallback_index, True
            
            raise ValueError("No API keys available")
    
    def _find_earliest_quota_recovery(self) -> Optional[Tuple[int, float]]:
        """Find the API key that will recover from quota exhaustion earliest"""
        earliest_recovery = None
        earliest_time = float('inf')
        
        for index, status in self.api_statuses.items():
            if status.quota_exhausted_at is not None:
                recovery_time = status.quota_exhausted_at + 60.0  # 1 minute recovery
                if recovery_time < earliest_time:
                    earliest_time = recovery_time
                    earliest_recovery = (index, recovery_time)
        
        return earliest_recovery
    
    def mark_api_result(self, api_index: int, success: bool, is_quota_error: bool = False):
        """Mark the result of an API call"""
        if api_index not in self.api_statuses:
            logger.warning(f"⚠️ Unknown API index: {api_index}")
            return
        
        status = self.api_statuses[api_index]
        
        if success:
            status.mark_success()
        elif is_quota_error:
            status.mark_quota_exhausted()
        else:
            status.mark_failure()
    
    def get_status_summary(self) -> Dict:
        """Get summary of all API key statuses"""
        summary = {
            "total_keys": len(self.api_statuses),
            "available": len(self.get_available_keys()),
            "quota_exhausted": 0,
            "disabled": 0,
            "details": {}
        }
        
        for index, status in self.api_statuses.items():
            if status.is_quota_exhausted():
                summary["quota_exhausted"] += 1
            elif not status.is_available:
                summary["disabled"] += 1
            
            summary["details"][index] = {
                "is_available": status.is_available,
                "is_quota_exhausted": status.is_quota_exhausted(),
                "consecutive_failures": status.consecutive_failures,
                "last_used": status.last_used
            }
        
        return summary
    
    def reset_api_key(self, api_index: int):
        """Reset an API key status (useful for manual recovery)"""
        if api_index in self.api_statuses:
            status = self.api_statuses[api_index]
            status.quota_exhausted_at = None
            status.consecutive_failures = 0
            status.is_available = True
            logger.info(f"🔄 Reset API key {api_index} status")
    
    def get_next_recovery_time(self) -> Optional[float]:
        """Get the next time when a quota-exhausted API key will recover"""
        earliest = self._find_earliest_quota_recovery()
        return earliest[1] if earliest else None

# Global instance
gemini_manager = GeminiApiManager()
