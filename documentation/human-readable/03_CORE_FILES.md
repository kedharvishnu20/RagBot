# Core Application Files Documentation

## 📄 serializable_server.py

**Purpose**: Main FastAPI server entry point with JSON serialization fixes  
**Location**: `/serializable_server.py`  
**Type**: Main Server File

### Overview

The primary server file that initializes and runs the FastAPI application. This file ensures all responses are properly JSON serializable and handles the core application routing.

### Key Features

- **FastAPI Application**: Creates the main app instance with CORS middleware
- **Static File Serving**: Mounts static files from `src/static/`
- **Database Initialization**: Automatically initializes SQLite database on startup
- **Router Integration**: Includes all API route modules
- **Error Handling**: Comprehensive exception handling with JSON responses
- **Timeout Protection**: 30-second timeout wrapper for API calls

### Dependencies

```python
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
```

### Configuration

- **Title**: "RAG AI Application - Serializable"
- **Version**: "2.2.0"
- **Default Port**: 8001
- **CORS**: Enabled for all origins
- **Timeout**: 30 seconds for chat endpoints

### Routes Included

- Session management (`/sessions/`)
- Chat functionality (`/chat`)
- File operations (`/files/`)
- System status (`/health`, `/status`)

### Error Handling

- HTTP 422 validation errors resolved
- API exhaustion graceful fallback
- Timeout protection for hanging requests
- Comprehensive logging and debugging

### Usage

```bash
python serializable_server.py
# Server starts on http://localhost:8001
```

---

## 📄 requirements.txt

**Purpose**: Python package dependencies  
**Location**: `/requirements.txt`  
**Type**: Configuration File

### Overview

Contains all Python packages required for the application to run. Includes specific versions for stability and compatibility.

### Key Dependencies

- **FastAPI**: Web framework (`fastapi>=0.104.1`)
- **LangChain**: AI/ML framework (`langchain>=0.1.0`)
- **Google AI**: Gemini integration (`google-generativeai>=0.3.0`)
- **FAISS**: Vector database (`faiss-cpu>=1.7.4`)
- **SQLAlchemy**: Database ORM (`sqlalchemy>=2.0.0`)
- **Uvicorn**: ASGI server (`uvicorn>=0.24.0`)

### Document Processing

- **PyMuPDF**: PDF processing (`PyMuPDF>=1.23.0`)
- **python-docx**: Word document handling
- **chardet**: Character encoding detection

### AI and ML

- **transformers**: Hugging Face models
- **sentence-transformers**: Text embeddings
- **torch**: PyTorch backend

### Web and HTTP

- **requests**: HTTP client library
- **aiohttp**: Async HTTP client
- **websockets**: WebSocket support

### Installation

```bash
pip install -r requirements.txt
```

---

## 📄 .env.example

**Purpose**: Environment variables template  
**Location**: `/.env.example`  
**Type**: Configuration Template

### Overview

Template file showing required environment variables. Users copy this to `.env` and fill in their actual values.

### Required Variables

```env
# Google Gemini API Keys (multiple for quota management)
GOOGLE_API_KEY_0=your_primary_gemini_api_key_here
GOOGLE_API_KEY_1=your_secondary_gemini_api_key_here
GOOGLE_API_KEY_2=your_tertiary_gemini_api_key_here

# Application Configuration
APP_PORT=8001
APP_HOST=0.0.0.0
DEBUG_MODE=false

# AI Model Settings
DEFAULT_MODEL=gemini-1.5-flash
TEMPERATURE=0.1
MAX_TOKENS=8192

# Database
DATABASE_URL=sqlite:///./rag_ai_app.db

# File Upload
MAX_FILE_SIZE=10MB
ALLOWED_EXTENSIONS=pdf,txt,docx
```

### Security Notes

- Never commit actual `.env` file to version control
- Use strong, unique API keys
- Rotate keys regularly for security
- Keep backup of working configuration

---

## 📄 .gitignore

**Purpose**: Git version control ignore rules  
**Location**: `/.gitignore`  
**Type**: Version Control Configuration

### Overview

Specifies which files and directories Git should ignore to prevent sensitive data and temporary files from being committed.

### Key Exclusions

- **Environment**: `.env` files with API keys
- **Python Cache**: `__pycache__/`, `*.pyc` files
- **Database**: `*.db`, `*.db-*` files
- **Vector Store**: `vector_store/` directory
- **Logs**: `*.log` files
- **Temporary**: `tmp/`, `.DS_Store`, `Thumbs.db`

### Content Example

```gitignore
# Environment variables
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class

# Database files
*.db
*.db-shm
*.db-wal

# Vector store
vector_store/

# Logs
*.log
logs/

# OS generated
.DS_Store
Thumbs.db
```

---

## 📄 README.md

**Purpose**: Basic project information  
**Location**: `/README.md`  
**Type**: Documentation

### Overview

Provides essential project information, quick start instructions, and basic usage guidelines for developers and users.

### Contents

- Project description and features
- Quick installation steps
- Basic usage examples
- Key technologies used
- Links to detailed documentation

### Target Audience

- New developers joining the project
- Users wanting quick setup instructions
- Contributors understanding project scope

---

## 📄 Database Files

### rag_ai_app.db

**Purpose**: Main SQLite database  
**Type**: Binary Database File

Contains all application data:

- **sessions**: Chat session records
- **messages**: Chat message history
- **files**: Uploaded file metadata
- **usage_logs**: API usage tracking

### rag_ai_app.db-shm, rag_ai_app.db-wal

**Purpose**: SQLite shared memory and write-ahead log files  
**Type**: Binary Database Support Files

Support files for SQLite WAL mode operation:

- Better concurrent access
- Improved performance
- Crash recovery support

---

## 📁 Key Directories

### /src/

Main source code directory containing all application logic

### /documentation/

Comprehensive documentation for humans and AI agents

### /study_docs/

Sample documents for testing and demonstration

### /vector_store/

FAISS vector database files for document embeddings

This documentation covers all the core application files in the root directory. Each file serves a specific purpose in the overall application architecture.
