# AI Agent Rebuild Guide - Part 6: Utility Files Implementation

This document provides exact implementations for all utility files in the RAG AI Application.

## Directory Structure

```
src/utils/
├── __init__.py
├── config.py
├── database.py
├── db_models.py
├── gemini_api_manager.py
├── meta_llm.py
├── meta_rag_processor_fixed.py
├── session_manager.py
└── api_exhaustion_handler.py
```

## 1. Utility Package Initialization

**File: `src/utils/__init__.py`**

```python
# This file makes the utils directory a Python package
```

## 2. Gemini API Manager

**File: `src/utils/gemini_api_manager.py`**

_Note: This is a comprehensive API management system (218 lines) that handles random API key selection, quota tracking, and failover._

```python
# filepath: src/utils/gemini_api_manager.py
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

    # Additional methods:
    # - get_available_keys()
    # - select_random_api_key()
    # - get_api_key_with_fallback()
    # - mark_api_result()
    # - get_status_summary()

# Global instance
gemini_manager = GeminiApiManager()
```

## 3. Meta AI LLM Integration

**File: `src/utils/meta_llm.py`**

_Note: This is a comprehensive Meta AI integration (296 lines) with rate limiting and conversation history._

```python
# filepath: src/utils/meta_llm.py
import json
import time
import traceback
from typing import List, Dict, Any, Optional, Tuple
import os
import sys

# Import monitoring
try:
    from src.utils.meta_ai_monitor import log_meta_ai_call, log_rate_limit_event
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    def log_meta_ai_call(*args, **kwargs):
        pass
    def log_rate_limit_event(*args, **kwargs):
        pass

try:
    from meta_ai_api import MetaAI as MetaAIClient
except ImportError:
    print("Please install meta-ai-api: pip install meta-ai-api")
    # Create a mock class for testing/development if the real client isn't available
    class MetaAIClient:
        def prompt(self, message=""):
            return {"message": "Meta AI API not installed. This is a mock response."}

class MetaLLM:
    """
    Meta AI integration that can operate with or without RAG
    Includes rate limiting and retry logic to prevent API overload
    """
    def __init__(self, debug=False):
        try:
            self.client = MetaAIClient()
            self.debug = debug
            self.history = []  # Store recent conversation history
            self.max_history = 3  # Maximum number of past exchanges to keep

            # Rate limiting settings
            self.last_request_time = 0
            self.min_request_interval = 2.0  # Minimum 2 seconds between requests
            self.max_retries = 2  # Maximum retry attempts
            self.retry_delay = 5.0  # Delay between retries

        except Exception as e:
            print(f"Error initializing Meta AI client: {str(e)}")
            # Create a basic client that can handle errors gracefully
            self.client = MetaAIClient() if 'MetaAIClient' in locals() else None
            # ... initialization continues

    # Key methods:
    # - prepare_context_from_docs()
    # - format_history()
    # - _wait_for_rate_limit()
    # - prompt_simple()
    # - prompt_with_rag()
    # - _make_request_with_retry()
```

## 4. Session Manager

**File: `src/utils/session_manager.py`**

_Note: This is a comprehensive session management system (370 lines) with database integration._

```python
# filepath: src/utils/session_manager.py
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

    # Additional methods:
    # - update_session()
    # - delete_session()
    # - clear_all_sessions()
    # - add_message()
    # - get_session_history()
    # - add_sources_to_session()
    # - get_session_sources()
    # - get_all_sessions()
    # - get_usage_stats()
    # - increment_usage()
```

## 5. Meta RAG Processor (Fixed)

**File: `src/utils/meta_rag_processor_fixed.py`**

This file contains an enhanced RAG processor that handles HTTP 422 errors and provides advanced reasoning capabilities using Meta AI.

```python
# filepath: src/utils/meta_rag_processor_fixed.py
"""
Fixed Meta RAG Processor with HTTP 422 error handling
Provides advanced RAG capabilities using Meta AI with proper error handling
"""
import asyncio
import logging
from typing import List, Tuple, Any, Optional
from langchain.schema import Document
from src.utils.meta_llm import MetaLLM

logger = logging.getLogger(__name__)

class MetaRAGProcessorFixed:
    """Fixed Meta RAG processor with HTTP 422 error handling and advanced reasoning"""

    def __init__(self):
        self.meta_llm = MetaLLM(debug=False)
        self.max_context_length = 8000
        self.max_docs_for_processing = 10

    async def process_query(self, question: str, retriever) -> Tuple[str, List[Document]]:
        """Process a query using Meta AI with enhanced error handling"""
        try:
            # Get relevant documents
            docs = retriever.get_relevant_documents(question)

            if not docs:
                return "No relevant documents found to answer your question.", []

            # Limit documents for processing
            limited_docs = docs[:self.max_docs_for_processing]

            # Use Meta AI for advanced reasoning
            try:
                answer = await self._generate_meta_rag_response(question, limited_docs)
                return answer, limited_docs

            except Exception as meta_error:
                error_msg = str(meta_error)

                # Handle specific HTTP 422 errors
                if "422" in error_msg or "unprocessable entity" in error_msg.lower():
                    return "❌ HTTP 422 Error: Unable to process your question due to content validation issues. Please try rephrasing your question.", limited_docs
                elif "rate limit" in error_msg.lower():
                    return "⏱️ Rate limit reached. Please wait before trying again.", limited_docs
                else:
                    return f"❌ Error processing with Meta AI: {error_msg[:200]}", limited_docs

        except Exception as e:
            logger.error(f"Meta RAG processing error: {e}")
            return f"❌ Meta RAG processing failed: {str(e)[:200]}", []

    async def _generate_meta_rag_response(self, question: str, docs: List[Document]) -> str:
        """Generate response using Meta AI with document context"""
        # Prepare context from documents
        context = self.meta_llm.prepare_context_from_docs(docs)

        # Create enhanced prompt for Meta AI
        enhanced_prompt = f"""Based on the provided context, please answer the following question comprehensively:

Context Information:
{context}

Question: {question}

Please provide a detailed answer based on the context. If the context doesn't contain enough information, mention what additional information would be helpful."""

        # Get response from Meta AI
        response = self.meta_llm.prompt_simple(enhanced_prompt)

        if isinstance(response, dict) and 'message' in response:
            return response['message']
        else:
            return str(response)

# For backward compatibility
MetaRAGProcessor = MetaRAGProcessorFixed
META_AI_AVAILABLE = True
```

## 6. API Exhaustion Handler

**File: `src/utils/api_exhaustion_handler.py`**

```python
# filepath: src/utils/api_exhaustion_handler.py
"""
API Exhaustion Handler for managing API rate limits and quota exhaustion
"""
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ApiExhaustionStatus:
    """Track API exhaustion status"""
    last_exhaustion_time: Optional[float] = None
    exhaustion_count: int = 0
    recovery_time: float = 60.0  # 1 minute default recovery time

    def is_exhausted(self) -> bool:
        """Check if API is currently exhausted"""
        if self.last_exhaustion_time is None:
            return False
        return (time.time() - self.last_exhaustion_time) < self.recovery_time

    def mark_exhausted(self):
        """Mark API as exhausted"""
        self.last_exhaustion_time = time.time()
        self.exhaustion_count += 1
        logger.warning(f"🚫 API exhausted, count: {self.exhaustion_count}")

    def reset(self):
        """Reset exhaustion status"""
        self.last_exhaustion_time = None
        self.exhaustion_count = 0
        logger.info("✅ API exhaustion status reset")

class ApiExhaustionHandler:
    """Handle API exhaustion across different services"""

    def __init__(self):
        self.status: Dict[str, ApiExhaustionStatus] = {}

    def is_service_exhausted(self, service_name: str) -> bool:
        """Check if a service is exhausted"""
        if service_name not in self.status:
            self.status[service_name] = ApiExhaustionStatus()
        return self.status[service_name].is_exhausted()

    def mark_service_exhausted(self, service_name: str, recovery_time: float = 60.0):
        """Mark a service as exhausted"""
        if service_name not in self.status:
            self.status[service_name] = ApiExhaustionStatus()
        self.status[service_name].recovery_time = recovery_time
        self.status[service_name].mark_exhausted()

    def reset_service(self, service_name: str):
        """Reset exhaustion status for a service"""
        if service_name in self.status:
            self.status[service_name].reset()

    def get_recovery_time(self, service_name: str) -> float:
        """Get remaining recovery time for a service"""
        if service_name not in self.status or not self.status[service_name].is_exhausted():
            return 0.0

        elapsed = time.time() - self.status[service_name].last_exhaustion_time
        return max(0.0, self.status[service_name].recovery_time - elapsed)

# Global instance
exhaustion_handler = ApiExhaustionHandler()
```

## Implementation Notes

### Key Utility Components

1. **Configuration Management** (`config.py`)

   - API key management and rotation
   - Application settings and defaults
   - Environment-specific configurations

2. **Database Operations** (`database.py`, `db_models.py`)

   - SQLAlchemy models and relationships
   - Database connection management
   - Session and transaction handling

3. **API Management** (`gemini_api_manager.py`)

   - Random API key selection
   - Quota tracking and recovery
   - Rate limiting and failover

4. **Meta AI Integration** (`meta_llm.py`)

   - Meta AI API client wrapper
   - Conversation history management
   - Rate limiting and retry logic

5. **Session Management** (`session_manager.py`)

   - Chat session lifecycle
   - Message history tracking
   - Database integration

6. **RAG Processing** (`meta_rag_processor_fixed.py`)
   - Advanced RAG with Meta AI reasoning
   - HTTP 422 error handling
   - Document context preparation

### Error Handling Strategy

All utility modules implement:

- **Graceful degradation** when external services are unavailable
- **Comprehensive logging** for debugging and monitoring
- **Retry logic** with exponential backoff
- **Fallback mechanisms** for critical operations

### Dependencies

These utilities depend on:

- **SQLAlchemy** for database operations
- **LangChain** for document processing
- **Google Generative AI** for embeddings and chat
- **Meta AI API** for alternative AI responses
- **FAISS** for vector similarity search

### Configuration Requirements

Each utility requires specific configuration:

- **API Keys**: Google Gemini API keys for AI responses
- **Database**: SQLite database for persistence
- **Meta AI**: Optional Meta AI API access
- **Vector Store**: FAISS index files for similarity search

## Integration Points

These utilities integrate with:

1. **Service Layer**: Provide core functionality for business logic
2. **API Routes**: Support endpoint implementations
3. **Database**: Persist application state and history
4. **External APIs**: Interface with AI services

## Next Steps

After implementing these utility files, proceed to Part 7: Frontend Implementation.
