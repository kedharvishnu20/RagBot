#!/usr/bin/env python3
"""
Enhanced MetaRAG Processor with HTTP 422 Error Handling

This version addresses common HTTP 422 "Unprocessable Entity" errors by:
1. Adding comprehensive error handling and retries
2. Implementing request validation and sanitization
3. Adding rate limiting protection
4. Providing fallback mechanisms
5. Improving error logging and debugging
"""

from typing import List, Tuple, Dict, Any, Optional
from langchain.schema import Document
import re
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time
import random

# Meta AI API integration with error handling
try:
    from meta_ai_api import MetaAI
    META_AI_AVAILABLE = True
except ImportError:
    print("Meta AI API not available. Install with: pip install meta-ai-api")
    MetaAI = None
    META_AI_AVAILABLE = False

logger = logging.getLogger(__name__)

class MetaRAGProcessorFixed:
    """MetaRAG processor with HTTP 422 error fixes and comprehensive error handling"""
    
    def __init__(self):
        if not META_AI_AVAILABLE:
            raise ImportError("Meta AI API is required but not available. Install with: pip install meta-ai-api")
        
        # Use lazy initialization for Meta AI to avoid hanging during import
        self._meta_ai = None
        self.relevance_threshold = 0.75
        self.max_context_length = 4000   # Reduced to avoid payload issues
        self.max_documents = 4            # Reduced to minimize API load
        self.executor = ThreadPoolExecutor(max_workers=2)  # Reduced workers
        
        # HTTP 422 prevention settings
        self.max_prompt_length = 3000     # Prevent overly long prompts
        self.min_delay_between_calls = 3.0  # Minimum 3 seconds between API calls
        self.max_retries = 2              # Reduced retries to prevent spam
        self.last_api_call_time = 0
        
        # Request validation settings
        self.forbidden_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',              # JavaScript URLs
            r'data:',                   # Data URLs
            r'vbscript:',               # VBScript URLs
        ]
        
        print("✅ MetaRAG processor with HTTP 422 fixes initialized successfully")

    @property
    def meta_ai(self):
        """Lazy initialization of Meta AI with error handling"""
        if self._meta_ai is None:
            try:
                print("🔄 Initializing Meta AI connection...")
                self._meta_ai = MetaAI()
                print("✅ Meta AI connection established")
            except Exception as e:
                print(f"❌ Error initializing Meta AI: {e}")
                raise
        return self._meta_ai

    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitize prompt to prevent HTTP 422 errors"""
        # Remove potentially problematic patterns
        for pattern in self.forbidden_patterns:
            prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE | re.DOTALL)
        
        # Limit prompt length
        if len(prompt) > self.max_prompt_length:
            prompt = prompt[:self.max_prompt_length] + "..."
        
        # Remove control characters and normalize whitespace
        prompt = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', prompt)
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        
        return prompt

    async def _rate_limited_api_call(self, prompt: str, max_retries: int = None) -> Dict[str, Any]:
        """Make a rate-limited API call with retry logic for HTTP 422 errors"""
        if max_retries is None:
            max_retries = self.max_retries
        
        # Enforce rate limiting
        time_since_last_call = time.time() - self.last_api_call_time
        if time_since_last_call < self.min_delay_between_calls:
            await asyncio.sleep(self.min_delay_between_calls - time_since_last_call)
        
        # Sanitize prompt
        sanitized_prompt = self._sanitize_prompt(prompt)
        
        for attempt in range(max_retries + 1):
            try:
                self.last_api_call_time = time.time()
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    self.executor,
                    lambda: self.meta_ai.prompt(sanitized_prompt, new_conversation=True)
                )
                
                if response and 'message' in response:
                    return response
                else:
                    raise Exception("Invalid response from Meta AI")
                    
            except Exception as e:
                error_str = str(e).lower()
                
                # Handle specific HTTP 422 errors
                if "422" in error_str or "unprocessable entity" in error_str:
                    logger.warning(f"HTTP 422 error on attempt {attempt + 1}: {e}")
                    
                    if attempt < max_retries:
                        # Exponential backoff for retries
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.info(f"Retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error("Max retries reached for HTTP 422 error")
                        raise Exception(f"HTTP 422 error after {max_retries + 1} attempts: {e}")
                
                # Handle rate limiting
                elif "rate limit" in error_str or "too many requests" in error_str:
                    if attempt < max_retries:
                        delay = 10 + random.uniform(0, 5)  # Longer delay for rate limits
                        logger.info(f"Rate limited, retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded after {max_retries + 1} attempts: {e}")
                
                # Handle other errors
                else:
                    if attempt < max_retries:
                        delay = 2 + random.uniform(0, 1)
                        logger.info(f"General error, retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise Exception(f"API call failed after {max_retries + 1} attempts: {e}")
        
        raise Exception("Unexpected end of retry loop")

    async def process_query(self, query: str, retriever) -> Tuple[str, List[Document]]:
        """
        Process a query using MetaRAG with comprehensive HTTP 422 error handling
        
        Args:
            query: User's question
            retriever: Vector store retriever
            
        Returns:
            Tuple of (answer, relevant_documents)
        """
        try:
            # Step 1: Input validation
            if not query or len(query.strip()) < 3:
                return "❌ Please provide a valid question with at least 3 characters.", []
            
            # Step 2: Retrieve candidate documents
            candidate_docs = retriever.get_relevant_documents(query)
            
            if not candidate_docs:
                return await self._handle_no_documents(query), []
            
            # Step 3: Local filtering to reduce API calls
            relevant_docs = await self._local_relevance_filtering(query, candidate_docs)
            
            if not relevant_docs:
                return await self._handle_no_documents(query), []
            
            # Step 4: Generate answer with single API call
            answer = await self._generate_comprehensive_answer(query, relevant_docs)
            
            return answer, relevant_docs
            
        except Exception as e:
            logger.error(f"Error in MetaRAG processing: {e}")
            if "422" in str(e) or "unprocessable entity" in str(e).lower():
                return "❌ Unable to process your question due to content validation issues. Please try rephrasing your question.", []
            else:
                return f"❌ Error processing your question: {str(e)[:200]}", []

    async def _local_relevance_filtering(self, query: str, docs: List[Document]) -> List[Document]:
        """Filter documents locally using keyword matching and basic heuristics"""
        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
        query_keywords = {word for word in query_keywords if len(word) > 2}  # Filter short words
        
        scored_docs = []
        for doc in docs[:self.max_documents]:  # Limit documents processed
            content = doc.page_content.lower()
            content_words = set(re.findall(r'\b\w+\b', content))
            
            # Calculate keyword overlap
            common_words = query_keywords.intersection(content_words)
            keyword_score = len(common_words) / max(len(query_keywords), 1)
            
            # Basic content quality check
            content_length_score = min(len(doc.page_content) / 500, 1.0)  # Prefer longer content
            
            # Combined score
            final_score = (keyword_score * 0.7) + (content_length_score * 0.3)
            
            if final_score > 0.1:  # Very low threshold for local filtering
                scored_docs.append((doc, final_score))
        
        # Sort by score and return top documents
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:self.max_documents]]

    async def _generate_comprehensive_answer(self, query: str, docs: List[Document]) -> str:
        """Generate a comprehensive answer using a single API call"""
        
        # Prepare context from documents
        context_parts = []
        for i, doc in enumerate(docs[:self.max_documents]):
            content = doc.page_content[:800]  # Limit content length
            source = doc.metadata.get('source', f'Document {i+1}')
            context_parts.append(f"Source {i+1} ({source}):\n{content}")
        
        context = "\n\n".join(context_parts)
        
        # Limit total context length
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + "..."
        
        comprehensive_prompt = f"""Based on the provided context, please answer the user's question comprehensively and accurately.

USER QUESTION: {query}

CONTEXT:
{context}

Please provide a detailed, accurate answer based on the context provided. If the context doesn't contain enough information to fully answer the question, acknowledge this and provide what information is available.

ANSWER:"""
        
        try:
            response = await self._rate_limited_api_call(comprehensive_prompt)
            answer = response.get('message', '').strip()
            
            if answer:
                return f"📚 MetaRAG Answer: {answer}"
            else:
                return await self._generate_fallback_answer(query, docs)
                
        except Exception as e:
            logger.error(f"Error generating comprehensive answer: {e}")
            return await self._generate_fallback_answer(query, docs)

    async def _generate_fallback_answer(self, query: str, docs: List[Document]) -> str:
        """Generate a simple fallback answer when Meta AI fails"""
        if not docs:
            return "❌ I couldn't find relevant information to answer your question."
        
        # Create a simple concatenated answer from document content
        relevant_content = []
        for doc in docs[:3]:  # Use top 3 documents
            content = doc.page_content[:300]  # Shorter excerpts
            relevant_content.append(content)
        
        combined_content = " ".join(relevant_content)
        
        return f"📄 Based on the available documents: {combined_content[:800]}{'...' if len(combined_content) > 800 else ''}"

    async def _handle_no_documents(self, query: str) -> str:
        """Handle cases where no relevant documents are found"""
        fallback_prompt = f"The user asked: '{query}'. No relevant documents were found. Please provide a helpful response acknowledging this and suggesting how they might rephrase their question or what type of information might be needed."
        
        try:
            response = await self._rate_limited_api_call(fallback_prompt, max_retries=1)
            return f"🔍 {response.get('message', 'No relevant documents found for your question.')}"
        except Exception:
            return "🔍 No relevant documents found for your question. Please try rephrasing your question or asking about a different topic."
