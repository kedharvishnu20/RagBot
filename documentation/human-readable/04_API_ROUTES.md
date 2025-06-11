# API Routes Documentation

## 📁 /src/api/

**Purpose**: FastAPI route handlers and endpoint definitions  
**Location**: `/src/api/`  
**Type**: API Layer

### Overview

Contains all FastAPI route definitions organized by functionality. Each file handles specific API endpoints with proper request/response models and error handling.

---

## 📄 session_routes.py

**Purpose**: Session management endpoints  
**Location**: `/src/api/session_routes.py`  
**Type**: API Route Handler

### Overview

Handles all session-related operations including creation, retrieval, updating, and deletion of chat sessions.

### Endpoints

#### POST /sessions/

**Purpose**: Create a new chat session

```python
@router.post("/", response_model=SessionResponse)
async def create_session(request: Optional[Dict] = Body(default={}))
```

- **Input**: Optional session metadata
- **Output**: Session ID and metadata
- **HTTP Status**: 200 (success), 422 (validation error)

#### GET /sessions/

**Purpose**: List all sessions

```python
@router.get("/", response_model=List[SessionResponse])
async def list_sessions()
```

- **Output**: Array of all sessions
- **Ordering**: Most recent first

#### GET /sessions/{session_id}

**Purpose**: Get specific session details

```python
@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str)
```

- **Input**: Session ID path parameter
- **Output**: Session details and metadata
- **Error**: 404 if session not found

#### PUT /sessions/{session_id}

**Purpose**: Update session (e.g., rename)

```python
@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, request: SessionUpdateRequest)
```

- **Input**: Session ID and update data
- **Output**: Updated session details

#### DELETE /sessions/{session_id}

**Purpose**: Delete a session and its messages

```python
@router.delete("/{session_id}")
async def delete_session(session_id: str)
```

- **Input**: Session ID path parameter
- **Output**: Deletion confirmation

#### GET /sessions/{session_id}/messages

**Purpose**: Get session message history

```python
@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str)
```

- **Output**: Array of messages in chronological order

#### GET /sessions/{session_id}/sources

**Purpose**: Get sources for session messages

```python
@router.get("/{session_id}/sources")
async def get_session_sources(session_id: str)
```

- **Output**: Source documents and citations

### Dependencies

- `SessionService`: Business logic for session operations
- `SessionCreateRequest`, `SessionUpdateRequest`: Request models
- `SessionResponse`, `MessageResponse`: Response models

---

## 📄 chat_routes.py

**Purpose**: Chat and AI response endpoints  
**Location**: `/src/api/chat_routes.py`  
**Type**: API Route Handler

### Overview

Handles chat interactions, AI model responses, and message processing with timeout protection and error handling.

### Endpoints

#### POST /chat

**Purpose**: Send message and get AI response

```python
@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest)
```

- **Input**: Message, model selection, API key index, session ID
- **Output**: AI response with sources and metadata
- **Timeout**: 30 seconds with graceful fallback
- **Models Supported**: Gemini (RAG/direct), Meta AI (RAG/direct)

### Request Model

```python
class ChatRequest(BaseModel):
    message: str
    model: str = "gemini-1.5-flash"
    use_rag: bool = True
    api_key_index: Optional[int] = None
    session_id: Optional[str] = None
```

### Response Model

```python
class ChatResponse(BaseModel):
    response: str
    model_used: str
    processing_time: float
    session_id: str
    message_sources: List[Dict]
    error: Optional[str] = None
```

### AI Models Integration

- **Gemini RAG**: Document-based responses with citations
- **Gemini Direct**: Direct AI responses without RAG
- **Meta RAG**: Enhanced RAG with Meta AI reasoning
- **Meta Direct**: Direct Meta AI responses

### Error Handling

- API quota exhaustion with fallback
- Timeout protection (30 seconds)
- Model switching on failures
- Graceful degradation

### Performance Features

- Async processing throughout
- Multiple API key rotation
- Connection pooling
- Response caching

---

## 📄 file_routes.py

**Purpose**: File upload and management endpoints  
**Location**: `/src/api/file_routes.py`  
**Type**: API Route Handler

### Overview

Handles document upload, processing, and vectorization for the RAG system.

### Endpoints

#### POST /files/upload

**Purpose**: Upload and process documents

```python
@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...))
```

- **Input**: Multiple file uploads
- **Supported**: PDF, TXT, DOCX
- **Max Size**: 10MB per file
- **Processing**: Text extraction and vectorization
- **Response**: `{"files": [UploadResponse, ...]}`

#### GET /files/uploaded

**Purpose**: List uploaded files

```python
@router.get("/uploaded")
async def list_uploaded_files()
```

- **Output**: `{"files": [filename1, filename2, ...]}`

#### GET /files/content-preview/{filename}

**Purpose**: Get file content preview with pagination

```python
@router.get("/content-preview/{filename}")
async def get_file_content_preview(filename: str, page: int = 1, fast: bool = False)
```

- **Input**: Filename, optional page number, fast mode flag
- **Output**: Preview data with text content, page info, conversion status
- **Features**: Automatic DOCX-to-PDF conversion for seamless viewing

#### GET /files/preview/{filename}

**Purpose**: Get basic file information for preview modal

```python
@router.get("/preview/{filename}")
async def get_file_preview_info(filename: str)
```

- **Output**: File metadata, type information, preview capabilities

#### GET /files/view/{filename}

**Purpose**: Serve file for direct viewing or download

```python
@router.get("/view/{filename}")
async def view_file(filename: str, download: bool = False)
```

- **Features**:
  - Automatic DOCX-to-PDF conversion for seamless viewing
  - Inline PDF display in browser
  - Optional download with `?download=true`
  - Transparent conversion (users see PDF even for DOCX files)

#### DELETE /files/delete/{filename}

**Purpose**: Delete uploaded file

```python
@router.delete("/delete/{filename}")
async def delete_file(filename: str)
```

- **Input**: Filename
- **Action**: Removes file and associated vectors

#### DELETE /files/clear_uploads

**Purpose**: Clear all uploaded files

```python
@router.delete("/clear_uploads")
async def clear_uploads()
```

- **Action**: Removes all files from study_docs directory

### File Processing Pipeline

1. **Upload Validation**: Check format and size
2. **Text Extraction**: Extract content based on file type
3. **Document Conversion**: Automatic DOCX-to-PDF conversion for seamless viewing
4. **Text Chunking**: Split into manageable segments
5. **Embedding Generation**: Create vector embeddings
6. **Vector Storage**: Store in FAISS index
7. **Metadata Storage**: Save file info to database

### Document Preview Features

- **Seamless DOCX Viewing**: Automatic conversion to PDF for consistent viewing experience
- **Real-time Preview**: Tabbed interface with text extract and document preview
- **Page Navigation**: Support for multi-page PDF documents
- **Caching**: Converted PDFs are cached for improved performance
- **Multiple Conversion Methods**: Fallback options for reliable conversion

### Supported Formats

- **PDF**: Direct viewing with pypdf text extraction
- **TXT**: Direct text reading with encoding detection
- **DOCX**: Automatic conversion to PDF using docx2pdf, python-docx, or LibreOffice
- **DOC**: Legacy Word document support with conversion

### Error Handling

- File size validation
- Format validation
- Encoding detection and handling
- Processing failure recovery

---

## 📄 system_routes.py

**Purpose**: System status and monitoring endpoints  
**Location**: `/src/api/system_routes.py`  
**Type**: API Route Handler

### Overview

Provides system health checks, status monitoring, and diagnostic information.

### Endpoints

#### GET /health

**Purpose**: Basic health check

```python
@router.get("/health")
async def health_check()
```

- **Output**: System status and timestamp
- **Usage**: Load balancer health checks

#### GET /status

**Purpose**: Detailed system status

```python
@router.get("/status")
async def system_status()
```

- **Output**:
  - Database connection status
  - Vector store status
  - API key availability
  - Model status
  - File system status

#### GET /metrics

**Purpose**: Performance metrics

```python
@router.get("/metrics")
async def get_metrics()
```

- **Output**:
  - Response times
  - API usage statistics
  - Error rates
  - Session statistics

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2025-06-08T...",
  "version": "2.2.0",
  "database": "connected",
  "vector_store": "ready",
  "api_keys": "available"
}
```

---

## 📄 **init**.py

**Purpose**: Python package initialization  
**Location**: `/src/api/__init__.py`  
**Type**: Package Initializer

### Overview

Empty file that marks the `api` directory as a Python package, enabling imports from other modules.

### Usage

Allows imports like:

```python
from src.api.chat_routes import router as chat_router
```

---

## 🔧 Common Features Across All Route Files

### Error Handling

- Standardized HTTP status codes
- Detailed error messages
- Logging for debugging
- Graceful fallback mechanisms

### Request Validation

- Pydantic model validation
- Input sanitization
- Type checking
- Required field validation

### Response Formatting

- Consistent JSON structure
- Proper HTTP headers
- CORS support
- Compression for large responses

### Security Features

- Input validation and sanitization
- Rate limiting (planned)
- Authentication hooks (ready for implementation)
- SQL injection prevention

### Performance Optimizations

- Async/await throughout
- Database connection pooling
- Response caching where appropriate
- Efficient query patterns

This API layer provides a clean, RESTful interface for all application functionality with comprehensive error handling and performance optimizations.
