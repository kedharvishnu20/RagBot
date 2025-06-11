import json
import time
import traceback
from typing import List, Dict, Any, Optional, Tuple
import os
import sys

# Import monitoring
try:
    from src.utils.meta_ai_monitor import log_meta_ai_call, log_rate_limit_event
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    def log_meta_ai_call(*args, **kwargs):
        pass
    def log_rate_limit_event(*args, **kwargs):
        pass

try:
    from meta_ai_api import MetaAI as MetaAIClient
except ImportError:
    print("Please install meta-ai-api: pip install meta-ai-api")
    # Create a mock class for testing/development if the real client isn't available
    class MetaAIClient:
        def prompt(self, message=""):
            return {"message": "Meta AI API not installed. This is a mock response."}

class MetaLLM:
    """
    Meta AI integration that can operate with or without RAG
    Includes rate limiting and retry logic to prevent API overload
    """
    def __init__(self, debug=False):
        try:
            self.client = MetaAIClient()
            self.debug = debug
            self.history = []  # Store recent conversation history
            self.max_history = 3  # Maximum number of past exchanges to keep
            
            # Rate limiting settings
            self.last_request_time = 0
            self.min_request_interval = 2.0  # Minimum 2 seconds between requests
            self.max_retries = 2  # Maximum retry attempts
            self.retry_delay = 5.0  # Delay between retries
            
        except Exception as e:
            print(f"Error initializing Meta AI client: {str(e)}")
            # Create a basic client that can handle errors gracefully
            self.client = MetaAIClient() if 'MetaAIClient' in locals() else None
            self.debug = debug
            self.history = []
            self.max_history = 3
            self.last_request_time = 0
            self.min_request_interval = 2.0
            self.max_retries = 2
            self.retry_delay = 5.0
    
    def prepare_context_from_docs(self, docs: List[Any]) -> str:
        """Prepare context string from retrieved documents"""
        if not docs:
            return ""
        
        # Process documents iteratively to avoid overloading
        context_parts = []
        total_char_count = 0
        max_char_limit = 6000  # Set a reasonable max character limit
        
        for i, doc in enumerate(docs):
            # Extract content based on document type
            if hasattr(doc, 'page_content'):
                content = doc.page_content.strip()
                source = doc.metadata.get('source', f"Document {i+1}") if hasattr(doc, 'metadata') else f"Document {i+1}"
                doc_text = f"[Source: {source}]\n{content}"
            elif isinstance(doc, dict) and 'content' in doc:
                content = doc['content'].strip()
                source = doc.get('name', f"Document {i+1}")
                doc_text = f"[Source: {source}]\n{content}"
            elif isinstance(doc, str):
                doc_text = doc.strip()
            else:
                continue  # Skip incompatible document types
                
            # Truncate if needed and add to context
            if total_char_count + len(doc_text) <= max_char_limit:
                context_parts.append(doc_text)
                total_char_count += len(doc_text)
            else:
                # Truncate the document to fit remaining space
                remaining_space = max_char_limit - total_char_count
                if remaining_space > 100:  # Only add if reasonable space left
                    context_parts.append(doc_text[:remaining_space] + "... [truncated]")
                break  # Stop adding documents once limit is reached
                
        return "\n\n".join(context_parts)
    
    def format_history(self) -> str:
        """Format conversation history"""
        if not self.history:
            return ""
        
        formatted = "Previous conversation:\n"
        for entry in self.history:
            if entry['role'] == 'user':
                formatted += f"User: {entry['content']}\n"
            else:
                formatted += f"Assistant: {entry['content']}\n"
        return formatted
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history"""
        self.history.append({'role': role, 'content': content})
        # Keep only the most recent exchanges
        if len(self.history) > self.max_history * 2:  # Each exchange is 2 messages
            self.history = self.history[-self.max_history * 2:]
    
    def construct_prompt(self, question: str, context: str) -> str:
        """Construct the full prompt for Meta AI"""
        prompt_parts = []
        
        # Add system instruction
        prompt_parts.append("You are a helpful, accurate assistant that answers questions based on the provided context.")
        prompt_parts.append("If the context doesn't contain the information needed, say so rather than making up information.")
        
        # Add context if available
        if context:
            prompt_parts.append("\nContext information:")
            prompt_parts.append(context)
        
        # Add conversation history if available
        history_text = self.format_history()
        if history_text:
            prompt_parts.append("\n" + history_text)
        
        # Add the current question
        prompt_parts.append("\nUser question: " + question)
        prompt_parts.append("\nPlease provide a helpful, detailed answer:")
        
        return "\n".join(prompt_parts)
    
    def _rate_limit_check(self):
        """Ensure minimum interval between API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            if self.debug:
                print(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    def _make_request_with_retry(self, message: str) -> Dict[str, Any]:
        """Make API request with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                self._rate_limit_check()
                response = self.client.prompt(message=message)
                return response
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check for HTTP 422 errors specifically
                if '422' in error_str or 'unprocessable entity' in error_str:
                    if attempt < self.max_retries:
                        retry_delay = self.retry_delay * (attempt + 1)  # Exponential backoff
                        if self.debug:
                            print(f"HTTP 422 error, retrying in {retry_delay} seconds (attempt {attempt + 1})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {'message': '🔧 Meta AI request format issue (HTTP 422). Content may be too long or contain invalid characters.'}
                
                # Check for rate limiting errors
                elif any(keyword in error_str for keyword in ['rate limit', 'too many requests', 'quota', 'throttle']):
                    if attempt < self.max_retries:
                        retry_delay = self.retry_delay * (attempt + 1)  # Exponential backoff
                        if self.debug:
                            print(f"Rate limit hit, retrying in {retry_delay} seconds (attempt {attempt + 1})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {'message': '⏱️ Meta AI rate limit reached. Please try again later.'}
                
                # Check for temporary errors
                elif any(keyword in error_str for keyword in ['timeout', 'connection', 'network']):
                    if attempt < self.max_retries:
                        if self.debug:
                            print(f"Network error, retrying in {self.retry_delay} seconds (attempt {attempt + 1})")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {'message': f'⏰ Meta AI connection error after {self.max_retries} retries: {str(e)[:100]}'}
                
                # For other errors, don't retry
                else:
                    return {'message': f'❌ Meta AI error: {str(e)[:100]}'}
        
        return {'message': '❌ Meta AI request failed after all retry attempts'}
    def prompt_simple(self, message: str) -> Dict[str, Any]:
        """
        Send a simple prompt to Meta AI without RAG context
        Includes rate limiting and retry logic
        
        Args:
            message: The user's question
            
        Returns:
            Dict containing the response
        """
        try:
            # Send the prompt with retry logic
            response = self._make_request_with_retry(message)
            
            # Extract response text
            response_text = response["message"]
            
            # Add to conversation history only if successful
            if not any(error_indicator in response_text for error_indicator in ['❌', '⏱️', '⏰']):
                self.add_to_history('user', message)
                self.add_to_history('assistant', response_text)
            
            return {
                'message': response_text,
                'sources': []
            }
            
        except Exception as e:
            error_msg = f"Error querying Meta AI: {str(e)}"
            if self.debug:
                error_msg += f"\n{traceback.format_exc()}"
            return {'message': error_msg, 'sources': []}
    
    def prompt(self, message: str, context_docs: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Send a prompt to Meta AI with context from retrieved documents
        
        Args:
            message: The user's question
            context_docs: Optional list of documents for context
            
        Returns:
            Dict containing the response and source information
        """
        # If no context documents provided, use the simple prompt method
        if not context_docs:
            return self.prompt_simple(message)
        
        # Prepare context from documents iteratively with size limits
        context = self.prepare_context_from_docs(context_docs)
        
        # Construct the full prompt
        full_prompt = self.construct_prompt(message, context)
        
        if self.debug:
            print(f"Sending prompt to Meta AI:\n{full_prompt}")
        try:
            # Send the prompt with retry logic
            response = self._make_request_with_retry(full_prompt)
            
            # Extract response text
            response_text = response["message"]
            
            # Add to conversation history only if successful
            if not any(error_indicator in response_text for error_indicator in ['❌', '⏱️', '⏰']):
                self.add_to_history('user', message)
                self.add_to_history('assistant', response_text)
            
            # Return formatted response with limited source information
            document_sources = []
            
            # Process context documents to format them properly
            if context_docs:
                # Only process a reasonable number of documents (max 5)
                for doc in context_docs[:5]:
                    if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                        name = os.path.basename(doc.metadata.get("source", "Unknown"))
                        # Limit content length to avoid overload
                        document_sources.append({
                            "name": name,
                            "content": doc.page_content[:500],  # Limit content length
                            "document_type": "MetaRag",  # Changed from "meta_rag" to "MetaRAG"
                            "metadata": {k: str(v)[:100] for k, v in doc.metadata.items()}  # Limit metadata values
                        })
            
            return {
                'message': response_text,
                'sources': document_sources if document_sources else []
            }
            
        except Exception as e:
            error_msg = f"Error querying Meta AI: {str(e)}"
            if self.debug:
                error_msg += f"\n{traceback.format_exc()}"
            return {'message': error_msg, 'sources': []}
