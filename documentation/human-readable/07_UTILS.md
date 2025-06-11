# Utilities Documentation

## 📁 /src/utils/

**Purpose**: Utility functions, helpers, and core infrastructure  
**Location**: `/src/utils/`  
**Type**: Utility Layer

### Overview

Contains essential utility modules that provide core functionality like database management, configuration handling, API management, and specialized AI processing. These utilities support the entire application infrastructure.

---

## 📄 config.py

**Purpose**: Configuration management and API key handling  
**Location**: `/src/utils/config.py`  
**Type**: Configuration Utility

### Overview

Centralized configuration management for the application, handling environment variables, API keys, and system settings with validation and defaults.

### Key Classes

#### APIKeys

**Manages Google API keys with validation**

### Core Methods

#### get_all_keys()

**Purpose**: Retrieve all available API keys

```python
def get_all_keys() -> List[str]
```

**Features**:

- Environment variable parsing
- Key validation
- Automatic discovery of numbered keys
- Error handling for missing keys

#### get_key()

**Purpose**: Get specific API key by index

```python
def get_key(index: int) -> Optional[str]
```

**Parameters**:

- `index`: Zero-based API key index
- Returns: API key string or None if not found

#### is_valid_key()

**Purpose**: Validate API key format

```python
def is_valid_key(key: str) -> bool
```

**Validation**:

- Length checks
- Format validation
- Character set verification

### Configuration Settings

```python
# API Configuration
DEFAULT_MODEL = "gemini-1.5-flash"
TEMPERATURE = 0.1
MAX_TOKENS = 8192
TIMEOUT = 30

# Database Configuration
DATABASE_URL = "sqlite:///./rag_ai_app.db"
DB_ECHO = False

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ["pdf", "txt", "docx"]

# Vector Store Configuration
VECTOR_STORE_PATH = "./vector_store"
EMBEDDING_MODEL = "textembedding-gecko@003"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Server Configuration
APP_HOST = "0.0.0.0"
APP_PORT = 8001
DEBUG_MODE = False
```

### Environment Variable Loading

```python
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEYS = {
    i: os.getenv(f"GOOGLE_API_KEY_{i}")
    for i in range(10)  # Support up to 10 API keys
    if os.getenv(f"GOOGLE_API_KEY_{i}")
}
```

---

## 📄 database.py

**Purpose**: Database connection and initialization  
**Location**: `/src/utils/database.py`  
**Type**: Database Utility

### Overview

Handles SQLite database setup, connection management, and table initialization using SQLAlchemy with async support.

### Key Functions

#### init_db()

**Purpose**: Initialize database and create tables

```python
async def init_db() -> None
```

**Operations**:

- Create database file if not exists
- Initialize all tables from models
- Set up indexes for performance
- Configure WAL mode for SQLite

#### get_db_session()

**Purpose**: Get database session for operations

```python
async def get_db_session() -> AsyncSession
```

**Features**:

- Async session management
- Connection pooling
- Auto-commit handling
- Error recovery

#### create_tables()

**Purpose**: Create all database tables

```python
async def create_tables() -> None
```

**Tables Created**:

- `sessions`: Chat session data
- `messages`: Chat message history
- `files`: Uploaded file metadata
- `usage_logs`: API usage tracking

### Database Configuration

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Async SQLite engine
engine = create_async_engine(
    "sqlite+aiosqlite:///./rag_ai_app.db",
    echo=False,
    pool_pre_ping=True
)

# Session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

### Connection Management

- **Connection Pooling**: Efficient connection reuse
- **Auto-reconnect**: Handles connection drops
- **Transaction Management**: ACID compliance
- **Performance Optimization**: Query optimization and indexing

---

## 📄 db_models.py

**Purpose**: SQLAlchemy database models  
**Location**: `/src/utils/db_models.py`  
**Type**: Database Models

### Overview

Defines SQLAlchemy ORM models for all database tables with relationships, constraints, and indexes.

### Key Models

#### Session

**Chat session model**

```python
class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
```

#### Message

**Chat message model**

```python
class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.session_id"))
    role = Column(String(20))  # "user" or "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String(50))
    processing_time = Column(Float)
    sources = Column(JSON)

    # Relationships
    session = relationship("Session", back_populates="messages")
```

#### File

**Uploaded file model**

```python
class File(Base):
    __tablename__ = "files"

    file_id = Column(String, primary_key=True)
    filename = Column(String(255))
    file_size = Column(Integer)
    file_type = Column(String(50))
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(20))  # "pending", "processed", "failed"
    chunk_count = Column(Integer)
    error_message = Column(Text)
```

#### UsageLog

**API usage tracking model**

```python
class UsageLog(Base):
    __tablename__ = "usage_logs"

    log_id = Column(String, primary_key=True)
    api_key_index = Column(Integer)
    model = Column(String(50))
    success = Column(Boolean)
    response_time = Column(Float)
    token_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)
```

### Indexes and Constraints

```python
# Performance indexes
Index('idx_session_created', Session.created_at.desc())
Index('idx_message_session', Message.session_id, Message.timestamp)
Index('idx_usage_timestamp', UsageLog.timestamp.desc())
Index('idx_file_status', File.processing_status)
```

---

## 📄 gemini_api_manager.py

**Purpose**: Google Gemini API key management and rotation  
**Location**: `/src/utils/gemini_api_manager.py`  
**Type**: API Management Utility

### Overview

Sophisticated API key management system with random selection, quota tracking, and intelligent fallback mechanisms for Google Gemini APIs.

### Key Classes

#### ApiKeyStatus

**Tracks individual API key status**

```python
@dataclass
class ApiKeyStatus:
    index: int
    key: str
    last_used: float = 0.0
    quota_exhausted_at: Optional[float] = None
    consecutive_failures: int = 0
    is_available: bool = True
```

**Methods**:

- `is_quota_exhausted()`: Check if key is in cooldown
- `mark_quota_exhausted()`: Set 1-minute cooldown
- `mark_success()`: Reset failure counters
- `mark_failure()`: Track consecutive failures

#### GeminiApiManager

**Main API key management class**

### Core Methods

#### get_api_key_with_fallback()

**Purpose**: Get available API key with intelligent fallback

```python
async def get_api_key_with_fallback() -> Tuple[int, bool]
```

**Features**:

- Random selection from available keys
- Quota exhaustion awareness
- Automatic fallback to recovery keys
- Wait for quota recovery if needed

#### select_random_api_key()

**Purpose**: Choose random available API key

```python
def select_random_api_key() -> Optional[int]
```

**Selection Logic**:

- Exclude quota-exhausted keys
- Weight by time since last use
- Prefer less recently used keys
- Random selection for load balancing

#### mark_api_result()

**Purpose**: Update API key status after use

```python
def mark_api_result(
    self,
    api_index: int,
    success: bool,
    is_quota_error: bool = False
) -> None
```

**Status Updates**:

- Success: Reset failure counters
- Quota Error: Set 1-minute cooldown
- General Error: Increment failure count
- Auto-disable after 3 consecutive failures

### Quota Management

- **1-Minute Recovery**: Automatic quota reset tracking
- **Intelligent Waiting**: Wait for earliest recovery time
- **Fallback Chains**: Multiple backup strategies
- **Load Distribution**: Even usage across keys

### Performance Features

- **Async Lock**: Thread-safe operations
- **Weighted Selection**: Performance-based key selection
- **Status Caching**: Efficient status checks
- **Recovery Prediction**: Estimate next available time

---

## 📄 meta_llm.py

**Purpose**: Meta AI integration utility  
**Location**: `/src/utils/meta_llm.py`  
**Type**: AI Integration Utility

### Overview

Provides interface to Meta AI API with error handling, response formatting, and integration with the RAG system.

### Key Classes

#### MetaLLM

**Meta AI integration class**

### Core Methods

#### prompt_simple()

**Purpose**: Send simple prompt to Meta AI

```python
def prompt_simple(self, message: str) -> Dict[str, Any]
```

**Features**:

- Direct Meta AI API calls
- Response formatting
- Error handling and recovery
- Debug mode support

#### prompt_with_context()

**Purpose**: Send context-aware prompt

```python
def prompt_with_context(
    self,
    message: str,
    context: List[str]
) -> Dict[str, Any]
```

**Features**:

- Context injection
- Response enhancement
- Source tracking

### Integration Features

- **Error Recovery**: Graceful failure handling
- **Response Formatting**: Consistent output structure
- **Debug Support**: Detailed logging for troubleshooting
- **Rate Limiting**: Built-in request throttling

---

## 📄 meta_rag_processor_fixed.py

**Purpose**: Enhanced MetaRAG processing with HTTP 422 fixes  
**Location**: `/src/utils/meta_rag_processor_fixed.py`  
**Type**: Advanced RAG Processor

### Overview

Advanced RAG processor that combines Meta AI with document retrieval, featuring comprehensive error handling, HTTP 422 prevention, and performance optimization.

### Key Classes

#### MetaRAGProcessorFixed

**Enhanced MetaRAG processor**

### Core Methods

#### process_query()

**Purpose**: Process complete RAG query

```python
async def process_query(
    self,
    query: str,
    retriever
) -> Tuple[str, List[Document]]
```

**Pipeline**:

1. Input validation and sanitization
2. Document retrieval from vector store
3. Local relevance filtering
4. Comprehensive answer generation
5. Source citation and formatting

#### \_sanitize_prompt()

**Purpose**: Prevent HTTP 422 errors

```python
def _sanitize_prompt(self, prompt: str) -> str
```

**Sanitization**:

- Remove script tags and dangerous content
- Limit prompt length (3000 chars)
- Remove control characters
- Normalize whitespace

#### \_rate_limited_api_call()

**Purpose**: Make rate-limited Meta AI calls

```python
async def _rate_limited_api_call(
    self,
    prompt: str,
    max_retries: int = None
) -> Dict[str, Any]
```

**Features**:

- 3-second minimum delay between calls
- Exponential backoff on failures
- HTTP 422 specific error handling
- Rate limit detection and waiting

### Error Prevention

- **HTTP 422 Prevention**: Input sanitization and validation
- **Rate Limiting**: Automatic delay management
- **Retry Logic**: Smart retry with backoff
- **Fallback Responses**: Graceful degradation

### Performance Optimization

- **Local Filtering**: Reduce API calls with keyword matching
- **Content Limiting**: Manage context length
- **Async Processing**: Non-blocking operations
- **Connection Pooling**: Efficient API usage

---

## 📄 api_exhaustion_handler.py

**Purpose**: API quota exhaustion handling  
**Location**: `/src/utils/api_exhaustion_handler.py`  
**Type**: Error Handling Utility

### Overview

Specialized utility for handling API quota exhaustion scenarios with graceful fallbacks and user-friendly messages.

### Core Functions

#### handle_api_exhaustion()

**Purpose**: Generate fallback response for quota exhaustion

```python
async def handle_api_exhaustion(
    query: str,
    available_docs: List[Document] = None
) -> str
```

**Features**:

- Informative error messages
- Document-based fallback responses
- Recovery time estimation
- User guidance for resolution

#### get_recovery_time_message()

**Purpose**: Estimate API recovery time

```python
def get_recovery_time_message() -> str
```

**Features**:

- Time-based recovery estimates
- User-friendly formatting
- Next available time prediction

---

## 📄 session_manager.py

**Purpose**: Session state management utility  
**Location**: `/src/utils/session_manager.py`  
**Type**: State Management Utility

### Overview

Utility for managing session state, context, and metadata outside of the database layer.

### Key Classes

#### SessionManager

**In-memory session management**

### Core Methods

#### get_session_context()

**Purpose**: Retrieve session conversation context

```python
def get_session_context(self, session_id: str) -> List[Dict]
```

#### update_session_state()

**Purpose**: Update session state information

```python
def update_session_state(
    self,
    session_id: str,
    state: Dict[str, Any]
) -> None
```

### Features

- **Context Caching**: Fast access to recent messages
- **State Management**: Track conversation flow
- **Memory Optimization**: Limit context size
- **Performance**: Reduce database queries

---

## 📄 **init**.py

**Purpose**: Utils package initialization  
**Location**: `/src/utils/__init__.py`  
**Type**: Package Initializer

### Overview

Makes utils directory a Python package and provides convenient imports for commonly used utilities.

### Common Imports

```python
from .config import api_keys, DEFAULT_MODEL, TEMPERATURE
from .database import init_db, get_db_session
from .gemini_api_manager import gemini_manager
from .meta_llm import MetaLLM
```

---

## 🔧 Utility Coordination

### Cross-Utility Integration

- **Configuration**: Central config management
- **Database**: Unified data access layer
- **API Management**: Intelligent quota handling
- **Error Handling**: Comprehensive error recovery
- **Performance**: Optimized resource usage

### Key Benefits

- **Modularity**: Clean separation of concerns
- **Reusability**: Utilities used across services
- **Maintainability**: Centralized functionality
- **Performance**: Optimized implementations
- **Reliability**: Robust error handling

These utilities provide the essential infrastructure that enables the RAG AI application to operate reliably, efficiently, and with comprehensive error handling across all components.
