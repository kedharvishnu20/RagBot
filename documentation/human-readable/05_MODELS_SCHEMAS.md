# Models and Schemas Documentation

## 📁 /src/models/

**Purpose**: Data models and schema definitions  
**Location**: `/src/models/`  
**Type**: Data Layer

### Overview

Contains Pydantic models for request/response validation and SQLAlchemy models for database operations. Ensures type safety and data validation throughout the application.

---

## 📄 schemas.py

**Purpose**: Pydantic models for API request/response validation  
**Location**: `/src/models/schemas.py`  
**Type**: Data Schema Definitions

### Overview

Defines all Pydantic models used for API request validation, response serialization, and internal data structures. Provides automatic validation, serialization, and documentation.

### Chat-Related Models

#### ChatRequest

**Purpose**: Validates incoming chat requests

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    model: str = Field(default="gemini-1.5-flash")
    use_rag: bool = Field(default=True)
    api_key_index: Optional[int] = Field(default=None, ge=0)
    session_id: Optional[str] = Field(default=None)
```

**Fields**:

- `message`: User's input message (1-5000 characters)
- `model`: AI model to use (gemini-1.5-flash, gemini-1.5-pro, meta-ai)
- `use_rag`: Whether to use document retrieval
- `api_key_index`: Specific API key index (optional, auto-selected if None)
- `session_id`: Target session ID (creates new if None)

#### ChatResponse

**Purpose**: Structures chat API responses

```python
class ChatResponse(BaseModel):
    response: str
    model_used: str
    processing_time: float
    session_id: str
    message_sources: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
```

**Fields**:

- `response`: AI-generated response text
- `model_used`: Actual model that generated the response
- `processing_time`: Request processing duration in seconds
- `session_id`: Session ID for conversation context
- `message_sources`: List of source documents with citations
- `error`: Error message if processing failed
- `metadata`: Additional processing information

### Session-Related Models

#### SessionCreateRequest

**Purpose**: Validates session creation requests

```python
class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
```

**Fields**:

- `title`: Optional session title
- `metadata`: Additional session data

#### SessionUpdateRequest

**Purpose**: Validates session update requests

```python
class SessionUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
```

**Fields**:

- `title`: New session title
- `metadata`: Updated session metadata

#### SessionResponse

**Purpose**: Structures session API responses

```python
class SessionResponse(BaseModel):
    session_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(default=0)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        from_attributes = True
```

**Fields**:

- `session_id`: Unique session identifier
- `title`: Human-readable session title
- `created_at`: Session creation timestamp
- `updated_at`: Last modification timestamp
- `message_count`: Number of messages in session
- `metadata`: Additional session information

### Message-Related Models

#### MessageResponse

**Purpose**: Structures message API responses

```python
class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        from_attributes = True
```

**Fields**:

- `message_id`: Unique message identifier
- `session_id`: Parent session ID
- `role`: Message sender ("user" or "assistant")
- `content`: Message text content
- `timestamp`: Message creation time
- `model_used`: AI model used for assistant messages
- `processing_time`: Response generation time
- `sources`: Source documents for assistant responses

### File-Related Models

#### FileUploadResponse

**Purpose**: Structures file upload responses

```python
class FileUploadResponse(BaseModel):
    files_processed: List[Dict[str, Any]]
    total_files: int
    successful_uploads: int
    failed_uploads: int
    processing_time: float
    errors: List[str] = Field(default_factory=list)
```

**Fields**:

- `files_processed`: Details of each file processed
- `total_files`: Total number of files submitted
- `successful_uploads`: Number of successfully processed files
- `failed_uploads`: Number of failed uploads
- `processing_time`: Total processing duration
- `errors`: List of error messages for failed uploads

#### FileInfo

**Purpose**: Represents file metadata

```python
class FileInfo(BaseModel):
    file_id: str
    filename: str
    file_size: int
    file_type: str
    upload_timestamp: datetime
    processing_status: str  # "pending", "processed", "failed"
    chunk_count: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
```

**Fields**:

- `file_id`: Unique file identifier
- `filename`: Original filename
- `file_size`: File size in bytes
- `file_type`: MIME type or extension
- `upload_timestamp`: Upload time
- `processing_status`: Current processing state
- `chunk_count`: Number of text chunks extracted
- `error_message`: Error details if processing failed

### System-Related Models

#### HealthResponse

**Purpose**: System health check response

```python
class HealthResponse(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    version: str
    components: Dict[str, str] = Field(default_factory=dict)
```

**Fields**:

- `status`: Overall system health
- `timestamp`: Check timestamp
- `version`: Application version
- `components`: Individual component statuses

#### SystemStatus

**Purpose**: Detailed system status information

```python
class SystemStatus(BaseModel):
    database: Dict[str, Any]
    vector_store: Dict[str, Any]
    api_keys: Dict[str, Any]
    models: Dict[str, Any]
    performance: Dict[str, Any]
```

**Fields**:

- `database`: Database connection and stats
- `vector_store`: Vector database status
- `api_keys`: API key availability and usage
- `models`: AI model status and performance
- `performance`: System performance metrics

### Configuration Models

#### ModelConfig

**Purpose**: AI model configuration

```python
class ModelConfig(BaseModel):
    name: str
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8192, ge=1, le=32768)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=0.0, le=2.0)
```

**Fields**:

- `name`: Model identifier
- `temperature`: Response randomness (0.0-2.0)
- `max_tokens`: Maximum response length
- `top_p`: Nucleus sampling parameter
- `frequency_penalty`: Repetition penalty

### Validation Features

#### Field Validation

- **String Length**: Min/max character limits
- **Numeric Ranges**: Value bounds for numbers
- **Required Fields**: Mandatory vs optional fields
- **Format Validation**: Email, URL, datetime formats

#### Custom Validators

```python
@validator('message')
def validate_message(cls, v):
    if not v.strip():
        raise ValueError('Message cannot be empty')
    return v.strip()

@validator('api_key_index')
def validate_api_key_index(cls, v):
    if v is not None and v < 0:
        raise ValueError('API key index must be non-negative')
    return v
```

#### Configuration

```python
class Config:
    from_attributes = True  # Enable ORM mode
    json_encoders = {
        datetime: lambda v: v.isoformat()
    }
    schema_extra = {
        "example": {
            "message": "What is machine learning?",
            "model": "gemini-1.5-flash",
            "use_rag": True
        }
    }
```

---

## 📄 **init**.py

**Purpose**: Package initialization for models  
**Location**: `/src/models/__init__.py`  
**Type**: Package Initializer

### Overview

Makes the models directory a Python package and provides convenient imports.

### Exports

```python
from .schemas import (
    ChatRequest,
    ChatResponse,
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    MessageResponse,
    FileUploadResponse,
    FileInfo,
    HealthResponse,
    SystemStatus
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "SessionCreateRequest",
    "SessionUpdateRequest",
    "SessionResponse",
    "MessageResponse",
    "FileUploadResponse",
    "FileInfo",
    "HealthResponse",
    "SystemStatus"
]
```

### Benefits of Schema-Driven Development

#### Type Safety

- Compile-time type checking
- IDE autocompletion
- Runtime validation

#### API Documentation

- Automatic OpenAPI schema generation
- Interactive documentation (Swagger UI)
- Clear API contracts

#### Data Validation

- Input sanitization
- Format validation
- Error messages for invalid data

#### Serialization

- Automatic JSON conversion
- Consistent response formats
- Database ORM integration

This comprehensive schema system ensures data integrity, provides clear API contracts, and enables automatic documentation generation while maintaining type safety throughout the application.
