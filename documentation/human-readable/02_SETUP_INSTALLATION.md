# Setup and Installation Guide

## 🛠️ Prerequisites

- **Python**: 3.10 or higher (recommended: 3.10+)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended for large documents)
- **Storage**: At least 2GB free space (more for document conversion cache)
- **Internet Connection**: Required for AI model access and package installation

## 📦 Quick Installation

### 1. Environment Setup

```bash
# Navigate to project directory
cd "c:\MY SPACE\MY LAPTOP\project works\my projects\rag\rag-ai-app"

# Create virtual environment (if not exists)
python -m venv ragi

# Activate virtual environment
# Windows:
ragi\Scripts\activate
# Linux/Mac:
source ragi/bin/activate
```

### 2. Install Dependencies

```bash
# Install all required packages (including new document conversion dependencies)
pip install -r requirements.txt
```

**New Dependencies in v2.1.0:**

- `python-docx>=1.1.0` - Word document processing
- `docx2pdf>=0.1.8` - Primary DOCX to PDF conversion
- `reportlab>=4.0.0` - Fallback PDF generation

### 3. Environment Configuration

Create a `.env` file based on `.env.example`:

```env
# Google Gemini API Keys (add multiple for quota management)
GOOGLE_API_KEY_0=your_primary_gemini_api_key
GOOGLE_API_KEY_1=your_secondary_gemini_api_key
GOOGLE_API_KEY_2=your_tertiary_gemini_api_key
# Add more as needed: GOOGLE_API_KEY_3, GOOGLE_API_KEY_4, etc.

# Meta AI Configuration (optional)
META_AI_SESSION=your_meta_session_token

# Application Configuration
APP_PORT=8000
APP_HOST=0.0.0.0
DEBUG_MODE=false

# Model Configuration
DEFAULT_MODEL=gemini-1.5-flash
TEMPERATURE=0.1
MAX_TOKENS=8192

# Database Configuration
DATABASE_URL=sqlite:///./rag_app.db

# File Upload Settings
MAX_FILE_SIZE=10MB
ALLOWED_EXTENSIONS=pdf,txt,docx,doc

# Vector Store Configuration
VECTOR_STORE_PATH=./vector_store
EMBEDDING_MODEL=textembedding-gecko@003

# Document Conversion Settings
CONVERTED_PDF_DIR=converted_pdfs
CONVERSION_CACHE=true
```

### 4. Document Conversion Setup

The application supports multiple DOCX-to-PDF conversion methods:

#### Primary Method: docx2pdf

- Included in requirements.txt
- Works well on Windows
- Automatic fallback if fails

#### Fallback Method: python-docx + reportlab

- Included in requirements.txt
- Cross-platform compatibility
- Manual PDF generation

#### Optional: LibreOffice

For enhanced conversion capabilities:

```bash
# Windows: Download from libreoffice.org
# Ubuntu/Debian:
sudo apt-get install libreoffice
# macOS:
brew install --cask libreoffice
```

### 5. Directory Structure Creation

The application will automatically create these directories:

```
rag-ai-app/
├── study_docs/           # Document uploads
├── converted_pdfs/       # PDF conversion cache
├── vector_store/         # FAISS embeddings
│   ├── index.faiss      # Vector index
│   └── index.pkl        # Metadata
└── rag_app.db           # SQLite database
```

## 🚀 Starting the Application

### Development Mode

```bash
# Activate environment
ragi\Scripts\activate

# Start the server
python serializable_server.py

# Server will start on http://localhost:8000
```

### Production Mode

```bash
# Use uvicorn for production
uvicorn serializable_server:app --host 0.0.0.0 --port 8000 --workers 1
```

## 🧪 Testing the Setup

### 1. Health Check

Visit `http://localhost:8001/health` - should return:

```json
{
  "status": "healthy",
  "timestamp": "2025-06-08T...",
  "version": "1.0.0"
}
```

### 2. Upload Test Document

1. Navigate to `http://localhost:8001`
2. Click "Upload Files"
3. Select a PDF/TXT/DOCX file
4. Wait for processing completion

### 3. Test Chat Functionality

1. Type a question related to your uploaded document
2. Select an AI model (Gemini recommended)
3. Click "Send" and verify response
4. Check that sources are displayed correctly

## 🔧 Configuration Options

### API Key Management

- **Multiple Keys**: Add multiple Gemini API keys for quota management
- **Automatic Rotation**: System automatically rotates between available keys
- **Quota Tracking**: 1-minute cooldown for exhausted keys

### Model Selection

- **gemini-1.5-flash**: Fast responses, good for general queries
- **gemini-1.5-pro**: Higher quality responses, slower
- **Meta AI**: Alternative AI provider (requires meta-ai-api package)

### Performance Tuning

- **TEMPERATURE**: Lower values (0.1) for factual responses
- **MAX_TOKENS**: Adjust based on desired response length
- **VECTOR_STORE**: Larger stores improve retrieval accuracy

## 🐛 Troubleshooting

### Common Issues

**1. API Key Errors**

```
Error: Invalid API key
```

- Check `.env` file format
- Verify API keys are valid and active
- Ensure proper key rotation setup

**2. Port Already in Use**

```
Error: Port 8001 is already in use
```

- Change APP_PORT in `.env`
- Kill existing processes: `netstat -ano | findstr :8001`

**3. File Upload Failures**

```
Error: File processing failed
```

- Check file size limits (MAX_FILE_SIZE)
- Verify file format is supported
- Ensure sufficient disk space

**4. Vector Store Issues**

```
Error: FAISS index not found
```

- Delete `vector_store/` directory
- Restart application to regenerate
- Re-upload documents

### Performance Issues

**1. Slow Responses**

- Reduce document count in vector store
- Use gemini-1.5-flash instead of pro model
- Increase API key count for better rotation

**2. Memory Usage**

- Monitor vector store size
- Clear old sessions periodically
- Restart application if memory leaks occur

## 📊 Monitoring

### Log Files

Application logs are output to console. For production, redirect to files:

```bash
python serializable_server.py > app.log 2>&1
```

### Database Monitoring

```sql
-- Check session count
SELECT COUNT(*) FROM sessions;

-- Check API usage
SELECT api_key_index, COUNT(*) FROM usage_logs
GROUP BY api_key_index;

-- Monitor file uploads
SELECT filename, upload_timestamp FROM files
ORDER BY upload_timestamp DESC;
```

### Performance Metrics

- Response time per query
- API key rotation frequency
- Vector store size and performance
- Session duration and message count

## 🔄 Updates and Maintenance

### Regular Tasks

1. **API Key Rotation**: Monitor quota usage and add keys as needed
2. **Database Cleanup**: Remove old sessions and logs periodically
3. **Vector Store Optimization**: Rebuild index for better performance
4. **Log Management**: Archive or rotate log files

### Backup Procedures

1. **Database**: Copy `rag_ai_app.db` regularly
2. **Vector Store**: Backup `vector_store/` directory
3. **Configuration**: Keep `.env` file secure and backed up
4. **Documents**: Backup `study_docs/` if important

This setup guide ensures a smooth installation and optimal configuration for the RAG AI Application.
