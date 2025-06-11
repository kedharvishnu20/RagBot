# Study Documents Directory

## Overview

The `study_docs/` directory contains the source documents that are processed and indexed by the RAG system. These documents serve as the knowledge base for the AI assistant.

## Directory Structure

```
study_docs/
├── imp questions mid1.pdf        # Important questions for mid-term 1
├── test_document.txt            # Test document for system validation
└── Unit 5 (lattice theory) mfcs.pdf  # Lattice theory unit from MFCS course
```

## Document Types and Purposes

### 1. Academic Documents

- **imp questions mid1.pdf**

  - Contains important questions for mid-term examination 1
  - Used for educational content retrieval
  - Format: PDF document

- **Unit 5 (lattice theory) mfcs.pdf**
  - Mathematical Foundations of Computer Science (MFCS) course material
  - Covers lattice theory concepts
  - Academic reference material
  - Format: PDF document

### 2. Test Documents

- **test_document.txt**
  - Simple text file used for system testing
  - Validates document processing pipeline
  - Format: Plain text
  - Purpose: Development and testing

## Document Processing Workflow

### 1. Document Ingestion

```python
# Documents are processed through the file upload API
POST /api/files/upload
- Accepts PDF, TXT, and other supported formats
- Validates file type and size
- Stores original file metadata
```

### 2. Content Extraction

- PDF documents: Text extraction using PyPDF2 or similar libraries
- Text documents: Direct content reading
- Preserves document structure and formatting where possible

### 3. Text Chunking

- Documents are split into manageable chunks
- Chunk size optimized for embedding models
- Maintains context coherence across chunks

### 4. Vector Embedding

- Text chunks converted to vector embeddings
- Uses Google's embedding models (Gemini)
- Embeddings stored in FAISS vector database

### 5. Indexing

- Vectors indexed for efficient similarity search
- Metadata preserved for source attribution
- Enables rapid retrieval during chat queries

## Integration with RAG System

### Vector Storage

- Processed documents stored in `vector_store/` directory
- FAISS index provides fast similarity search
- Supports real-time query processing

### Chat Integration

- Documents provide context for AI responses
- Relevant passages retrieved based on user queries
- Source attribution maintained for transparency

### Session Management

- Document access tracked per user session
- Upload history maintained
- File management through web interface

## Usage Guidelines

### Adding New Documents

1. Use the web interface file upload feature
2. Supported formats: PDF, TXT, DOC, DOCX
3. Maximum file size limits apply (configurable)
4. Documents automatically processed and indexed

### Document Management

- View uploaded documents in session interface
- Delete documents through web UI
- Re-upload updated versions as needed

### Best Practices

- Use descriptive filenames
- Organize documents by topic or course
- Regular cleanup of obsolete documents
- Monitor storage usage

## Technical Considerations

### File Format Support

- **PDF**: Primary format for academic documents
- **TXT**: Simple text files for testing
- **DOC/DOCX**: Microsoft Word documents (if configured)
- **Additional formats**: Can be added through file processing service

### Storage Requirements

- Original files stored in `study_docs/`
- Vector representations in `vector_store/`
- Database metadata in SQLite
- Consider disk space for large document collections

### Performance Impact

- Large documents increase processing time
- More documents improve knowledge coverage
- Balance between comprehensiveness and performance
- Regular index optimization recommended

## Troubleshooting

### Common Issues

1. **File Upload Failures**

   - Check file size limits
   - Verify supported format
   - Ensure sufficient disk space

2. **Processing Errors**

   - PDF corruption or protection
   - Encoding issues in text files
   - Memory limitations for large files

3. **Search Quality**
   - Insufficient document content
   - Poor document quality (scanned PDFs)
   - Need for better chunking strategies

### Solutions

- Monitor processing logs
- Use high-quality source documents
- Regular system maintenance
- Update processing algorithms as needed

## Future Enhancements

### Planned Features

- Support for additional file formats
- Automatic document categorization
- Advanced metadata extraction
- Document versioning system

### Optimization Opportunities

- Improved chunking algorithms
- Better embedding models
- Enhanced search relevance
- Automated document quality assessment
