#!/usr/bin/env python3
"""
API Exhaustion Recovery - Create fallback responses when APIs are exhausted
"""
import asyncio
import time
from typing import Dict, Any, List

class APIExhaustionHandler:
    """Handle API exhaustion gracefully with fallback responses"""
    
    def __init__(self):
        self.api_timeout = 15  # 15 second timeout for API calls
        self.exhaustion_messages = [
            "🔄 I'm currently experiencing high demand and my AI services are temporarily limited. Please try again in a few minutes.",
            "⏳ The AI services are currently at capacity. Your request is important - please retry shortly.",
            "🚦 I'm processing many requests right now. Please wait a moment and try your question again.",
            "💭 My thinking processes are currently overloaded. Give me a moment to catch up!",
            "🔋 I'm running low on API resources right now. Please try again in a few minutes for the best response."
        ]
        
    async def safe_ai_call(self, ai_function, *args, **kwargs) -> Dict[str, Any]:
        """Make an AI call with timeout protection"""
        try:
            # Create timeout wrapper
            return await asyncio.wait_for(
                ai_function(*args, **kwargs),
                timeout=self.api_timeout
            )
        except asyncio.TimeoutError:
            print(f"⏰ AI call timed out after {self.api_timeout} seconds - API likely exhausted")
            return self.get_exhaustion_response()
        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['422', 'unprocessable', 'rate limit', 'quota', 'throttle']):
                print(f"🚫 API exhaustion detected: {e}")
                return self.get_exhaustion_response()
            else:
                print(f"❌ Unexpected AI error: {e}")
                return {
                    'answer': f"I encountered an unexpected error: {str(e)[:100]}",
                    'sources': []
                }
    
    def get_exhaustion_response(self) -> Dict[str, Any]:
        """Get a friendly exhaustion response"""
        import random
        message = random.choice(self.exhaustion_messages)
        return {
            'answer': message,
            'sources': [],
            'status': 'api_exhausted'
        }

# Create singleton instance
api_exhaustion_handler = APIExhaustionHandler()

def create_timeout_aware_chat_response(message: str) -> Dict[str, Any]:
    """Create a timeout-aware response for exhausted APIs"""
    return {
        "answer": "🔄 I'm currently experiencing high demand. The AI services are temporarily limited due to API quotas. Please try again in a few minutes for the best response.",
        "answers": [
            "🔄 I'm currently experiencing high demand. The AI services are temporarily limited due to API quotas. Please try again in a few minutes for the best response."
        ],
        "sources": [],
        "message_sources": [],
        "status": "api_exhausted",
        "retry_after": 300  # Suggest retry after 5 minutes
    }

if __name__ == "__main__":
    print("API Exhaustion Handler Ready")
    response = create_timeout_aware_chat_response("test")
    print(f"Sample response: {response}")
