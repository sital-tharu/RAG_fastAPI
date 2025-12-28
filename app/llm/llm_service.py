from langchain_groq import ChatGroq
from typing import Dict, Optional, Tuple
import hashlib
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

from app.core.config import get_settings
from app.llm.prompt_templates import FINANCIAL_QA_PROMPT

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        # Initialize Groq
        # Temperature 0 for maximum factuality
        # Using llama-3.1-8b-instant for better rate limits on free tier
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=settings.groq_api_key,
            temperature=0.0
        )
        
        # LCEL Chain: Prompt | LLM
        self.chain = FINANCIAL_QA_PROMPT | self.llm
        
        # In-memory cache: {cache_key: (response, timestamp)}
        self._cache: Dict[str, Tuple[str, float]] = {}
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

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3), # Reduced retries to fail faster on rate limits
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _execute_chain(self, inputs: Dict):
        return await self.chain.ainvoke(inputs)

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
            print(f"DEBUG: [LLMService] invoking chain for query: {question[:50]}...", flush=True)
            response = await self._execute_chain({
                "question": question,
                "context": context
            })
            print(f"DEBUG: [LLMService] Chain invocation complete. Response received.", flush=True)
            # ChatGoogleGenerativeAI returns an AIMessage, we need the content
            answer = response.content
            
            # Cache the response
            self._add_to_cache(cache_key, answer)
            
            return answer
            
        except RetryError as e:
            # This catches exceptions after all retries failed
            logger.error(f"RetryError generating answer: {e}", exc_info=True)
            return ("**System Notice**: The AI model is currently experiencing high traffic (Rate Limit Reached). "
                    "Please wait a minute and try again.")
                    
        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            if "429" in str(e) or "Rate limit" in str(e): 
                 return ("**System Notice**: The AI model rate limit was reached. "
                         "Please wait a short while before asking another question.")
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

# Global Singleton Instance
llm_service = LLMService()
