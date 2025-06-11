# RAG AI Application

A sophisticated Retrieval-Augmented Generation (RAG) application that combines multiple AI models with advanced document processing and seamless preview capabilities.

## 🚀 Key Features

- **Advanced Document Processing**: Seamless DOCX-to-PDF conversion with multiple fallback methods
- **Real-time Document Preview**: Tabbed interface with text extract and visual document viewing
- **Multiple AI Modes**: RAG, Gemini, Meta AI, and MetaRAG with intelligent model selection
- **Intelligent Document Retrieval**: Vector-based semantic search with source citations
- **Smart API Management**: Automatic API key rotation and quota handling
- **Modern Chat Interface**: Real-time web UI with enhanced source display
- **Session Management**: Persistent chat sessions with comprehensive history
- **Error Recovery**: Comprehensive error handling and graceful fallback mechanisms
- **File Management**: Upload, preview, download, and delete documents with ease

## 🎯 New in Version 2.1.0

### Enhanced Document Preview System

- **Seamless DOCX Viewing**: Automatic background conversion to PDF for consistent experience
- **Tabbed Preview Interface**: Switch between text extract and visual document preview
- **Real-time Loading**: Asynchronous document loading with progress indicators
- **Multiple Conversion Methods**: Robust fallback system for reliable document conversion
- **Conversion Caching**: Improved performance with cached PDF conversions

### Improved User Experience

- **Transparent File Handling**: Users see PDF previews for Word documents automatically
- **Enhanced Source References**: Better visual presentation with preview capabilities
- **Clean Modal Design**: Modern, intuitive interface for document interaction
- **Action Buttons**: Direct access to view, download, and preview functions

## 🏗️ Architecture

### Core Components

1. **Enhanced AI Service Layer** (`src/services/ai_service.py`)

   - Manages multiple AI model integrations
   - Handles API key rotation and quota management
   - Implements advanced RAG processing with source citations

2. **Advanced Vector Store Service** (`src/services/vector_service.py`)

   - Manages document embeddings and retrieval
   - Supports multiple embedding models with optimized search
   - Implements semantic search with relevance scoring

3. **Comprehensive File Service** (`src/services/file_service.py`)

   - Handles multi-format document processing (PDF, TXT, DOCX, DOC)
   - Automatic DOCX-to-PDF conversion with caching
   - File management operations with validation

4. **Session Management** (`src/services/session_service.py`)

   - Persistent chat sessions with detailed history
   - Message source tracking and metadata management
   - Session analytics and usage statistics

5. **Enhanced Web Interface** (`src/static/`)
   - Modern chat interface with real-time document preview
   - Advanced source document display with tabbed viewing
   - Responsive session management UI
   - File upload with drag-and-drop support

### Document Processing Pipeline

1. **Upload & Validation**: Multi-format file support with size and type validation
2. **Text Extraction**: Format-specific content extraction with encoding detection
3. **Document Conversion**: Automatic DOCX-to-PDF conversion for seamless viewing
4. **Vector Embedding**: Advanced chunking and embedding generation
5. **Index Storage**: Efficient FAISS vector storage with metadata
6. **Preview Generation**: Real-time preview with caching for performance

### AI Models Supported

- **Gemini 1.5 Flash**: Fast responses for quick interactions
- **Gemini 1.5 Pro**: High-quality responses for complex queries
- **Meta AI**: Advanced conversational AI with reasoning capabilities
- **RAG Mode**: Document-enhanced responses with source citations
- **MetaRAG**: Advanced reasoning combining Meta AI with document context

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.8+** (recommended: Python 3.10+)
- **Git** for version control
- **Internet connection** for package installation and AI model access

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd rag-ai-app
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv ragi
   ragi\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   copy .env.example .env
   # Edit .env file with your API keys
   ```

5. **Start the application**

   ```bash
   python serializable_server.py
   ```

6. **Access the application**
   - Open your browser and navigate to `http://localhost:8000`
   - Upload documents and start chatting!

### Detailed Setup

#### 1. Environment Configuration

Create a `.env` file based on `.env.example`:

```env
# Google Gemini API Keys (add multiple for rotation)
GEMINI_API_KEY_1=your_gemini_key_1
GEMINI_API_KEY_2=your_gemini_key_2
GEMINI_API_KEY_3=your_gemini_key_3

# Meta AI Configuration (optional)
META_AI_SESSION=your_meta_session

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
```

#### 2. Document Conversion Setup

The application includes multiple conversion methods for DOCX files:

- **Primary**: `docx2pdf` (included in requirements)
- **Fallback**: `python-docx` + `reportlab` (included in requirements)
- **Alternative**: LibreOffice (optional, for advanced conversion)

For LibreOffice support (optional):

- Download and install LibreOffice
- Ensure `libreoffice` command is available in PATH

#### 3. Directory Structure

The application will create these directories automatically:

- `study_docs/` - Uploaded documents
- `converted_pdfs/` - Cached PDF conversions
- `vector_store/` - FAISS embeddings database

#### 4. First Run

1. **Upload Documents**: Use the file upload area to add PDF, TXT, or DOCX files
2. **Build Index**: Click "Rebuild Index" to process documents and create embeddings
3. **Start Chatting**: Ask questions about your uploaded documents
4. **Preview Documents**: Click "Document Preview" on any source to view the file

## 🚀 Usage

### Starting the Application

1. **Activate virtual environment**:

   ```bash
   ragi\Scripts\activate
   ```

2. **Start the server**:

   ```bash
   python serializable_server.py
   ```

3. **Access the application**:
   - Open browser to `http://localhost:8000`
   - The server runs on port 8000 by default

### Using the Interface

#### Document Management

1. **Upload Files**:

   - Click the upload area or drag-and-drop files
   - Supported formats: PDF, TXT, DOCX, DOC
   - Maximum size: 10MB per file

2. **View Documents**:

   - Click "Document Preview" in source references
   - Switch between "Text Extract" and "Document Preview" tabs
   - Download or open files in new tabs

3. **Manage Files**:
   - View uploaded files in the sidebar
   - Delete individual files or clear all uploads
   - Rebuild vector index after adding/removing documents

#### Chat Features

1. **Ask Questions**:

   - Type questions about your uploaded documents
   - Select AI model: Gemini Flash, Gemini Pro, or Meta AI
   - Enable/disable RAG mode for document-based responses

2. **View Sources**:

   - See source documents with relevance scores
   - Click document previews to view full content
   - Page-specific citations for PDFs

3. **Session Management**:
   - Create new chat sessions
   - Switch between existing sessions
   - View conversation history

### Advanced Features

#### API Key Management

- The system automatically rotates between available API keys
- Add multiple Gemini API keys for higher rate limits
- Fallback mechanisms handle quota exhaustion

#### Document Conversion

- DOCX files are automatically converted to PDF for viewing
- Conversions are cached for improved performance
- Multiple conversion methods ensure reliability

#### Error Handling

- Graceful fallback when primary AI models fail
- Automatic retry mechanisms for temporary failures
- Clear error messages for user actions

The server will start on `http://localhost:8001`

### Web Interface

1. Open your browser and navigate to `http://localhost:8001`
2. Select an AI mode (RAG, Gemini, Meta, MetaRAG)
3. Start asking questions!

### API Endpoints

#### Chat Endpoint

```http
POST /chat
Content-Type: application/json

{
  "message": "Your question here",
  "mode": "rag",
  "model": "gemini-1.5-flash",
  "api_key_index": 0,
  "session_id": "optional-session-id"
}
```

#### Session Management

```http
GET /sessions                    # List all sessions
POST /sessions                   # Create new session
GET /sessions/{id}               # Get session details
DELETE /sessions/{id}            # Delete session
GET /sessions/{id}/sources       # Get session sources
```

## 🔧 Configuration

### AI Service Configuration

Edit `src/utils/config.py`:

```python
class Config:
    temperature = 0.7
    max_tokens = 2048
    max_content_length = 1000
    embedding_model = "models/embedding-001"
```

### API Key Management

The system supports multiple API keys for load balancing and quota management:

- Add multiple Gemini API keys as `GOOGLE_API_KEY_0`, `GOOGLE_API_KEY_1`, etc.
- The system automatically rotates between available keys
- Quota-exhausted keys are temporarily disabled

### Vector Store Configuration

Documents are automatically embedded and stored in ChromaDB. To add new documents:

1. Place documents in the `study_docs/` directory
2. Restart the server to re-index documents

## 🔍 AI Modes Explained

### RAG (Retrieval-Augmented Generation)

- Retrieves relevant documents from the vector store
- Uses Gemini to generate responses based on retrieved context
- Best for questions about your specific documents

### Gemini

- Direct interaction with Google's Gemini model
- General knowledge and reasoning capabilities
- No document context

### Meta AI

- Uses Meta's conversational AI
- Good for creative and conversational responses
- No document context

### MetaRAG

- Advanced reasoning combining Meta AI with document retrieval
- Multi-step analysis and synthesis
- Best for complex questions requiring deep analysis

## 🛡️ Error Handling

The application includes comprehensive error handling:

### HTTP 422 Resolution

- Automatic prompt sanitization
- Content length validation
- Retry mechanisms with exponential backoff

### API Quota Management

- Automatic API key rotation
- Graceful degradation when quotas are exhausted
- User-friendly error messages

### Timeout Protection

- 30-second timeout for all API calls
- Prevents server hanging
- Automatic fallback to alternative APIs

## 📊 Performance Optimization

### Document Processing

- **Automatic Conversion Caching**: DOCX-to-PDF conversions are cached for faster subsequent access
- **Multiple Conversion Methods**: Fallback systems ensure reliable document conversion
- **Asynchronous Processing**: All file operations are non-blocking for better user experience

### Vector Search

- **FAISS Integration**: Highly optimized vector similarity search
- **Chunking Strategy**: Intelligent document segmentation for optimal retrieval
- **Embedding Caching**: Reduces computation overhead for repeated queries

### API Management

- **Key Rotation**: Automatic rotation across multiple API keys for higher rate limits
- **Request Optimization**: Efficient batching and caching of API requests
- **Fallback Systems**: Multiple AI models ensure service availability

## 🧹 Project Maintenance

### Automated Cleanup

The project includes a `cleanup.bat` script for regular maintenance:

```bash
# Run automated cleanup
cleanup.bat
```

**Cleanup Tasks:**

- Removes Python cache directories (`__pycache__/`)
- Deletes temporary files (`.tmp`, `.temp`, `*~`)
- Cleans test files from study_docs
- Removes backup database files
- Clears log files

### Manual Maintenance

- **Weekly**: Monitor conversion cache size, check database health
- **Monthly**: Update dependencies, optimize vector store
- **Quarterly**: Full backup, performance review

See `MAINTENANCE.md` for detailed maintenance procedures.

## 📚 Documentation

### Available Documentation

- **`README.md`** - This overview and setup guide
- **`CHANGELOG.md`** - Version history and feature updates
- **`MAINTENANCE.md`** - Comprehensive maintenance guide
- **`documentation/human-readable/`** - Detailed technical documentation
- **`documentation/ai-agent-rebuild/`** - Development and reconstruction guides

### Quick References

- **API Routes**: `documentation/human-readable/04_API_ROUTES.md`
- **Frontend Guide**: `documentation/human-readable/08_FRONTEND.md`
- **Troubleshooting**: `documentation/human-readable/12_TROUBLESHOOTING.md`
- **Setup Guide**: `documentation/human-readable/02_SETUP_INSTALLATION.md`

## 🤝 Contributing

### Development Workflow

1. **Setup Development Environment**: Follow installation guide
2. **Make Changes**: Use appropriate code style and documentation
3. **Test Changes**: Verify functionality with existing documents
4. **Update Documentation**: Keep documentation current with changes
5. **Run Cleanup**: Use `cleanup.bat` before committing

### Code Style

- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use modern ES6+ features
- **Documentation**: Update relevant markdown files
- **Comments**: Clear, concise explanations for complex logic

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support

### Getting Help

1. **Check Documentation**: Review relevant guides in `documentation/`
2. **Troubleshooting**: See `documentation/human-readable/12_TROUBLESHOOTING.md`
3. **Maintenance Issues**: Consult `MAINTENANCE.md`
4. **Version Changes**: Check `CHANGELOG.md` for recent updates

### Reporting Issues

When reporting issues, please include:

- **System Information**: OS, Python version, browser
- **Error Messages**: Complete error text and stack traces
- **Steps to Reproduce**: Detailed reproduction steps
- **Expected vs Actual Behavior**: Clear description of the problem
- **Log Files**: Any relevant application logs

---

**RAG AI Application v2.1.0** - Advanced document processing with seamless preview capabilities.

### Lazy Loading

- Components are loaded only when needed
- Reduces initial startup time

### Caching

- Session data is cached for quick access
- Document embeddings are persisted

### Async Processing

- All AI API calls are asynchronous
- Non-blocking server operations

## 🧪 Testing

### Run All Tests

```bash
python comprehensive_test_8001.py
```

### Test Specific Components

```bash
# Test Gemini API
python test_gemini_api_index7.py

# Test session management
python test_sources_fix.py

# Test HTTP 422 fixes
python test_http_422_resolution.py
```

## 🐛 Troubleshooting

### Common Issues

1. **"Meta AI API not available"**

   - Install: `pip install meta-ai-api`
   - Restart the server

2. **"HTTP 422 Unprocessable Entity"**

   - Check API key validity
   - Ensure message content is appropriate
   - Try shorter messages

3. **"API quota exhausted"**

   - Add more API keys to `.env`
   - Wait for quota reset (usually 24 hours)

4. **Sources not displaying**
   - Check browser console for errors
   - Refresh the page
   - Verify session ID is valid

### Debug Mode

Enable debug logging by setting:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Development

### Project Structure

```
rag-ai-app/
├── src/
│   ├── services/          # Core business logic
│   ├── models/           # Data models and schemas
│   ├── utils/            # Utility functions
│   └── static/           # Frontend assets
├── study_docs/           # Document corpus
├── vector_store/         # ChromaDB storage
└── tests/               # Test files
```

### Adding New AI Models

1. Create a new method in `AIService`
2. Add model configuration to `config.py`
3. Update frontend model selection
4. Add appropriate error handling

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🙏 Acknowledgments

- Google Gemini API
- Meta AI API
- LangChain framework
- ChromaDB vector database
- FastAPI web framework

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs in the console
3. Create an issue on GitHub

---

**Version**: 2.0.0  
**Last Updated**: June 2025  
**Status**: Production Ready ✅
