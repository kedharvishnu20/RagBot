# Troubleshooting Guide and FAQ

## Overview

This comprehensive guide provides solutions to common issues, debugging techniques, and frequently asked questions for the RAG AI Application, including new document preview and conversion features.

## Quick Diagnosis Checklist

### System Health Check

1. **Server Status**: Check if the server is running on port 8000
2. **Database Connection**: Verify SQLite database file exists and is accessible
3. **Vector Store**: Confirm FAISS index files are present and valid
4. **API Keys**: Ensure Google API keys are configured correctly
5. **Dependencies**: Verify all required packages including new conversion libraries
6. **Document Conversion**: Check DOCX-to-PDF conversion capabilities
7. **File Permissions**: Ensure write permissions for converted_pdfs directory

### Quick Commands

```bash
# Check server status
curl http://localhost:8000/api/system/health

# Verify database
dir *.db

# Check vector store
dir vector_store\

# Check converted PDFs directory
dir converted_pdfs\

# Test API key
python -c "import os; print('API Key:', os.getenv('GOOGLE_API_KEY_0', 'Not found')[:10] + '...')"

# Test document conversion dependencies
python -c "import docx2pdf, docx, reportlab; print('Conversion dependencies OK')"
```

## New Issues and Solutions (v2.1.0)

### 1. Document Preview Issues

#### Issue: Upload Failed - "result.files is not iterable"

**Error**: `TypeError: result.files is not iterable (cannot read property undefined)`

**Solution**: This was fixed in v2.1.0. Update your API response handling:

```javascript
// Before (broken)
this.uploadedFiles.push(...result.files);

// After (fixed) - API now returns {"files": [...]}
this.uploadedFiles.push(...result.files);
```

**Server Fix**: The API now returns `{"files": [...]}` instead of `[...]`

#### Issue: DOCX to PDF Conversion Fails

**Error**: Various conversion-related errors

**Solutions**:

1. **Check Primary Converter (docx2pdf)**:

   ```bash
   pip install docx2pdf
   python -c "from docx2pdf import convert; print('docx2pdf available')"
   ```

2. **Fallback to python-docx + reportlab**:

   ```bash
   pip install python-docx reportlab
   python -c "from docx import Document; from reportlab.platypus import SimpleDocTemplate; print('Fallback available')"
   ```

3. **Install LibreOffice (optional)**:

   ```bash
   # Windows: Download from libreoffice.org
   # Add to PATH: C:\Program Files\LibreOffice\program\

   # Test LibreOffice availability
   libreoffice --version
   ```

#### Issue: Converted PDFs Not Displaying

**Error**: PDF iframe shows blank or error

**Solutions**:

1. **Check file permissions**:

   ```bash
   # Ensure converted_pdfs directory is writable
   mkdir converted_pdfs
   # Check if PDF files exist
   dir converted_pdfs\
   ```

2. **Browser compatibility**:

   - Use Chrome, Firefox, or Edge (latest versions)
   - Enable PDF viewer in browser settings
   - Check browser console for iframe errors

3. **File serving issues**:
   ```bash
   # Test direct access to converted PDF
   curl -I http://localhost:8000/api/files/view/your_file.docx
   ```

### 2. File Upload and Management Issues

#### Issue: File Upload Returns 500 Error

**Error**: Server error during file upload

**Solutions**:

1. **Check file size limits**:

   ```bash
   # Files must be under 10MB
   # Check actual file size
   dir study_docs\
   ```

2. **Verify file permissions**:

   ```bash
   # Ensure study_docs directory is writable
   mkdir study_docs
   ```

3. **Check supported file types**:
   - Supported: PDF, TXT, DOCX, DOC
   - Case-insensitive extensions

#### Issue: Document Preview Modal Not Opening

**Error**: Modal doesn't appear or shows error

**Solutions**:

1. **Check JavaScript console**:

   - Open Developer Tools (F12)
   - Look for JavaScript errors
   - Check network requests for failed API calls

2. **Verify API endpoints**:

   ```bash
   # Test content preview endpoint
   curl http://localhost:8000/api/files/content-preview/your_file.pdf

   # Test file info endpoint
   curl http://localhost:8000/api/files/preview/your_file.pdf
   ```

## Common Issues and Solutions

### 1. Server Won't Start

#### Issue: Port Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**:

```bash
# Windows: Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Start server on different port
python serializable_server.py --port 8001
```

#### Issue: Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'xyz'`

**Solution**:

```bash
# Install missing dependencies
pip install -r requirements.txt

# For new conversion dependencies specifically
pip install python-docx docx2pdf reportlab

# Verify installation
pip list | findstr docx
pip list | findstr reportlab
```

kill -9 <PID>

# Restart application

````

#### Issue: Corrupted Database

**Error**: Database file corruption errors

**Solution**:

```bash
# Backup current database
cp chat_database.db chat_database.db.backup

# Check database integrity
sqlite3 chat_database.db "PRAGMA integrity_check;"

# If corrupted, recreate database
rm chat_database.db
python -c "from src.utils.database import init_db; init_db()"
````

#### Issue: Migration Problems

**Error**: Table or column doesn't exist

**Solution**:

```python
# Check database schema
import sqlite3
conn = sqlite3.connect('chat_database.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(tables)
```

### 3. Vector Store Issues

#### Issue: Missing Vector Index

**Error**: `FileNotFoundError: index.faiss not found`

**Solution**:

```bash
# Check vector store directory
ls -la vector_store/

# If missing, create empty index
mkdir -p vector_store
python -c "
import faiss
import pickle
index = faiss.IndexFlatIP(768)
faiss.write_index(index, 'vector_store/index.faiss')
with open('vector_store/index.pkl', 'wb') as f:
    pickle.dump({'documents': {}, 'chunks': {}, 'index_mapping': {}}, f)
"
```

#### Issue: Vector Dimension Mismatch

**Error**: Dimension mismatch in vector operations

**Solution**:

```python
# Check current index dimensions
import faiss
index = faiss.read_index('vector_store/index.faiss')
print(f"Index dimension: {index.d}")

# Rebuild index with correct dimensions
# Delete existing files and re-upload documents
```

#### Issue: Corrupted Vector Index

**Error**: Invalid index file or search errors

**Solution**:

```bash
# Backup and rebuild vector store
mv vector_store vector_store_backup
mkdir vector_store

# Re-upload all documents through the web interface
# Or use the rebuild script
python rebuild_vector_store.py
```

### 4. AI Service Issues

#### Issue: Google API Key Problems

**Error**: `401 Unauthorized` or API key errors

**Solution**:

```bash
# Check API key configuration
echo $GOOGLE_API_KEY

# Verify .env file
cat .env | grep GOOGLE_API_KEY

# Test API key
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models
```

#### Issue: API Rate Limiting

**Error**: `429 Too Many Requests`

**Solution**:

```python
# Check rate limiting configuration
# In config.py, adjust:
API_RATE_LIMIT = 60  # requests per minute
API_RETRY_DELAY = 1  # seconds between retries

# Implement exponential backoff
```

#### Issue: Model Not Available

**Error**: Model not found or unavailable

**Solution**:

```python
# Check available models
import google.generativeai as genai
for model in genai.list_models():
    print(model.name)

# Update model name in config
GEMINI_MODEL = "gemini-pro"  # or available model
```

### 5. File Upload Issues

#### Issue: File Size Limit Exceeded

**Error**: `413 Request Entity Too Large`

**Solution**:

```python
# Increase file size limit in serializable_server.py
app.add_middleware(
    CORSMiddleware,
    # ... other settings
)

# Add file size configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Or use nginx/apache for larger files
```

#### Issue: Unsupported File Type

**Error**: File type not supported

**Solution**:

```python
# Check supported file types in file_service.py
SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.doc', '.docx'}

# Add new file type support
def extract_text_from_file(file_path, file_type):
    if file_type == '.pdf':
        return extract_pdf_text(file_path)
    elif file_type == '.txt':
        return extract_txt_text(file_path)
    # Add new type here
```

#### Issue: File Processing Fails

**Error**: Text extraction or processing errors

**Solution**:

```bash
# Check file permissions
ls -la study_docs/

# Verify file integrity
file study_docs/document.pdf

# Test extraction manually
python -c "
from src.services.file_service import FileService
fs = FileService()
text = fs.extract_text('study_docs/document.pdf')
print(len(text))
"
```

### 6. Frontend Issues

#### Issue: JavaScript Errors

**Error**: Console errors in browser

**Solution**:

```javascript
// Check browser console for errors
// Common fixes:
// 1. Clear browser cache
// 2. Check CORS settings
// 3. Verify API endpoints

// Debug API calls
fetch("/api/system/health")
  .then((response) => response.json())
  .then((data) => console.log(data))
  .catch((error) => console.error("Error:", error));
```

#### Issue: Session Not Persisting

**Error**: Lost session on page refresh

**Solution**:

```javascript
// Check cookie settings in browser
// Verify session configuration in backend
// Enable secure cookies if using HTTPS

// Debug session storage
console.log(document.cookie);
console.log(localStorage.getItem("sessionId"));
```

### 7. Performance Issues

#### Issue: Slow Response Times

**Symptoms**: Long delays in chat responses

**Diagnosis**:

```python
# Enable performance logging
import time
import logging

logging.basicConfig(level=logging.DEBUG)

# Time API calls
start_time = time.time()
# ... your operation
end_time = time.time()
print(f"Operation took {end_time - start_time} seconds")
```

**Solutions**:

```python
# 1. Optimize vector search
SEARCH_K = 3  # Reduce number of retrieved chunks

# 2. Implement caching
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_embedding(text):
    return generate_embedding(text)

# 3. Use async operations
import asyncio
async def process_request():
    # Async implementation
```

#### Issue: High Memory Usage

**Symptoms**: Out of memory errors

**Solutions**:

```python
# 1. Batch processing
BATCH_SIZE = 10  # Process files in batches

# 2. Clear cache periodically
import gc
gc.collect()

# 3. Optimize vector storage
# Use compressed index types
index = faiss.IndexIVFPQ(quantizer, d, nlist, m, nbits)
```

## Debugging Techniques

### 1. Enable Debug Logging

```python
# In config.py
LOG_LEVEL = "DEBUG"

# In main application
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. API Testing

```bash
# Test all endpoints
curl -X GET http://localhost:8000/api/system/health
curl -X POST http://localhost:8000/api/sessions/new
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### 3. Database Inspection

```python
# Connect to database and inspect
import sqlite3
conn = sqlite3.connect('chat_database.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

# Check recent messages
cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5;")
print(cursor.fetchall())
```

### 4. Vector Store Debugging

```python
# Check vector store status
import faiss
import pickle

# Load index
index = faiss.read_index('vector_store/index.faiss')
print(f"Index size: {index.ntotal}")
print(f"Dimension: {index.d}")

# Load metadata
with open('vector_store/index.pkl', 'rb') as f:
    metadata = pickle.load(f)
    print(f"Documents: {len(metadata['documents'])}")
    print(f"Chunks: {len(metadata['chunks'])}")
```

## Frequently Asked Questions

### General Questions

**Q: How do I add support for new file types?**
A: Modify the `file_service.py` to include new extraction methods:

```python
def extract_text_from_file(file_path, file_type):
    if file_type == '.pdf':
        return extract_pdf_text(file_path)
    elif file_type == '.docx':
        return extract_docx_text(file_path)
    # Add your new type here
```

**Q: Can I use different AI models?**
A: Yes, modify the `ai_service.py` to use different models:

```python
# Change the model name
MODEL_NAME = "gemini-1.5-pro"  # or other available models

# Or use different providers (OpenAI, Anthropic, etc.)
```

**Q: How do I backup my data?**
A: Backup these directories:

```bash
# Database
cp chat_database.db backup/

# Vector store
cp -r vector_store backup/

# Documents
cp -r study_docs backup/

# Configuration
cp .env backup/
```

**Q: How do I deploy to production?**
A: Use Docker or cloud services:

```dockerfile
# Dockerfile example
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "serializable_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Technical Questions

**Q: What's the maximum file size I can upload?**
A: Default is 10MB, configurable in the server settings. Large files may need special handling.

**Q: How many documents can the system handle?**
A: The system can handle thousands of documents, limited by available memory and disk space.

**Q: Can I run this without internet?**
A: No, the system requires internet access for Google's AI services. Consider local alternatives like Ollama.

**Q: How do I migrate to a different database?**
A: Modify the database configuration in `database.py` to use PostgreSQL or MySQL instead of SQLite.

### Performance Questions

**Q: Why are responses slow?**
A: Common causes:

- Large vector index
- Complex documents
- API rate limits
- Network latency

**Q: How do I optimize for speed?**
A:

- Reduce chunk size
- Use faster embedding models
- Implement caching
- Optimize vector index type

**Q: Can I use GPU acceleration?**
A: Yes, install FAISS-GPU and modify vector operations to use GPU.

## Getting Help

### Log Files

- Application logs: Check console output
- Error logs: `logs/error.log` (if configured)
- Access logs: Web server logs

### Support Channels

1. Check documentation first
2. Search existing issues
3. Create detailed bug reports
4. Include log files and system information

### Reporting Bugs

Include:

- Python version
- Operating system
- Error messages
- Steps to reproduce
- Log files
- System specifications

### Contributing

- Fork the repository
- Create feature branches
- Submit pull requests
- Follow coding standards
- Include tests
