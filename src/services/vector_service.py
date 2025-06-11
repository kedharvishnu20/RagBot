# Fixed vector_service.py - Addresses race conditions and locking issues
import os
import shutil
import time
import threading
import logging
from typing import List, Tuple, Optional, Dict, Any, Dict, Any
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from src.utils.config import config, get_api_key
from filelock import FileLock
import tempfile

logger = logging.getLogger(__name__)

class VectorStoreService:
    """FIXED: Service for managing vector store operations with proper locking"""
    
    def __init__(self):
        self.vector_db_path = config.vector_db_path
        self.study_docs_folder = config.study_docs_folder
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap
        
        self._rebuild_lock = threading.RLock()
        self._cache_lock = threading.RLock()
        self._vector_store_cache = {}
        self._last_rebuild_time = 0
        
        self._file_lock_path = f"{self.vector_db_path}.lock"
        
        logger.info("✅ VectorStoreService initialized with thread safety")
    
    def create_embeddings(self, api_key: str) -> GoogleGenerativeAIEmbeddings:
        """Create and return GoogleGenerativeAI embeddings instance
        
        Args:
            api_key: The API key for Google Generative AI
            
        Returns:
            GoogleGenerativeAIEmbeddings: Configured embeddings instance
        """
        logger.debug(f"🔧 Creating GoogleGenerativeAI embeddings instance")
        return GoogleGenerativeAIEmbeddings(
            google_api_key=api_key,
            model="models/embedding-001"
        )
    
    def build_vector_store(self, api_key_index: int = 5, force_rebuild: bool = True) -> FAISS:
        """FIXED: Build or load vector store with proper locking"""
        with self._rebuild_lock:
            try:
                api_key = get_api_key(api_key_index)
                embeddings = self.create_embeddings(api_key)
                
                cache_key = f"{api_key_index}_{force_rebuild}"
                if not force_rebuild:
                    cached_store = self._get_cached_vector_store(cache_key)
                    if cached_store:
                        logger.debug("📋 Using cached vector store")
                        return cached_store
                
                with FileLock(self._file_lock_path, timeout=30):
                    if force_rebuild or not os.path.exists(self.vector_db_path):
                        vector_store = self._rebuild_vector_store_locked(embeddings)
                    else:
                        vector_store = self._load_existing_vector_store_locked(embeddings)
                
                self._cache_vector_store(cache_key, vector_store)
                return vector_store
                
            except Exception as e:
                logger.error(f"Error building vector store: {e}")
                raise ValueError(f"Failed to build vector store: {str(e)}")
    
    def _rebuild_vector_store_locked(self, embeddings: GoogleGenerativeAIEmbeddings) -> FAISS:
        """FIXED: Rebuild vector store with atomic operations"""
        logger.info("🔄 Starting vector store rebuild")
        
        files = self._get_document_files()
        if not files:
            raise ValueError("No documents found to index")
        
        chunks = self.load_and_split_documents(files)
        if not chunks:
            raise ValueError("No content extracted from documents")
        
        temp_dir = tempfile.mkdtemp(prefix="vector_store_temp_")
        temp_path = os.path.join(temp_dir, "temp_store")
        
        try:
            vector_store = FAISS.from_documents(chunks, embeddings)
            vector_store.save_local(temp_path)
            
            if os.path.exists(self.vector_db_path):
                backup_path = f"{self.vector_db_path}_backup_{int(time.time())}"
                shutil.move(self.vector_db_path, backup_path)
                logger.debug(f"📦 Backed up old vector store to {backup_path}")
              # Create parent directory only if it's not empty (for relative paths)
            parent_dir = os.path.dirname(self.vector_db_path)
            if parent_dir:  # Only create if parent_dir is not empty
                os.makedirs(parent_dir, exist_ok=True)
            shutil.move(temp_path, self.vector_db_path)
            
            if 'backup_path' in locals() and os.path.exists(backup_path):
                shutil.rmtree(backup_path, ignore_errors=True)
            
            self._last_rebuild_time = time.time()
            logger.info(f"✅ Vector store rebuilt successfully with {len(chunks)} chunks")
            
            return vector_store
            
        except Exception as e:
            logger.error(f"Error during vector store rebuild: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def get_retriever(self, api_key_index: int = 0, force_rebuild: bool = False):
        """FIXED: Get retriever with optimized search parameters"""
        try:
            vector_store = self.build_vector_store(api_key_index, force_rebuild)
            
            retriever = vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 15,
                    "fetch_k": 30,
                    "lambda_mult": 0.7
                }
            )
            
            logger.debug("🔍 Retriever created successfully")
            return retriever
            
        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            raise ValueError(f"Failed to create retriever: {str(e)}")
    
    def _get_cached_vector_store(self, cache_key: str) -> Optional[FAISS]:
        """Get cached vector store if available"""
        with self._cache_lock:
            return self._vector_store_cache.get(cache_key)
    
    def _cache_vector_store(self, cache_key: str, vector_store: FAISS) -> None:
        """Cache vector store for reuse"""
        with self._cache_lock:
            self._vector_store_cache[cache_key] = vector_store
            logger.debug(f"📦 Cached vector store with key: {cache_key}")
    
    def _load_existing_vector_store_locked(self, embeddings: GoogleGenerativeAIEmbeddings) -> FAISS:
        """Load existing vector store from disk"""
        try:
            logger.debug("📖 Loading existing vector store")
            vector_store = FAISS.load_local(
                self.vector_db_path, 
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("✅ Existing vector store loaded successfully")
            return vector_store
        except Exception as e:            
            logger.warning(f"Failed to load existing vector store: {e}")
            logger.info("🔄 Rebuilding vector store instead")
            return self._rebuild_vector_store_locked(embeddings)
    
    def _get_document_files(self) -> List[str]:
        """Get list of document files to process"""
        if not os.path.exists(self.study_docs_folder):
            logger.warning(f"Study docs folder not found: {self.study_docs_folder}")
            return []
            
        supported_extensions = ['.pdf', '.docx', '.txt', '.md']
        files = []
        
        for root, dirs, filenames in os.walk(self.study_docs_folder):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    file_path = os.path.join(root, filename)
                    # Validate file path is not empty
                    if file_path and file_path.strip():
                        files.append(file_path)
                    else:
                        logger.error(f"❌ Empty file path generated from root='{root}', filename='{filename}'")
        
        logger.info(f"📁 Found {len(files)} document files")
        # Additional validation: check for any empty paths
        valid_files = [f for f in files if f and f.strip()]
        if len(valid_files) != len(files):
            logger.error(f"❌ Found {len(files) - len(valid_files)} empty file paths!")
        return valid_files

    def load_and_split_documents(self, file_paths: List[str]) -> List[Document]:
        """Load and split documents into chunks"""
        documents = []
        
        logger.info(f"🔍 Processing {len(file_paths)} file paths")
        
        for i, file_path in enumerate(file_paths):
            logger.info(f"📄 Processing file {i+1}/{len(file_paths)}: '{file_path}'")
            
            # Check for empty or invalid paths
            if not file_path or not file_path.strip():
                logger.error(f"❌ Empty file path detected at index {i}")
                continue
                
            if not os.path.exists(file_path):
                logger.error(f"❌ File does not exist: {file_path}")
                continue
                
            try:
                docs = self._load_single_document(file_path)
                documents.extend(docs)
                logger.debug(f"✅ Loaded document: {os.path.basename(file_path)} ({len(docs)} chunks)")
            except Exception as e:
                logger.error(f"❌ Failed to load {file_path}: {e}")
                continue
        
        if not documents:
            raise ValueError("No documents could be loaded")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)        
        logger.info(f"📄 Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks

    def _load_single_document(self, file_path: str) -> List[Document]:
        """Load a single document based on its extension"""
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension == '.docx':
                loader = Docx2txtLoader(file_path)
            elif file_extension in ['.txt', '.md']:
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                # Fallback to unstructured loader
                loader = UnstructuredFileLoader(file_path)
            
            documents = loader.load()
            
            # Add source metadata
            for doc in documents:
                doc.metadata['source'] = file_path
                doc.metadata['filename'] = os.path.basename(file_path)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise
    
    def clear_vector_store(self) -> bool:
        """Clear the vector store and cache"""
        try:
            with self._rebuild_lock:
                # Clear cache
                with self._cache_lock:
                    self._vector_store_cache.clear()
                
                # Remove vector store files
                if os.path.exists(self.vector_db_path):
                    shutil.rmtree(self.vector_db_path, ignore_errors=True)
                    logger.info("🗑️ Vector store cleared successfully")
                    return True
                else:
                    logger.info("📭 Vector store was already empty")
                    return True
                    
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            stats = {
                "exists": os.path.exists(self.vector_db_path),
                "document_count": 0,
                "file_count": 0,
                "last_rebuild": self._last_rebuild_time,
                "cache_size": len(self._vector_store_cache)
            }
            
            if stats["exists"]:
                # Count files in study docs folder
                if os.path.exists(self.study_docs_folder):
                    files = self._get_document_files()
                    stats["file_count"] = len(files)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {
                "exists": False,
                "document_count": 0,
                "file_count": 0,
                "error": str(e)
            }
    async def rebuild_index(self, api_key_index: int = 0) -> Dict[str, Any]:
        """
        Rebuild the vector index from all available documents
        
        Args:
            api_key_index: Index of the API key to use for embeddings
            
        Returns:
            Dict containing rebuild status and statistics
        """
        try:
            logger.info("🔄 Starting vector index rebuild...")
            
            # Check if study docs folder exists and has files
            if not os.path.exists(self.study_docs_folder):
                error_msg = f"Study docs folder not found: {self.study_docs_folder}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "old_document_count": 0,
                    "new_document_count": 0,
                    "file_count": 0,
                    "error": error_msg
                }
            
            # Check if there are any files to process
            files = self._get_document_files()
            if not files:
                error_msg = f"No supported document files found in {self.study_docs_folder}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "old_document_count": 0,
                    "new_document_count": 0,
                    "file_count": 0,
                    "error": error_msg
                }
            
            # Get stats before rebuild
            old_stats = self.get_vector_store_stats()
            
            # Force rebuild the vector store
            vector_store = self.build_vector_store(
                api_key_index=api_key_index, 
                force_rebuild=True
            )
            
            # Get stats after rebuild
            new_stats = self.get_vector_store_stats()
            
            result = {
                "status": "success",
                "message": "Vector index rebuilt successfully",
                "old_document_count": old_stats.get("document_count", 0),
                "new_document_count": new_stats.get("document_count", 0),
                "file_count": new_stats.get("file_count", 0),
                "rebuild_time": time.time() - self._last_rebuild_time if self._last_rebuild_time else 0
            }
            
            logger.info(f"✅ Vector index rebuild completed: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Vector index rebuild failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "status": "error", 
                "message": error_msg,
                "old_document_count": 0,
                "new_document_count": 0,
                "file_count": 0,
                "error": str(e)
            }
