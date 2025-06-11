# Services Documentation

## 📁 /src/services/

**Purpose**: Business logic and service layer  
**Location**: `/src/services/`  
**Type**: Business Logic Layer

### Overview

Contains the core business logic of the application, implementing services for AI processing, session management, file handling, and orchestration. Each service encapsulates specific functionality with clean interfaces.

---

## 📄 ai_service.py

**Purpose**: AI model integration and response generation  
**Location**: `/src/services/ai_service.py`  
**Type**: AI Service

### Overview

Central service for all AI model interactions, including Gemini and Meta AI integration with comprehensive error handling, quota management, and response optimization.

### Key Classes

#### AIService

**Main service class for AI operations**

### Core Methods

#### generate_gemini_response()

**Purpose**: Generate responses using Gemini models

```python
async def generate_gemini_response(
    self,
    message: str,
    model: str,
    api_key_index: int = 0
) -> str
```

**Features**:

- Random API key selection for quota management
- Automatic fallback on quota exhaustion
- Retry logic with exponential backoff
- Error categorization (quota, timeout, general)
- Success/failure tracking for API keys

**Error Handling**:

- `ResourceExhausted`: Automatic API key rotation
- `Timeout`: Graceful timeout with user-friendly message
- `General Errors`: Comprehensive error logging and fallback

#### generate_meta_response()

**Purpose**: Generate responses using Meta AI

```python
async def generate_meta_response(self, message: str) -> str
```

**Features**:

- MetaLLM integration with debug capabilities
- Simple prompt interface
- Error handling and fallback responses

#### generate_rag_response()

**Purpose**: Generate document-augmented responses

```python
async def generate_rag_response(
    self,
    message: str,
    model: str,
    api_key_index: int = 0
) -> Tuple[str, List[Document]]
```

**Features**:

- Document retrieval from vector store
- Context-aware response generation
- Source document tracking
- Multi-model support (Gemini, Meta)
- Fallback mechanisms for API failures

### API Key Management Integration

- **GeminiApiManager**: Automated key rotation and quota tracking
- **Quota Monitoring**: 1-minute recovery tracking
- **Load Balancing**: Random selection with usage weighting
- **Fallback Logic**: Graceful degradation on exhaustion

### Model Support

- **gemini-1.5-flash**: Fast responses, optimized for speed
- **gemini-1.5-pro**: High-quality responses, more detailed
- **Meta AI**: Alternative AI provider with RAG capabilities

### Performance Features

- Async/await throughout
- Connection pooling
- Response caching (planned)
- Timeout protection (30 seconds)

---

## 📄 chat_orchestrator.py

**Purpose**: Orchestrates chat flow and AI model coordination  
**Location**: `/src/services/chat_orchestrator.py`  
**Type**: Orchestration Service

### Overview

High-level service that coordinates between different AI services, manages chat sessions, and provides unified interface for chat operations.

### Key Classes

#### ChatOrchestrator

**Main orchestration class**

### Core Methods

#### process_chat_message()

**Purpose**: Process complete chat interaction

```python
async def process_chat_message(
    self,
    message: str,
    model: str,
    use_rag: bool,
    session_id: Optional[str] = None,
    api_key_index: Optional[int] = None
) -> Dict[str, Any]
```

**Features**:

- Session management integration
- Model selection and routing
- RAG vs direct response routing
- Source citation handling
- Performance timing
- Error recovery

#### route_to_ai_service()

**Purpose**: Route requests to appropriate AI service

```python
async def route_to_ai_service(
    self,
    message: str,
    model: str,
    use_rag: bool,
    api_key_index: Optional[int] = None
) -> Tuple[str, List[Document]]
```

**Routing Logic**:

- **Gemini + RAG**: `ai_service.generate_rag_response()`
- **Gemini Direct**: `ai_service.generate_gemini_response()`
- **Meta + RAG**: Enhanced MetaRAG processing
- **Meta Direct**: `ai_service.generate_meta_response()`

### Session Integration

- Automatic session creation
- Message history management
- Context preservation
- Session metadata updates

### Error Orchestration

- Service-level error handling
- Graceful fallback between models
- User-friendly error messages
- Performance monitoring

---

## 📄 session_service.py

**Purpose**: Session lifecycle management  
**Location**: `/src/services/session_service.py`  
**Type**: Data Service

### Overview

Manages chat sessions including creation, retrieval, updates, and deletion. Handles session metadata and message history.

### Key Classes

#### SessionService

**Main session management service**

### Core Methods

#### create_session()

**Purpose**: Create new chat session

```python
async def create_session(
    self,
    title: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]
```

**Features**:

- UUID generation for session IDs
- Default title generation
- Metadata storage
- Database persistence

#### get_session()

**Purpose**: Retrieve session details

```python
async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]
```

**Returns**:

- Session metadata
- Message count
- Creation/update timestamps
- Custom metadata

#### list_sessions()

**Purpose**: Get all sessions for user

```python
async def list_sessions(self) -> List[Dict[str, Any]]
```

**Features**:

- Ordered by creation date (newest first)
- Includes message counts
- Metadata summaries

#### update_session()

**Purpose**: Update session information

```python
async def update_session(
    self,
    session_id: str,
    title: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]
```

**Updates**:

- Session title/name
- Custom metadata
- Last updated timestamp

#### delete_session()

**Purpose**: Remove session and all messages

```python
async def delete_session(self, session_id: str) -> bool
```

**Actions**:

- Delete session record
- Remove all associated messages
- Clean up metadata
- Return success status

#### add_message()

**Purpose**: Add message to session

```python
async def add_message(
    self,
    session_id: str,
    role: str,
    content: str,
    model_used: Optional[str] = None,
    processing_time: Optional[float] = None,
    sources: Optional[List[Dict]] = None
) -> str
```

**Features**:

- Message ID generation
- Role validation (user/assistant)
- Source document storage
- Performance metadata

#### get_session_messages()

**Purpose**: Retrieve message history

```python
async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]
```

**Returns**:

- Chronological message order
- Full message details
- Source citations
- Performance metrics

#### rename_session()

**Purpose**: Update session title

```python
async def rename_session(self, session_id: str, new_title: str) -> bool
```

### Database Integration

- SQLAlchemy ORM models
- Async database operations
- Transaction management
- Error handling

---

## 📄 file_service.py

**Purpose**: File upload and document processing  
**Location**: `/src/services/file_service.py`  
**Type**: File Processing Service

### Overview

Handles file uploads, text extraction, and document processing for the RAG system. Supports multiple file formats with comprehensive error handling.

### Key Classes

#### FileService

**Main file processing service**

### Core Methods

#### process_uploaded_files()

**Purpose**: Process multiple uploaded files

```python
async def process_uploaded_files(
    self,
    files: List[UploadFile]
) -> Dict[str, Any]
```

**Pipeline**:

1. File validation (size, format)
2. Text extraction
3. Content chunking
4. Vector embedding generation
5. FAISS index updates
6. Database metadata storage

#### extract_text_from_file()

**Purpose**: Extract text content from various formats

```python
async def extract_text_from_file(
    self,
    file_content: bytes,
    filename: str
) -> str
```

**Supported Formats**:

- **PDF**: PyMuPDF with OCR fallback
- **TXT**: Direct reading with encoding detection
- **DOCX**: Python-docx structured extraction

#### chunk_text()

**Purpose**: Split text into manageable chunks

```python
def chunk_text(
    self,
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]
```

**Features**:

- Configurable chunk size
- Overlap for context preservation
- Sentence boundary respect
- Paragraph preservation

#### update_vector_store()

**Purpose**: Add new documents to vector database

```python
async def update_vector_store(
    self,
    texts: List[str],
    metadatas: List[Dict]
) -> bool
```

**Operations**:

- Generate embeddings
- Update FAISS index
- Store metadata
- Index optimization

### File Validation

- Size limits (configurable)
- Format validation
- Content scanning
- Security checks

### Error Handling

- Unsupported format graceful handling
- Corrupted file detection
- Encoding issues resolution
- Processing timeout protection

---

## 📄 vector_service.py

**Purpose**: Vector database operations and similarity search  
**Location**: `/src/services/vector_service.py`  
**Type**: Vector Database Service

### Overview

Manages the FAISS vector store for document embeddings, similarity search, and retrieval operations essential for RAG functionality.

### Key Classes

#### VectorService

**Main vector database service**

### Core Methods

#### initialize_vector_store()

**Purpose**: Set up FAISS vector database

```python
async def initialize_vector_store(self) -> bool
```

**Operations**:

- Create FAISS index
- Initialize embeddings model
- Set up metadata storage
- Configure similarity search

#### add_documents()

**Purpose**: Add new documents to vector store

```python
async def add_documents(
    self,
    texts: List[str],
    metadatas: List[Dict]
) -> bool
```

**Process**:

- Generate embeddings
- Add to FAISS index
- Store metadata
- Update index files

#### similarity_search()

**Purpose**: Find similar documents for query

```python
async def similarity_search(
    self,
    query: str,
    k: int = 5,
    score_threshold: float = 0.7
) -> List[Document]
```

**Features**:

- Configurable result count
- Score-based filtering
- Metadata preservation
- Distance calculations

#### get_retriever()

**Purpose**: Get retriever for specific API key

```python
def get_retriever(self, api_key_index: int = 0)
```

**Features**:

- API-key-specific retrievers
- Configurable search parameters
- Performance optimization

### Embedding Models

- **Google Embeddings**: Primary embedding model
- **Multiple API Keys**: Load balancing for embedding generation
- **Fallback Models**: Backup embedding providers

### Performance Optimization

- Index caching
- Batch processing
- Memory management
- Incremental updates

---

## 📄 usage_service.py

**Purpose**: Usage tracking and analytics  
**Location**: `/src/services/usage_service.py`  
**Type**: Analytics Service

### Overview

Tracks API usage, performance metrics, and system analytics for monitoring and optimization.

### Key Classes

#### UsageService

**Main usage tracking service**

### Core Methods

#### log_api_usage()

**Purpose**: Record API usage statistics

```python
async def log_api_usage(
    self,
    api_key_index: int,
    model: str,
    success: bool,
    response_time: float,
    token_count: Optional[int] = None
) -> None
```

#### get_usage_stats()

**Purpose**: Retrieve usage analytics

```python
async def get_usage_stats(
    self,
    time_range: str = "24h"
) -> Dict[str, Any]
```

#### track_session_metrics()

**Purpose**: Monitor session performance

```python
async def track_session_metrics(
    self,
    session_id: str,
    metrics: Dict[str, Any]
) -> None
```

### Analytics Features

- API call frequency
- Response time tracking
- Error rate monitoring
- Token usage analysis
- Model performance comparison

---

## 📄 **init**.py

**Purpose**: Services package initialization  
**Location**: `/src/services/__init__.py`  
**Type**: Package Initializer

### Overview

Makes services directory a Python package and provides convenient imports.

### Service Coordination

All services work together to provide:

- **Unified Interface**: Clean API for business logic
- **Error Handling**: Consistent error management
- **Performance**: Optimized async operations
- **Scalability**: Modular, extensible design
- **Maintainability**: Clear separation of concerns

This service layer provides the core business logic with proper abstraction, error handling, and performance optimization for the entire RAG AI application.
