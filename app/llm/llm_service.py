from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Optional
import hashlib
import time
import logging

from app.core.config import get_settings
from app.llm.prompt_templates import FINANCIAL_QA_PROMPT

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        # Initialize Google Gemini
        # Temperature 0 for maximum factuality
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0
        )
        
        # LCEL Chain: Prompt | LLM
        self.chain = FINANCIAL_QA_PROMPT | self.llm
        
        # In-memory cache: {cache_key: (response, timestamp)}
        self._cache: Dict[str, tuple[str, float]] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        self._cache_max_size = 1000  # Maximum cache entries

    def _generate_cache_key(self, question: str, context: str) -> str:
        """
        Generate a cache key from question and context.
        
        Args:
            question: User question
            context: Retrieved context
            
        Returns:
            MD5 hash string as cache key
        """
        combined = f"{question}|||{context}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """
        Get response from cache if valid.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached response if valid, None otherwise
        """
        if cache_key in self._cache:
            response, timestamp = self._cache[cache_key]
            # Check if cache is still valid
            if time.time() - timestamp < self._cache_ttl:
                logger.info(f"Cache hit for key: {cache_key[:8]}...")
                return response
            else:
                # Remove expired entry
                del self._cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, response: str):
        """
        Add response to cache.
        
        Args:
            cache_key: Cache key
            response: LLM response to cache
        """
        # Simple cache size management: remove oldest if at max
        if len(self._cache) >= self._cache_max_size:
            # Remove oldest entry (first inserted)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache full, removed oldest entry")
        
        self._cache[cache_key] = (response, time.time())
        logger.debug(f"Cached response for key: {cache_key[:8]}...")

    async def generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer from LLM based on context.
        Uses in-memory cache to reduce API calls.
        
        Args:
            question: User's question
            context: Retrieved context from RAG
            
        Returns:
            LLM-generated answer
        """
        if not context.strip():
            return "I cannot answer this question as no relevant financial data was found in my database for this company."
        
        # Check cache first
        cache_key = self._generate_cache_key(question, context)
        cached_response = self._get_from_cache(cache_key)
        
        if cached_response:
            return cached_response
            
        try:
            # invoke chain with input dict
            logger.info(f"Calling LLM for new query (cache miss)")
            response = await self.chain.ainvoke({
                "question": question,
                "context": context
            })
            # ChatGoogleGenerativeAI returns an AIMessage, we need the content
            answer = response.content
            
            # Cache the response
            self._add_to_cache(cache_key, answer)
            
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            return f"Error generating answer: {str(e)}"
    
    def clear_cache(self):
        """Clear the entire cache."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_max_size": self._cache_max_size,
            "cache_ttl_seconds": self._cache_ttl
        }
