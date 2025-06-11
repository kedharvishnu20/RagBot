# API Reference and Usage Examples

## Overview

This document provides comprehensive API reference and practical usage examples for all endpoints in the RAG AI Application. Each endpoint includes request/response schemas, authentication requirements, and real-world examples.

## Base Configuration

```
Base URL: http://localhost:8000
Content-Type: application/json
Session Management: Cookie-based sessions
```

## Session Management API

### Create New Session

**Endpoint**: `POST /api/sessions/new`

**Description**: Creates a new chat session with optional custom name.

**Request Body**:

```json
{
  "session_name": "My Study Session" // Optional
}
```

**Response**:

```json
{
  "session_id": "uuid-string",
  "session_name": "My Study Session",
  "created_at": "2024-01-01T10:00:00Z",
  "message": "Session created successfully"
}
```

**Usage Example**:

```javascript
// JavaScript fetch example
const response = await fetch("/api/sessions/new", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    session_name: "Computer Science Study",
  }),
});
const data = await response.json();
console.log(data.session_id);
```

### Get Session History

**Endpoint**: `GET /api/sessions/history`

**Description**: Retrieves all sessions for the current user.

**Response**:

```json
{
  "sessions": [
    {
      "session_id": "uuid-1",
      "session_name": "Math Study",
      "created_at": "2024-01-01T10:00:00Z",
      "message_count": 15,
      "last_activity": "2024-01-01T11:30:00Z"
    }
  ],
  "total_sessions": 1
}
```

### Switch Session

**Endpoint**: `POST /api/sessions/switch`

**Request Body**:

```json
{
  "session_id": "uuid-string"
}
```

**Response**:

```json
{
  "message": "Session switched successfully",
  "session_id": "uuid-string",
  "session_name": "Math Study"
}
```

## Chat API

### Send Message

**Endpoint**: `POST /api/chat/message`

**Description**: Sends a message to the AI assistant and receives a response with sources.

**Request Body**:

```json
{
  "message": "What is lattice theory in computer science?",
  "stream": false // Optional: enable streaming response
}
```

**Response**:

```json
{
  "response": "Lattice theory is a branch of mathematics that studies lattices...",
  "sources": [
    {
      "filename": "Unit 5 (lattice theory) mfcs.pdf",
      "chunk_text": "A lattice is a partially ordered set...",
      "relevance_score": 0.95,
      "page_number": 3
    }
  ],
  "session_id": "uuid-string",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

**Streaming Response**:

```javascript
// Enable streaming for real-time response
const response = await fetch("/api/chat/message", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "Explain neural networks",
    stream: true,
  }),
});

// Handle streaming response
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const data = JSON.parse(line.slice(6));
      console.log(data.content); // Stream content
    }
  }
}
```

### Get Chat History

**Endpoint**: `GET /api/chat/history`

**Query Parameters**:

- `session_id`: Session ID (optional, uses current session if not provided)
- `limit`: Number of messages to retrieve (default: 50)
- `offset`: Pagination offset (default: 0)

**Response**:

```json
{
    "messages": [
        {
            "id": 1,
            "message": "What is machine learning?",
            "response": "Machine learning is a subset of AI...",
            "timestamp": "2024-01-01T10:00:00Z",
            "sources": [...]
        }
    ],
    "total_messages": 1,
    "session_info": {
        "session_id": "uuid-string",
        "session_name": "AI Study Session"
    }
}
```

### Clear Chat History

**Endpoint**: `DELETE /api/chat/history`

**Request Body**:

```json
{
  "session_id": "uuid-string" // Optional
}
```

**Response**:

```json
{
  "message": "Chat history cleared successfully",
  "cleared_messages": 5
}
```

## File Management API

### Upload File

**Endpoint**: `POST /api/files/upload`

**Description**: Uploads and processes documents for the knowledge base.

**Request**: Multipart form data

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("description", "Computer Science textbook"); // Optional

const response = await fetch("/api/files/upload", {
  method: "POST",
  body: formData,
});
```

**Response**:

```json
{
  "message": "File uploaded and processed successfully",
  "file_id": "uuid-string",
  "filename": "textbook.pdf",
  "file_size": 2048576,
  "pages_processed": 150,
  "chunks_created": 75,
  "processing_time": 12.5
}
```

### Get Uploaded Files

**Endpoint**: `GET /api/files/list`

**Query Parameters**:

- `session_id`: Filter by session (optional)
- `limit`: Number of files (default: 20)
- `offset`: Pagination offset (default: 0)

**Response**:

```json
{
  "files": [
    {
      "file_id": "uuid-string",
      "filename": "textbook.pdf",
      "upload_date": "2024-01-01T10:00:00Z",
      "file_size": 2048576,
      "status": "processed",
      "chunks_count": 75,
      "description": "Computer Science textbook"
    }
  ],
  "total_files": 1
}
```

### Delete File

**Endpoint**: `DELETE /api/files/{file_id}`

**Response**:

```json
{
  "message": "File deleted successfully",
  "file_id": "uuid-string",
  "filename": "textbook.pdf"
}
```

### File Processing Status

**Endpoint**: `GET /api/files/{file_id}/status`

**Response**:

```json
{
  "file_id": "uuid-string",
  "filename": "textbook.pdf",
  "status": "processing", // "uploading", "processing", "completed", "error"
  "progress": 65, // Percentage complete
  "estimated_time": 30, // Seconds remaining
  "error_message": null
}
```

## System Information API

### Health Check

**Endpoint**: `GET /api/system/health`

**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "uptime": 3600,
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "vector_store": "healthy",
    "ai_service": "available"
  }
}
```

### System Statistics

**Endpoint**: `GET /api/system/stats`

**Response**:

```json
{
  "total_sessions": 25,
  "total_messages": 150,
  "total_files": 12,
  "total_chunks": 2500,
  "disk_usage": {
    "total_gb": 100,
    "used_gb": 15.7,
    "available_gb": 84.3
  },
  "performance": {
    "avg_response_time": 1.2,
    "queries_per_minute": 45,
    "error_rate": 0.02
  }
}
```

### API Usage Statistics

**Endpoint**: `GET /api/system/usage`

**Query Parameters**:

- `period`: "day", "week", "month" (default: "day")
- `session_id`: Filter by session (optional)

**Response**:

```json
{
  "period": "day",
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T23:59:59Z"
  },
  "usage": {
    "total_requests": 120,
    "total_tokens": 15000,
    "unique_sessions": 8,
    "peak_hour": "14:00-15:00",
    "most_active_endpoint": "/api/chat/message"
  },
  "breakdown": {
    "chat_messages": 80,
    "file_uploads": 5,
    "session_operations": 35
  }
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "Human-readable error message",
  "details": {
    "field": "message",
    "reason": "Message cannot be empty"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "request_id": "uuid-string"
}
```

### Common Error Codes

#### Authentication Errors

- `AUTH_REQUIRED` (401): Authentication required
- `SESSION_EXPIRED` (401): Session has expired
- `INVALID_SESSION` (403): Invalid session ID

#### Validation Errors

- `VALIDATION_ERROR` (400): Request validation failed
- `MISSING_REQUIRED_FIELD` (400): Required field missing
- `INVALID_FILE_TYPE` (400): Unsupported file format

#### Resource Errors

- `FILE_NOT_FOUND` (404): Requested file not found
- `SESSION_NOT_FOUND` (404): Session not found
- `RESOURCE_LIMIT_EXCEEDED` (429): Rate limit exceeded

#### Server Errors

- `AI_SERVICE_UNAVAILABLE` (503): AI service temporarily unavailable
- `PROCESSING_ERROR` (500): File processing failed
- `DATABASE_ERROR` (500): Database operation failed

## Rate Limiting

### Default Limits

- Chat messages: 60 per minute per session
- File uploads: 10 per hour per session
- API calls: 1000 per hour per IP

### Rate Limit Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## Authentication Examples

### Cookie-based Session (Web Interface)

```javascript
// Automatic cookie handling
fetch("/api/chat/message", {
  method: "POST",
  credentials: "include", // Include cookies
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "Hello",
  }),
});
```

### Session Management

```javascript
// Create session and store ID
const createSession = async () => {
  const response = await fetch("/api/sessions/new", {
    method: "POST",
    credentials: "include",
  });
  const data = await response.json();
  localStorage.setItem("sessionId", data.session_id);
  return data.session_id;
};

// Use stored session ID
const sessionId = localStorage.getItem("sessionId");
```

## WebSocket Integration (if available)

### Connection

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat");

ws.onopen = () => {
  console.log("Connected to chat WebSocket");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
};
```

### Real-time Chat

```javascript
// Send message via WebSocket
const sendMessage = (message) => {
  ws.send(
    JSON.stringify({
      type: "chat_message",
      message: message,
      session_id: sessionId,
    })
  );
};

// Handle responses
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "chat_response":
      displayMessage(data.response, data.sources);
      break;
    case "processing_status":
      updateProcessingIndicator(data.status);
      break;
    case "error":
      displayError(data.message);
      break;
  }
};
```

## SDKs and Client Libraries

### Python SDK Example

```python
import requests
import json

class RAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def create_session(self, name=None):
        response = self.session.post(
            f"{self.base_url}/api/sessions/new",
            json={"session_name": name} if name else {}
        )
        return response.json()

    def send_message(self, message):
        response = self.session.post(
            f"{self.base_url}/api/chat/message",
            json={"message": message}
        )
        return response.json()

    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/api/files/upload",
                files=files
            )
        return response.json()

# Usage
client = RAGClient()
session = client.create_session("Study Session")
response = client.send_message("What is machine learning?")
print(response['response'])
```

### JavaScript SDK Example

```javascript
class RAGClient {
  constructor(baseUrl = "http://localhost:8000") {
    this.baseUrl = baseUrl;
  }

  async createSession(name) {
    const response = await fetch(`${this.baseUrl}/api/sessions/new`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_name: name }),
      credentials: "include",
    });
    return response.json();
  }

  async sendMessage(message) {
    const response = await fetch(`${this.baseUrl}/api/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      credentials: "include",
    });
    return response.json();
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseUrl}/api/files/upload`, {
      method: "POST",
      body: formData,
      credentials: "include",
    });
    return response.json();
  }
}

// Usage
const client = new RAGClient();
const session = await client.createSession("Study Session");
const response = await client.sendMessage("Explain neural networks");
console.log(response.response);
```
