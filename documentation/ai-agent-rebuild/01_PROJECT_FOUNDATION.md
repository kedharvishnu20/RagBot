# AI Agent Project Reconstruction Guide

## Purpose

This documentation enables an AI agent to completely reconstruct the RAG AI Application from scratch. It contains exact file contents, directory structure, and step-by-step rebuild instructions.

## Project Overview

- **Name**: RAG AI Application
- **Type**: Python FastAPI web application with vector search
- **Architecture**: Client-server with SQLite database and FAISS vector store
- **Primary Function**: Document-based question answering using Google's Gemini AI

## Prerequisites for Reconstruction

```bash
# Required software
Python 3.8+
pip (Python package manager)
Git (for version control)

# Required API keys
GOOGLE_API_KEY (for Gemini AI services)

# Operating system compatibility
Windows, macOS, Linux
```

## Directory Structure to Create

```
rag-ai-app/
├── serializable_server.py          # Main FastAPI server
├── requirements.txt                 # Python dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore file
├── README.md                       # Project readme
├── chat_database.db               # SQLite database (created at runtime)
├── study_docs/                    # Document storage directory
│   ├── imp questions mid1.pdf
│   ├── test_document.txt
│   └── Unit 5 (lattice theory) mfcs.pdf
├── vector_store/                  # Vector embeddings storage
│   ├── index.faiss               # FAISS vector index
│   └── index.pkl                 # Metadata mappings
├── src/                          # Source code directory
│   ├── __init__.py
│   ├── api/                      # API route handlers
│   │   ├── __init__.py
│   │   ├── session_routes.py     # Session management
│   │   ├── chat_routes.py        # Chat functionality
│   │   ├── file_routes.py        # File operations
│   │   └── system_routes.py      # System information
│   ├── models/                   # Data models and schemas
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic models
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── ai_service.py         # AI integration
│   │   ├── chat_orchestrator.py  # Chat coordination
│   │   ├── session_service.py    # Session management
│   │   ├── file_service.py       # File processing
│   │   ├── vector_service.py     # Vector operations
│   │   └── usage_service.py      # Usage tracking
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration
│   │   ├── database.py           # Database operations
│   │   ├── db_models.py          # SQLAlchemy models
│   │   ├── gemini_api_manager.py # Gemini API handling
│   │   ├── meta_llm.py           # LLM abstraction
│   │   ├── meta_rag_processor_fixed.py # RAG processing
│   │   ├── api_exhaustion_handler.py # Rate limiting
│   │   └── session_manager.py    # Session handling
│   └── static/                   # Frontend assets
│       ├── index.html            # Main HTML page
│       ├── css/                  # Stylesheets
│       │   ├── styles.css        # Main styles
│       │   └── components.css    # Component styles
│       └── js/                   # JavaScript modules
│           ├── main.js           # Main application
│           ├── api.js            # API communication
│           ├── chat.js           # Chat interface
│           ├── fileUpload.js     # File handling
│           └── sessionManager.js # Session management
└── documentation/                # Documentation (this directory)
    ├── human-readable/           # Human documentation
    └── ai-agent-rebuild/         # AI reconstruction guides
```

## Step 1: Environment Setup

### Create Project Directory

```bash
mkdir rag-ai-app
cd rag-ai-app
```

### Initialize Git Repository

```bash
git init
```

### Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

## Step 2: Create Root Configuration Files

### requirements.txt

Create file with exact content:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.1
sqlalchemy==2.0.23
sqlite3
python-multipart==0.0.6
aiofiles==23.2.1
python-dotenv==1.0.0
google-generativeai==0.3.2
faiss-cpu==1.7.4
numpy==1.24.3
PyPDF2==3.0.1
python-docx==1.1.0
jinja2==3.1.2
starlette==0.27.0
```

### .env.example

Create file with exact content:

```env
# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=sqlite:///./chat_database.db

# Vector Store Configuration
VECTOR_STORE_PATH=./vector_store
EMBEDDING_MODEL=text-embedding-004

# AI Model Configuration
GEMINI_MODEL=gemini-1.5-flash
MAX_TOKENS=8192
TEMPERATURE=0.7

# File Upload Configuration
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=.pdf,.txt,.doc,.docx

# Rate Limiting
API_RATE_LIMIT=60
REQUESTS_PER_MINUTE=30

# Session Configuration
SESSION_TIMEOUT=3600
MAX_SESSIONS_PER_USER=5

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### .gitignore

Create file with exact content:

```gitignore
# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# Project specific
chat_database.db
vector_store/
study_docs/*.pdf
*.log
temp/
uploads/
```

### README.md

Create file with exact content:

````markdown
# RAG AI Application

A Retrieval-Augmented Generation (RAG) application that allows users to upload documents and ask questions about their content using Google's Gemini AI.

## Features

- Document upload and processing (PDF, TXT, DOC, DOCX)
- Vector similarity search using FAISS
- AI-powered question answering with source attribution
- Session management for multiple users
- Web-based interface with real-time chat
- Usage tracking and analytics

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
````

2. Set up environment:

   ```bash
   cp .env.example .env
   # Edit .env with your Google API key
   ```

3. Run the server:

   ```bash
   python serializable_server.py
   ```

4. Open browser to `http://localhost:8000`

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Architecture

- **Backend**: FastAPI with SQLite database
- **Vector Store**: FAISS for similarity search
- **AI Service**: Google Gemini for text generation
- **Frontend**: Vanilla JavaScript with modern UI

## License

MIT License

````

## Step 3: Create Directory Structure

```bash
# Create main directories
mkdir -p src/api
mkdir -p src/models
mkdir -p src/services
mkdir -p src/utils
mkdir -p src/static/css
mkdir -p src/static/js
mkdir -p study_docs
mkdir -p vector_store
mkdir -p documentation/human-readable
mkdir -p documentation/ai-agent-rebuild

# Create __init__.py files
touch src/__init__.py
touch src/api/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/utils/__init__.py
````

## Validation Commands

After creating the structure, validate with:

```bash
# Check directory structure
find . -type d | sort

# Check Python syntax
python -m py_compile src/**/*.py

# Check imports
python -c "import src.api.session_routes"

# Test server startup
python serializable_server.py --help
```

## Next Steps

1. **Implement Core Files**: Follow the detailed file creation guides in subsequent documents
2. **Install Dependencies**: Run `pip install -r requirements.txt`
3. **Configure Environment**: Set up `.env` file with API keys
4. **Initialize Database**: Run database initialization scripts
5. **Test Application**: Verify all components work together

## Troubleshooting Reconstruction

### Common Issues

1. **Import Errors**: Ensure all `__init__.py` files are created
2. **Permission Errors**: Check file permissions on created directories
3. **Dependency Issues**: Use exact versions from `requirements.txt`
4. **Path Issues**: Ensure working directory is project root

### Validation Steps

1. Check all files are created with correct names
2. Verify directory structure matches specification
3. Test Python imports work correctly
4. Confirm environment configuration is valid

This document provides the foundation for reconstructing the project. Refer to subsequent documents for exact file contents and implementation details.
