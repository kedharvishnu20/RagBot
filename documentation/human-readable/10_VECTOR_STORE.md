# Vector Store Directory

## Overview

The `vector_store/` directory contains the processed vector embeddings and indices that power the RAG system's semantic search capabilities. This is the core data store that enables fast and relevant document retrieval.

## Directory Structure

```
vector_store/
├── index.faiss    # FAISS vector index file
└── index.pkl      # Serialized metadata and mappings
```

## File Descriptions

### 1. index.faiss

- **Purpose**: FAISS (Facebook AI Similarity Search) vector index
- **Content**: High-dimensional vector embeddings of document chunks
- **Format**: Binary FAISS index format
- **Size**: Varies based on number of documents and embedding dimensions

#### Technical Details

- **Vector Dimensions**: Typically 768 or 1536 (depends on embedding model)
- **Index Type**: Usually IndexFlatIP (Inner Product) or IndexIVFFlat
- **Similarity Metric**: Cosine similarity or dot product
- **Update Frequency**: Updated when new documents are processed

### 2. index.pkl

- **Purpose**: Serialized Python object containing metadata
- **Content**: Mappings between vector indices and source documents
- **Format**: Python pickle file
- **Components**:
  - Document ID mappings
  - Chunk-to-document relationships
  - Original text snippets
  - File paths and metadata

#### Metadata Structure

```python
{
    'documents': {
        'doc_id_1': {
            'filename': 'document.pdf',
            'upload_time': '2024-01-01T00:00:00',
            'chunks': ['chunk_1', 'chunk_2', ...],
            'metadata': {...}
        }
    },
    'chunks': {
        'chunk_1': {
            'document_id': 'doc_id_1',
            'text': 'Original text content',
            'page_number': 1,
            'chunk_index': 0
        }
    },
    'index_mapping': {
        0: 'chunk_1',
        1: 'chunk_2',
        ...
    }
}
```

## Vector Processing Pipeline

### 1. Document Ingestion

```python
# Document upload triggers processing
document → text_extraction → chunking → embedding → indexing
```

### 2. Text Chunking

- **Chunk Size**: Configurable (typically 500-1000 tokens)
- **Overlap**: 10-20% overlap between chunks
- **Strategy**: Sentence-aware splitting when possible
- **Preservation**: Context and structure maintained

### 3. Embedding Generation

```python
# Using Google's Gemini embedding model
text_chunk → embedding_model → vector_embedding
```

- **Model**: text-embedding-004 or similar
- **Dimensions**: 768 (configurable)
- **Normalization**: L2 normalized for cosine similarity

### 4. Index Building

```python
# FAISS index construction
import faiss
index = faiss.IndexFlatIP(embedding_dim)
index.add(embeddings_array)
```

### 5. Metadata Storage

- Document relationships preserved
- Source attribution maintained
- Search result mapping enabled

## Search and Retrieval Process

### 1. Query Processing

```python
# User query to vector embedding
user_query → embedding_model → query_vector
```

### 2. Similarity Search

```python
# FAISS similarity search
scores, indices = index.search(query_vector, k=top_k)
```

### 3. Result Mapping

```python
# Map indices to original content
for idx in indices:
    chunk_id = index_mapping[idx]
    original_text = chunks[chunk_id]['text']
    document_info = documents[chunks[chunk_id]['document_id']]
```

### 4. Context Assembly

- Relevant chunks retrieved
- Source documents identified
- Context assembled for AI model

## Performance Characteristics

### Search Performance

- **Latency**: Sub-100ms for typical queries
- **Throughput**: Hundreds of queries per second
- **Scalability**: Linear with document count
- **Memory Usage**: Proportional to vector count

### Index Statistics

- **Build Time**: Proportional to document count
- **Update Overhead**: Incremental updates possible
- **Storage Efficiency**: Compressed vector storage
- **Accuracy**: High precision for semantic similarity

## Integration Points

### 1. File Service Integration

```python
# file_service.py processes uploads
upload → extract_text → create_chunks → generate_embeddings → update_index
```

### 2. Vector Service Integration

```python
# vector_service.py manages search
query → embed_query → search_index → retrieve_chunks → return_results
```

### 3. Chat Orchestrator Integration

```python
# chat_orchestrator.py uses retrieved context
user_message → search_context → generate_response → return_with_sources
```

## Configuration and Tuning

### Index Parameters

```python
# FAISS index configuration
INDEX_TYPE = 'IndexFlatIP'  # or IndexIVFFlat for larger datasets
SIMILARITY_METRIC = 'cosine'
SEARCH_K = 5  # Number of results to retrieve
```

### Embedding Parameters

```python
# Embedding model settings
EMBEDDING_MODEL = 'text-embedding-004'
MAX_CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
EMBEDDING_BATCH_SIZE = 32
```

## Maintenance and Operations

### 1. Index Updates

- **New Documents**: Incremental addition to existing index
- **Document Removal**: Index rebuilding required
- **Bulk Updates**: Batch processing for efficiency

### 2. Index Optimization

```python
# Periodic index optimization
faiss.omp_set_num_threads(4)  # Parallel processing
index.train(training_vectors)  # For trained indices
```

### 3. Backup and Recovery

- Regular backup of index files
- Version control for index snapshots
- Recovery procedures documented

### 4. Monitoring

- Index size monitoring
- Query performance metrics
- Error rate tracking
- Resource usage monitoring

## Troubleshooting

### Common Issues

#### 1. Index Corruption

**Symptoms**: Search errors, inconsistent results
**Solutions**:

- Rebuild index from source documents
- Verify file integrity
- Check disk space and permissions

#### 2. Performance Degradation

**Symptoms**: Slow search, high memory usage
**Solutions**:

- Index optimization
- Consider index type change (flat → IVF)
- Resource scaling

#### 3. Missing Results

**Symptoms**: Expected documents not found
**Solutions**:

- Verify embedding consistency
- Check metadata mappings
- Validate document processing

### Diagnostic Commands

```python
# Index diagnostics
print(f"Index size: {index.ntotal}")
print(f"Index dimension: {index.d}")
print(f"Is trained: {index.is_trained}")

# Metadata validation
with open('index.pkl', 'rb') as f:
    metadata = pickle.load(f)
    print(f"Documents: {len(metadata['documents'])}")
    print(f"Chunks: {len(metadata['chunks'])}")
```

## Security Considerations

### Data Protection

- Vector embeddings don't contain raw text
- Metadata access controls
- Encryption at rest (if required)

### Access Control

- Index file permissions
- API-level access controls
- Session-based document access

## Future Enhancements

### Planned Improvements

1. **Advanced Index Types**

   - Product quantization for compression
   - GPU-accelerated search
   - Distributed indices

2. **Enhanced Metadata**

   - Rich document annotations
   - Temporal information
   - Quality scores

3. **Search Optimization**
   - Hybrid search (vector + keyword)
   - Query expansion
   - Result re-ranking

### Scalability Roadmap

- Distributed vector storage
- Microservice architecture
- Cloud-native deployment
- Auto-scaling capabilities
