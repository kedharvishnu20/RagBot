from typing import List, Tuple, Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from src.utils.config import get_api_key, config
from src.services.vector_service import VectorStoreService
from src.utils.meta_llm import MetaLLM
from src.utils.gemini_api_manager import gemini_manager

try:
    from src.utils.meta_rag_processor_fixed import MetaRAGProcessorFixed as MetaRAGProcessor
    META_AI_AVAILABLE = True
    print("✅ Fixed MetaRAG processor with HTTP 422 handling imported successfully")
except ImportError as e:
    print(f"⚠️ Fixed MetaRAG processor import failed, trying optimized...")
    try:
        from src.utils.meta_rag_processor_optimized import OptimizedMetaRAGProcessor as MetaRAGProcessor, META_AI_AVAILABLE
        print("✅ Optimized MetaRAG processor imported successfully")
    except ImportError as e:
        print(f"⚠️ Optimized MetaRAG processor import failed, trying original...")
        try:
            from src.utils.meta_rag_processor import MetaRAGProcessor, META_AI_AVAILABLE
            print("✅ Original MetaRAG processor imported successfully")
        except ImportError as e2:
            print(f"⚠️ MetaRAG processor import failed: {e2}")
            META_AI_AVAILABLE = False
            MetaRAGProcessor = None

from src.models.schemas import SourceItem

class AIService:
    """Service for AI model interactions"""
    
    def __init__(self):
        self.vector_service = VectorStoreService()
        self.relevance_threshold = 6.0
        self.top_docs_count = 10
    
    def create_gemini_llm(self, model: str, api_key_index: int = 0) -> ChatGoogleGenerativeAI:
        """Create Gemini LLM instance with rate limiting configuration"""
        api_key = get_api_key(api_key_index)
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            request_timeout=60,
            max_retries=2,
        )
    async def generate_gemini_response(self, message: str, model: str, api_key_index: int = 0) -> str:
        """Generate response using Gemini model with random API selection and rate limit handling"""
        try:
            # Use random API selection if index is None or -1
            if api_key_index is None or api_key_index == -1:
                actual_api_index, is_fallback = await gemini_manager.get_api_key_with_fallback()
                if is_fallback:
                    print(f"🔄 Using fallback API key {actual_api_index} due to quota exhaustion")
            else:
                actual_api_index = api_key_index
            
            llm = self.create_gemini_llm(model, actual_api_index)
            response = llm.invoke(message)
            
            # Mark success
            gemini_manager.mark_api_result(actual_api_index, success=True)
            
            return response.content.strip()
            
        except Exception as e:
            error_msg = str(e)
            is_quota_error = False
            
            if "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                is_quota_error = True
                gemini_manager.mark_api_result(actual_api_index, success=False, is_quota_error=True)
                
                # Try to get another API key
                try:
                    fallback_index, _ = await gemini_manager.get_api_key_with_fallback()
                    if fallback_index != actual_api_index:
                        print(f"🔄 Retrying with API key {fallback_index} after quota exhaustion")
                        llm = self.create_gemini_llm(model, fallback_index)
                        response = llm.invoke(message)
                        gemini_manager.mark_api_result(fallback_index, success=True)
                        return response.content.strip()
                except Exception as retry_e:
                    print(f"⚠️ Fallback also failed: {str(retry_e)[:100]}")
                
                return f"⏱️ All API keys quota exhausted. Next recovery in {self._get_recovery_time_message()}"
                
            elif "timeout" in error_msg.lower():
                gemini_manager.mark_api_result(actual_api_index, success=False, is_quota_error=False)
                return "⏰ Request timed out. Please try again with a shorter message."
            else:
                gemini_manager.mark_api_result(actual_api_index, success=False, is_quota_error=False)
                return f"❌ Error generating answer: {str(e)[:200]}"
    
    async def generate_meta_response(self, message: str) -> str:
        """Generate response using Meta AI"""
        try:
            meta_llm = MetaLLM(debug=False)
            response = meta_llm.prompt_simple(message)
            return response.get('message', "No response from Meta AI")
        except Exception as e:
            return f"❌ Error with Meta AI: {str(e)}"    
    async def generate_rag_response(self, message: str, model: str, api_key_index: int = 0) -> Tuple[str, List[Document]]:
        """Generate response using RAG with random API selection and improved error handling"""
        try:
            # Use random API selection if index is None or -1
            if api_key_index is None or api_key_index == -1:
                actual_api_index, is_fallback = await gemini_manager.get_api_key_with_fallback()
                if is_fallback:
                    print(f"🔄 RAG using fallback API key {actual_api_index}")
            else:
                actual_api_index = api_key_index
            
            llm = self.create_gemini_llm(model, actual_api_index)
            retriever = self.vector_service.get_retriever(actual_api_index)
            
            result = self._process_rag_query(message, retriever, llm)
            
            # Mark success
            gemini_manager.mark_api_result(actual_api_index, success=True)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            if "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                gemini_manager.mark_api_result(actual_api_index, success=False, is_quota_error=True)
                
                # Try with another API key
                try:
                    fallback_index, _ = await gemini_manager.get_api_key_with_fallback()
                    if fallback_index != actual_api_index:
                        print(f"🔄 RAG retrying with API key {fallback_index}")
                        llm = self.create_gemini_llm(model, fallback_index)
                        retriever = self.vector_service.get_retriever(fallback_index)
                        result = self._process_rag_query(message, retriever, llm)
                        gemini_manager.mark_api_result(fallback_index, success=True)
                        return result
                except Exception as retry_e:
                    print(f"⚠️ RAG fallback failed: {str(retry_e)[:100]}")
                
                return f"⏱️ RAG: All API keys quota exhausted. Next recovery in {self._get_recovery_time_message()}", []
                
            elif "timeout" in error_msg.lower():
                gemini_manager.mark_api_result(actual_api_index, success=False, is_quota_error=False)
                return "⏰ RAG: Request timed out. Please try again.", []
            else:
                gemini_manager.mark_api_result(actual_api_index, success=False, is_quota_error=False)
                return f"❌ Error with RAG: {str(e)[:200]}", []

    async def generate_meta_rag_response(self, message: str) -> Tuple[str, List[Document]]:
        """Generate advanced RAG response using Meta AI reasoning with HTTP 422 error handling"""
        try:
            if not META_AI_AVAILABLE or MetaRAGProcessor is None:
                return "❌ MetaRAG is not available. Meta AI API may not be installed.", []
            
            retriever = self.vector_service.get_retriever(0)
            
            try:
                meta_rag = MetaRAGProcessor()
                answer, relevant_docs = await meta_rag.process_query(message, retriever)
                
                # Check if the response indicates an HTTP 422 error
                if "422" in answer or "unprocessable entity" in answer.lower():
                    return "❌ Unable to process your question due to content validation issues. Please try rephrasing your question or asking about a different topic.", []
                
                return answer, relevant_docs
                
            except ImportError as ie:
                return f"❌ MetaRAG initialization failed: {str(ie)}", []
            except Exception as proc_error:
                error_msg = str(proc_error)
                
                # Handle specific HTTP 422 errors
                if "422" in error_msg or "unprocessable entity" in error_msg.lower():
                    return "❌ HTTP 422 Error: The request could not be processed. This may be due to content validation issues or API restrictions. Please try rephrasing your question.", []
                elif "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    return "⏱️ Rate limit reached with Meta AI. Please wait a moment before trying again.", []
                elif "timeout" in error_msg.lower():
                    return "⏰ Request timed out. Please try again with a shorter or simpler question.", []
                else:
                    return f"❌ MetaRAG processing error: {str(proc_error)[:200]}", []
            
        except Exception as e:
            error_msg = str(e)
            if "422" in error_msg or "unprocessable entity" in error_msg.lower():
                return "❌ HTTP 422 Error: Unable to process request. Please try rephrasing your question.", []
            else:
                return f"❌ Error with MetaRAG: {str(e)[:200]}", []
    
    def _process_rag_query(self, question: str, retriever, llm) -> Tuple[str, List[Document]]:
        """Process RAG query with document reranking"""
        try:
            docs = retriever.get_relevant_documents(question)
            if not docs:
                return "No relevant documents found in the database.", []
            
            relevant_docs = self._rerank_documents(question, docs, llm)
            
            if not relevant_docs:
                relevant_docs = docs[:3]
            
            answer = self._generate_answer_from_docs(question, relevant_docs, llm)
            
            return answer, relevant_docs
            
        except Exception as e:
            return f"❌ Error processing RAG query: {str(e)}", []
    
    def _rerank_documents(self, question: str, docs: List[Document], llm, top_n: int = None) -> List[Document]:
        """Rerank documents based on relevance to the question"""
        if top_n is None:
            top_n = self.top_docs_count
            
        scored_docs = []
        
        for doc in docs:
            try:
                score = self._score_document_relevance(question, doc, llm)
                if score >= self.relevance_threshold:
                    scored_docs.append((doc, score))
            except Exception:
                continue
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs[:top_n]]
    
    def _score_document_relevance(self, question: str, doc: Document, llm) -> float:
        """Score document relevance to the question"""
        try:
            scoring_prompt = f"""
On a scale of 1-10, how relevant is this document content to answering the question?
Question: {question}
Document: {doc.page_content[:500]}...

Score (1-10 only):"""
            
            response = llm.invoke(scoring_prompt)
            score_text = response.content.strip()
            
            # Extract numeric score
            import re
            score_match = re.search(r'\d+\.?\d*', score_text)
            if score_match:
                return float(score_match.group())
            return 5.0  # Default middle score
            
        except Exception:
            return 5.0  # Default score on error
    
    def _generate_answer_from_docs(self, question: str, docs: List[Document], llm) -> str:
        """Generate answer from relevant documents"""
        try:
            if not docs:
                return "No relevant documents found to answer the question."
            
            # Prepare context from documents
            context_parts = []
            for i, doc in enumerate(docs):
                source = doc.metadata.get('source', f'Document {i+1}')
                content = doc.page_content[:1000]  # Limit content length
                context_parts.append(f"Source: {source}\nContent: {content}")
            
            context = "\n\n".join(context_parts)
            
            # Create prompt for answer generation
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""Based on the following context, please provide a comprehensive answer to the question. 
If the context doesn't contain relevant information, say so clearly.

Context:
{context}

Question: {question}

Answer:"""
            )
            
            prompt = prompt_template.format(context=context, question=question)
            response = llm.invoke(prompt)
            
            return response.content.strip()
            
        except Exception as e:
            return f"❌ Error generating answer: {str(e)}"
    
    def get_available_modes(self) -> List[str]:
        """Get list of available AI modes"""
        modes = ["RAG", "Gemini", "Meta"]
        
        if META_AI_AVAILABLE and MetaRAGProcessor is not None:
            try:
                test_processor = MetaRAGProcessor()
                modes.append("MetaRAG")
                print("✅ MetaRAG added to available modes")
            except Exception as e:
                print(f"⚠️ MetaRAG not added due to error: {e}")
        
        return modes
    
    def format_source_safe(self, source, source_type: str = "document") -> Optional[Dict[str, Any]]:
        """Safely format a source document for storage and display"""
        try:
            if hasattr(source, 'page_content') and hasattr(source, 'metadata'):
                metadata = source.metadata if isinstance(source.metadata, dict) else {}
                name = metadata.get("source", "Unknown Source")
                if name != "Unknown Source":
                    name = name.split("/")[-1] if "/" in name else name.split("\\")[-1]
                
                return {
                    "name": name,
                    "content": source.page_content[:config.max_content_length],
                    "metadata": {},
                    "document_type": source_type
                }
            elif isinstance(source, dict):
                return {
                    "name": source.get("name", "Unknown"),
                    "content": source.get("content", "")[:config.max_content_length],
                    "metadata": {},
                    "document_type": source_type
                }
            elif isinstance(source, str):
                return {
                    "name": "Text Source",
                    "content": source[:config.max_content_length],
                    "metadata": {},
                    "document_type": source_type
                }
            return None
        except Exception as e:
            print(f"Error formatting source: {str(e)}")
            return {
                "name": "Error Source",
                "content": f"Error formatting source: {str(e)}",
                "metadata": {},
                "document_type": source_type
            }
