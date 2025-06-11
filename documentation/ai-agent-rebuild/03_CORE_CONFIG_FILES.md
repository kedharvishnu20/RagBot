# Core Configuration Files - Exact Implementation

## Overview

This document contains the exact implementation for all core configuration and utility files required to reconstruct the RAG AI Application.

---

## File 1: src/utils/config.py

### Purpose

Central configuration management with environment variables and API keys.

### Complete File Content

```python
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

class AppConfig:
    """Application configuration"""
    def __init__(self):
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "vector_store")
        self.study_docs_folder = os.getenv("STUDY_DOCS_FOLDER", "study_docs")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.4"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2048"))
        self.default_model = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
        self.max_content_length = 500

class ApiKeys:
    """API keys configuration"""
    def __init__(self):
        main_key = os.getenv("GOOGLE_API_KEY")
        if main_key:
            self.google_api_keys = [main_key]
        else:
            self.google_api_keys = []

        for i in range(1, 11):
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if key:
                self.google_api_keys.append(key)

        self.meta_fb_email = os.getenv("META_FB_EMAIL")
        self.meta_fb_password = os.getenv("META_FB_PASSWORD")

    def get_all_keys(self) -> List[str]:
        """Get all available Google API keys"""
        return [key for key in self.google_api_keys if key and key.strip()]

config = AppConfig()
api_keys = ApiKeys()

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-preview-04-17",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

AI_MODES = ["RAG", "Gemini", "Meta", "MetaRAG"]

def get_api_key(index: int = 0) -> str:
    """Get a Google API key by index with fallback"""
    valid_keys = [k for k in api_keys.google_api_keys if k]
    if not valid_keys:
        raise ValueError("No valid Google API keys found")

    return valid_keys[index % len(valid_keys)]
```

---

## File 2: src/utils/database.py

### Purpose

Database initialization and connection management using SQLAlchemy.

### Complete File Content

```python
import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager

# Database configuration
DATABASE_URL = "sqlite:///chat_database.db"
Base = declarative_base()

# Create engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database with required tables"""
    try:
        # Create tables using SQLAlchemy
        from .db_models import Session, Message, FileUpload, Source
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Fallback to raw SQL
        init_db_raw()

def init_db_raw():
    """Initialize database with raw SQL as fallback"""
    try:
        conn = sqlite3.connect('chat_database.db')
        cursor = conn.cursor()

        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        # Create file_uploads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'uploaded',
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        # Create sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.0,
                page_number INTEGER DEFAULT 0,
                FOREIGN KEY (message_id) REFERENCES messages (id)
            )
        ''')

        # Create usage_stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Database initialized with raw SQL")
    except Exception as e:
        print(f"Raw SQL database initialization error: {e}")

@contextmanager
def get_db():
    """Get database session with context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_connection():
    """Get raw SQLite connection"""
    return sqlite3.connect('chat_database.db')

def execute_query(query: str, params: tuple = None):
    """Execute a query and return results"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
    except Exception as e:
        print(f"Query execution error: {e}")
        return None
```

---

## File 3: src/utils/db_models.py

### Purpose

SQLAlchemy ORM models for database tables.

### Complete File Content

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Session(Base):
    """Session model for chat sessions"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    file_uploads = relationship("FileUpload", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    """Message model for chat messages"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="messages")
    sources = relationship("Source", back_populates="message", cascade="all, delete-orphan")

class FileUpload(Base):
    """File upload model"""
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer, default=0)
    status = Column(String, default="uploaded")

    # Relationships
    session = relationship("Session", back_populates="file_uploads")

class Source(Base):
    """Source model for message sources"""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.0)
    page_number = Column(Integer, default=0)

    # Relationships
    message = relationship("Message", back_populates="sources")

class UsageStats(Base):
    """Usage statistics model"""
    __tablename__ = "usage_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(String, nullable=False)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, default=datetime.utcnow)
```

---

## File 4: src/utils/**init**.py

### Purpose

Package initialization for utils module.

### Complete File Content

```python
"""
Utility modules for RAG AI Application

This package contains:
- config: Configuration management
- database: Database operations
- db_models: SQLAlchemy models
- gemini_api_manager: Google API management
- meta_llm: Meta AI integration
- meta_rag_processor_fixed: RAG processing
- api_exhaustion_handler: Rate limiting
- session_manager: Session management
"""

from .config import config, api_keys, get_api_key, GEMINI_MODELS, AI_MODES
from .database import init_db, get_db, get_db_connection, execute_query

__all__ = [
    'config',
    'api_keys',
    'get_api_key',
    'GEMINI_MODELS',
    'AI_MODES',
    'init_db',
    'get_db',
    'get_db_connection',
    'execute_query'
]
```

---

## File 5: src/models/**init**.py

### Purpose

Package initialization for models module.

### Complete File Content

```python
"""
Data models and schemas for RAG AI Application

This package contains:
- schemas: Pydantic models for API requests/responses
"""

from .schemas import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionResponse,
    MessageResponse,
    FileUploadResponse,
    SourceResponse,
    UsageStatsResponse,
    HealthCheckResponse,
    ErrorResponse
)

__all__ = [
    'ChatRequest',
    'ChatResponse',
    'SessionCreate',
    'SessionResponse',
    'MessageResponse',
    'FileUploadResponse',
    'SourceResponse',
    'UsageStatsResponse',
    'HealthCheckResponse',
    'ErrorResponse'
]
```

---

## File 6: src/services/**init**.py

### Purpose

Package initialization for services module.

### Complete File Content

```python
"""
Business logic services for RAG AI Application

This package contains:
- ai_service: AI model integration
- chat_orchestrator: Chat request coordination
- session_service: Session management
- file_service: File processing
- vector_service: Vector store operations
- usage_service: Usage tracking
"""

# Import service classes for easy access
try:
    from .ai_service import AIService
    from .chat_orchestrator import ChatOrchestrator
    from .session_service import SessionService
    from .file_service import FileService
    from .vector_service import VectorStoreService
    from .usage_service import UsageService, get_usage_service

    __all__ = [
        'AIService',
        'ChatOrchestrator',
        'SessionService',
        'FileService',
        'VectorStoreService',
        'UsageService',
        'get_usage_service'
    ]
except ImportError as e:
    print(f"Warning: Could not import all services: {e}")
    __all__ = []
```

---

## File 7: src/api/**init**.py

### Purpose

Package initialization for API routes module.

### Complete File Content

```python
"""
API route handlers for RAG AI Application

This package contains:
- session_routes: Session management endpoints
- chat_routes: Chat functionality endpoints
- file_routes: File upload/management endpoints
- system_routes: System information endpoints
"""

# Import routers for easy access
try:
    from .session_routes import router as session_router
    from .chat_routes import router as chat_router
    from .file_routes import router as file_router
    from .system_routes import router as system_router

    __all__ = [
        'session_router',
        'chat_router',
        'file_router',
        'system_router'
    ]
except ImportError as e:
    print(f"Warning: Could not import all routers: {e}")
    __all__ = []
```

---

## File 8: src/**init**.py

### Purpose

Package initialization for main src module.

### Complete File Content

```python
"""
RAG AI Application - Source Code Package

This package contains the complete implementation of the RAG AI Application
including API routes, business logic services, data models, and utilities.

Structure:
- api/: FastAPI route handlers
- models/: Pydantic schemas and data models
- services/: Business logic and core functionality
- utils/: Utility functions and configuration
- static/: Frontend assets (HTML, CSS, JS)
"""

__version__ = "2.2.0"
__title__ = "RAG AI Application"
__description__ = "Document-based question answering using Google Gemini AI"
__author__ = "RAG AI Team"

# Make sure the package can be imported
__all__ = ['api', 'models', 'services', 'utils']
```

---

## Installation Instructions

### Step 1: Create Directory Structure

```bash
mkdir -p src/utils src/models src/services src/api
```

### Step 2: Create **init**.py Files

```bash
touch src/__init__.py
touch src/utils/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/api/__init__.py
```

### Step 3: Create Configuration Files

Create each file above with the exact content provided.

### Step 4: Test Configuration

```python
# Test imports
python -c "from src.utils.config import config; print(config.study_docs_folder)"
python -c "from src.utils.database import init_db; init_db()"
```

## Validation Steps

1. **Import Test**:

   ```python
   import src.utils.config
   import src.utils.database
   import src.utils.db_models
   ```

2. **Database Test**:

   ```python
   from src.utils.database import init_db
   init_db()
   ```

3. **Configuration Test**:
   ```python
   from src.utils.config import config, api_keys
   print(f"Vector DB Path: {config.vector_db_path}")
   print(f"Study Docs: {config.study_docs_folder}")
   ```

## Environment Variables Required

Create `.env` file with:

```env
GOOGLE_API_KEY=your_google_api_key_here
VECTOR_DB_PATH=vector_store
STUDY_DOCS_FOLDER=study_docs
CHUNK_SIZE=800
CHUNK_OVERLAP=200
TEMPERATURE=0.4
MAX_TOKENS=2048
DEFAULT_MODEL=gemini-1.5-flash
```

## Common Issues

1. **Import Errors**: Ensure all `__init__.py` files exist
2. **Database Errors**: Check SQLite permissions
3. **Configuration Errors**: Verify `.env` file exists
4. **Module Not Found**: Check Python path and working directory

This completes the core configuration and utility files needed for the RAG AI Application.
