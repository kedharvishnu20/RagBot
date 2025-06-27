# Fixed chat_orchestrator.py - Complete implementation with all missing methods
import logging
from typing import List, Tuple, Dict, Any, Optional, Union
from src.services.ai_service import AIService
from src.services.session_service import SessionService
from src.services.vector_service import VectorStoreService
from src.models.schemas import ChatRequest, ChatResponse, SourceItem
from src.utils.config import AI_MODES
import json
import traceback

logger = logging.getLogger(__name__)

class ChatOrchestrator:
    """FIXED: Complete ChatOrchestrator with all required methods"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.session_service = SessionService()
        self.vector_service = VectorStoreService()
        logger.info("✅ ChatOrchestrator initialized successfully")
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """FIXED: Process a chat request with proper error handling and all required methods"""
        try:
            # Validate AI modes
            if not self.session_service.validate_ai_modes(request.ai_modes):
                invalid_modes = [mode for mode in request.ai_modes if mode not in AI_MODES]
                error_msg = f"Invalid AI modes: {invalid_modes}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Ensure session exists and add user message
            self.session_service.add_user_message(request.session_id, request.message)
            logger.info(f"✅ Added user message to session {request.session_id}")
              # Generate responses for each AI mode IN PARALLEL to prevent blocking
            logger.info(f"🚀 Processing {len(request.ai_modes)} AI modes in parallel: {request.ai_modes}")
            
            # Create async tasks for parallel processing
            async def process_single_mode(mode: str) -> Tuple[str, str, List, List]:
                """Process a single AI mode and return (mode, answer, sources, formatted_sources)"""
                try:
                    logger.debug(f"🤖 Starting processing with AI mode: {mode}")
                    
                    answer, sources = await self._generate_response_for_mode(
                        mode, request.message, request.gemini_model, 
                        request.api_key_index, request.session_id
                    )
                    
                    # Format sources
                    formatted_sources = self._safely_format_sources(sources, mode.lower())
                    
                    logger.debug(f"✅ {mode} response generated successfully")
                    return mode, answer, sources, formatted_sources
                    
                except Exception as mode_error:
                    error_msg = f"❌ Error in {mode} mode: {str(mode_error)}"
                    logger.error(error_msg)
                    return mode, error_msg, [], []
            
            # Process all AI modes concurrently with timeout protection
            import asyncio
            tasks = [process_single_mode(mode) for mode in request.ai_modes]
            
            try:
                # Wait for all tasks with a reasonable timeout (60 seconds total)
                mode_results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), 
                    timeout=60.0
                )
                
                # Process results in the original order
                answers = []
                all_sources = []
                message_sources = []
                
                for i, result in enumerate(mode_results):
                    if isinstance(result, Exception):
                        # Handle exceptions from individual tasks
                        mode = request.ai_modes[i]
                        error_msg = f"❌ {mode} failed: {str(result)[:200]}"
                        logger.error(error_msg)
                        answers.append(error_msg)
                        message_sources.append([])
                    else:
                        mode, answer, sources, formatted_sources = result
                        answers.append(answer)
                        message_sources.append(formatted_sources)
                        all_sources.extend(formatted_sources)
                        
                        # Add assistant message to session
                        self.session_service.add_assistant_message(
                            request.session_id, answer, mode, formatted_sources
                        )
                
                logger.info(f"✅ Parallel processing completed for {len(request.ai_modes)} AI modes")
                
            except asyncio.TimeoutError:
                logger.error("⏰ Timeout: Some AI modes took too long to respond")
                # Provide partial results for modes that completed
                answers = []
                message_sources = []
                all_sources = []
                
                for mode in request.ai_modes:
                    answers.append(f"⏰ {mode}: Request timed out after 60 seconds")
                    message_sources.append([])
            
            # Add new sources to session (avoiding duplicates)
            if all_sources:
                self._add_unique_sources_to_session(request.session_id, all_sources)
            
            # Update usage statistics
            self._update_usage_statistics(request.ai_modes)
            
            # Get all session sources for response
            session_sources = self.session_service.get_session_sources(request.session_id)
            
            # Create safe response
            response = self._create_safe_response(answers, session_sources, message_sources)
            logger.info(f"✅ Chat request processed successfully for session {request.session_id}")
            return response
        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Unexpected error processing chat request: {e}")
            logger.error(traceback.format_exc())
            return self._create_error_response(str(e))
    
    async def _generate_response_for_mode(
        self, mode: str, message: str, gemini_model: str, 
        api_key_index: int, session_id: str) -> Tuple[str, List]:
        """FIXED: Generate response for specific AI mode with timeout protection"""
        import asyncio
        
        async def _generate_with_timeout():
            try:
                if mode == "Gemini":
                    answer = await self.ai_service.generate_gemini_response(message, gemini_model, api_key_index)
                    return answer, []
                elif mode == "Meta":
                    answer = await self.ai_service.generate_meta_response(message + "  note: If your response includes any code (e.g., HTML, CSS, JavaScript, Python, etc.), please wrap it inside a <pre><code>...</code></pre> block to preserve formatting and make it easy to copy. For example:<pre><code><!-- code goes here --></code></pre>Ensure the entire code is valid, indented properly, and self-contained if relevant.")
                    return answer, []
                
                elif mode == "RAG":
                    answer, sources = await self.ai_service.generate_rag_response(message, gemini_model, api_key_index)
                    return answer, sources
                
                elif mode == "MetaRAG":
                    answer, sources = await self.ai_service.generate_meta_rag_response(message)
                    return answer, sources
                
                else:
                    return f"❌ Unknown AI mode: {mode}", []
                    
            except Exception as e:
                logger.error(f"Error in {mode} mode: {e}")
                return f"❌ Error in {mode} mode: {str(e)}", []
        
        try:
            # Apply individual timeout per AI mode (30 seconds)
            return await asyncio.wait_for(_generate_with_timeout(), timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning(f"⏰ {mode} mode timed out after 30 seconds")
            return f"⏰ {mode}: Request timed out after 30 seconds. Please try again.", []
    
    def _safely_format_sources(self, sources: List[Any], source_type: str) -> List[Dict[str, Any]]:
        """FIXED: Format sources into JSON-serializable dictionaries"""
        if not sources:
            return []
        
        formatted_sources = []
        
        for i, source in enumerate(sources):
            try:
                formatted_source = self._format_single_source(source, source_type, i)
                if formatted_source:
                    formatted_sources.append(formatted_source)
            except Exception as e:
                logger.warning(f"Error formatting source {i}: {e}")
                formatted_sources.append(self._create_fallback_source(i, str(e)))
        
        logger.debug(f"📄 Formatted {len(formatted_sources)} sources for type {source_type}")
        return formatted_sources
    
    def _format_single_source(self, source, source_type: str, index: int) -> Optional[Dict[str, Any]]:
        """Format a single source into a dictionary"""
        try:
            if hasattr(source, 'page_content') and hasattr(source, 'metadata'):
                # Langchain document
                metadata = source.metadata if isinstance(source.metadata, dict) else {}
                name = metadata.get("source", f"Source {index + 1}")
                if name != f"Source {index + 1}" and "/" in name:
                    name = name.split("/")[-1]
                elif name != f"Source {index + 1}" and "\\" in name:
                    name = name.split("\\")[-1]
                
                return {
                    "name": name,
                    "content": source.page_content[:500],
                    "preview": source.page_content[:200] + "..." if len(source.page_content) > 200 else source.page_content,
                    "document_type": source_type,
                    "metadata": {}
                }
            elif isinstance(source, dict):
                # Already formatted source
                return {
                    "name": source.get("name", f"Source {index + 1}"),
                    "content": str(source.get("content", ""))[:500],
                    "preview": str(source.get("content", ""))[:200] + "..." if len(str(source.get("content", ""))) > 200 else str(source.get("content", "")),
                    "document_type": source_type,
                    "metadata": source.get("metadata", {})
                }
            elif isinstance(source, str):
                # String source
                return {
                    "name": f"Text Source {index + 1}",
                    "content": source[:500],
                    "preview": source[:200] + "..." if len(source) > 200 else source,
                    "document_type": source_type,
                    "metadata": {}
                }
            else:
                # Unknown source type
                return {
                    "name": f"Unknown Source {index + 1}",
                    "content": str(source)[:500],
                    "preview": str(source)[:200] + "..." if len(str(source)) > 200 else str(source),
                    "document_type": source_type,
                    "metadata": {}
                }
        except Exception as e:
            logger.error(f"Error formatting single source {index}: {e}")
            return self._create_fallback_source(index, str(e))
    
    def _create_fallback_source(self, index: int, error_msg: str) -> Dict[str, Any]:
        """Create a fallback source when formatting fails"""
        return {
            "name": f"Error Source {index + 1}",
            "content": f"Error formatting source: {error_msg}",
            "preview": f"Error: {error_msg[:100]}",
            "document_type": "error",
            "metadata": {}
        }
    
    def _add_unique_sources_to_session(self, session_id: str, new_sources: List[Dict[str, Any]]) -> None:
        """FIXED: Add unique sources to session, avoiding duplicates"""
        try:
            existing_sources = self.session_service.get_session_sources(session_id)
            
            # Create a set of existing source identifiers
            existing_identifiers = set()
            for source in existing_sources:
                if hasattr(source, 'name') and hasattr(source, 'content'):
                    name = source.name or "Unknown"
                    content = (source.content or "")[:100]
                elif isinstance(source, dict):
                    name = source.get('name', 'Unknown')
                    content = str(source.get('content', ''))[:100]
                else:
                    name = str(source)[:50]
                    content = str(source)[:100]
                
                identifier = (name, content)
                existing_identifiers.add(identifier)
            
            # Filter out duplicate sources
            unique_sources = []
            for source in new_sources:
                if isinstance(source, dict):
                    name = source.get('name', 'Unknown')
                    content = str(source.get('content', ''))[:100]
                else:
                    name = str(source)[:50]
                    content = str(source)[:100]
                
                identifier = (name, content)
                if identifier not in existing_identifiers:
                    unique_sources.append(source)
                    existing_identifiers.add(identifier)
            
            # Add unique sources to session
            if unique_sources:
                self.session_service.add_sources_to_session(session_id, unique_sources)
                logger.debug(f"📚 Added {len(unique_sources)} unique sources to session")
                
        except Exception as e:
            logger.error(f"Error adding sources to session: {e}")
    def _update_usage_statistics(self, ai_modes: List[str]) -> None:
        """FIXED: Update usage statistics for AI modes with name standardization"""
        try:
            from src.services.usage_service import get_usage_service
            usage_service = get_usage_service()
            
            # Standardize mode names to ensure consistency
            standardized_modes = []
            for mode in ai_modes:
                # Map inconsistent names to standard names
                if mode in ["MeRag", "Meta+RAG", "SmartRAG"]:
                    standardized_mode = "MetaRAG"
                else:
                    standardized_mode = mode
                standardized_modes.append(standardized_mode)
                usage_service.increment_usage(standardized_mode)
                
            logger.debug(f"✅ Updated usage stats for modes: {standardized_modes} (original: {ai_modes})")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update usage stats: {e}")
    
    def _create_safe_response(self, answers: List[str], session_sources: List, message_sources: List) -> ChatResponse:
        """FIXED: Create a safe, JSON-serializable ChatResponse"""
        try:
            def safe_to_dict(obj):
                """Convert any object to a JSON-safe dictionary"""
                try:
                    if isinstance(obj, dict):
                        return {k: safe_to_dict(v) for k, v in obj.items()}
                    elif hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
                        return safe_to_dict(obj.dict())
                    elif hasattr(obj, '__dict__'):
                        return {k: safe_to_dict(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
                    elif isinstance(obj, list):
                        return [safe_to_dict(item) for item in obj]
                    elif isinstance(obj, (str, int, float, bool, type(None))):
                        return obj
                    else:
                        return {"content": str(obj), "type": type(obj).__name__}
                except Exception as e:
                    return {"error": f"Serialization error: {str(e)}", "type": "error"}

            # Prepare response
            if len(answers) == 1:
                response = ChatResponse(
                    answer=answers[0],
                    sources=[safe_to_dict(source) for source in session_sources],
                    message_sources=[[safe_to_dict(s) for s in ms] for ms in message_sources]
                )
            else:                response = ChatResponse(
                    answers=answers,
                    sources=[safe_to_dict(source) for source in session_sources],
                    message_sources=[[safe_to_dict(s) for s in ms] for ms in message_sources]
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating safe response: {e}")
            return self._create_error_response("Response serialization error")
    
    def _create_error_response(self, error_message: str) -> ChatResponse:
        """FIXED: Create an error response"""
        try:
            return ChatResponse(
                answer=f"❌ Error: {error_message}",
                sources=[],
                message_sources=[]
            )
        except Exception as e:
            logger.error(f"Error creating error response: {e}")
            # Fallback to basic response
            return ChatResponse(
                answer="❌ An unexpected error occurred",
                sources=[],
                message_sources=[]
            )
    
    async def rebuild_vector_index(self, api_key_index: int = 0) -> Dict[str, str]:
        """Rebuild the vector index"""
        try:
            result = await self.vector_service.rebuild_index(api_key_index)
            return {"status": "success", "message": "Vector index rebuilt successfully"}
        except Exception as e:
            logger.error(f"Error rebuilding vector index: {e}")
            return {"status": "error", "message": f"Failed to rebuild index: {str(e)}"}
    
    def clear_vector_database(self) -> Dict[str, str]:
        """Clear the vector database"""
        try:
            success = self.vector_service.clear_vector_store()
            if success:
                return {"status": "success", "message": "Vector database cleared successfully"}
            else:
                return {"status": "error", "message": "Failed to clear vector database"}
        except Exception as e:
            logger.error(f"Error clearing vector database: {e}")
            return {"status": "error", "message": f"Error clearing vector database: {str(e)}"}
    
    def get_vector_store_status(self) -> Dict[str, Any]:
        """Get vector store statistics and status"""
        try:
            return self.vector_service.get_vector_store_stats()
        except Exception as e:
            logger.error(f"Error getting vector store status: {e}")
            return {
                "exists": False,
                "document_count": 0,
                "file_count": 0,
                "error": str(e)
            }
