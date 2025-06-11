import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

class AppConfig:
    """Application configuration"""
    def __init__(self):
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "vector_store")
        self.study_docs_folder = os.getenv("STUDY_DOCS_FOLDER", r"study_docs")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.4"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2048"))
        self.default_model = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
        self.max_content_length = 500

        # Validation to prevent empty paths
        if not self.vector_db_path or not self.vector_db_path.strip():
            raise ValueError("VECTOR_DB_PATH environment variable is missing or empty.")
        if not self.study_docs_folder or not self.study_docs_folder.strip():
            raise ValueError("STUDY_DOCS_FOLDER environment variable is missing or empty.")

class ApiKeys:
    """API keys configuration"""
    def __init__(self):
        main_key = os.getenv("GOOGLE_API_KEY")
        if main_key:
            self.google_api_keys = [main_key]
        else:
            self.google_api_keys = []
            
        for i in range(1, 11):
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if key:
                self.google_api_keys.append(key)
                
        self.meta_fb_email = os.getenv("META_FB_EMAIL")
        self.meta_fb_password = os.getenv("META_FB_PASSWORD")
    
    def get_all_keys(self) -> List[str]:
        """Get all available Google API keys"""
        return [key for key in self.google_api_keys if key and key.strip()]

config = AppConfig()
api_keys = ApiKeys()

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite", 
    "gemini-2.5-flash-preview-04-17",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

AI_MODES = ["RAG", "Gemini", "Meta", "MetaRAG"]

def get_api_key(index: int = 0) -> str:
    """Get a Google API key by index with fallback"""
    valid_keys = [k for k in api_keys.google_api_keys if k]
    if not valid_keys:
        raise ValueError("No valid Google API keys found")
    
    return valid_keys[index % len(valid_keys)]
