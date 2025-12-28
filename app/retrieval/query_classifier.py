from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.config import get_settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# from google.api_core.exceptions import ResourceExhausted

settings = get_settings()

class QueryType(Enum):
    NUMERIC = "numeric"  # SQL Tables (Income, Balance, Ratios)
    FACTUAL = "factual"  # Vector Store (Text, Risks, Strategy)
    HYBRID = "hybrid"    # Both
    GENERAL = "general"   # LLM Knowledge

class ClassificationResult(BaseModel):
    query_type: str = Field(description="The classified type: numeric, factual, hybrid, or general")
    reasoning: str = Field(description="Brief reason for the classification")

class QueryClassifier:
    def __init__(self):
        # Use a lightweight fast model for classification
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant", 
            api_key=settings.groq_api_key,
            temperature=0.0
        )
        
        self.parser = JsonOutputParser(pydantic_object=ClassificationResult)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial query intent classifier.
Analyze the user's question and classify it into one of the following categories:

1. **numeric**: Questions requiring specific financial constants, calculated ratios, or data from financial statements (e.g., "What is the revenue?", "Calculate P/E ratio", "Compare debt of X and Y").
2. **factual**: Questions about qualitative aspects, business description, risks, management, strategy, or text-based info (e.g., "What does the company do?", "Who is the CEO?", "List the risk factors").
3. **hybrid**: Questions requiring both numbers and context (e.g., "Why did revenue drop in 2023?").
4. **general**: Questions not related to specific financial data or requiring RAG (e.g., "What is a stock market?", "Hi").

Output JSON only.
"""),
            ("human", "{query}"),
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    @retry(
        retry=retry_if_exception_type(Exception), # Groq might raise different errors, general retry for now + specific
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _execute_chain(self, query: str):
        return await self.chain.ainvoke({"query": query})

    async def classify(self, query: str) -> QueryType:
        """
        Classifies the query using LLM.
        """
        try:
            # We use invoke (sync) wrapped in sync-to-async if needed, or if chain supports async invoke
            # LangChain chains usually support ainvoke
            result = await self._execute_chain(query)
            
            q_type_str = result.get("query_type", "hybrid").lower()
            
            if "numeric" in q_type_str:
                return QueryType.NUMERIC
            elif "factual" in q_type_str:
                return QueryType.FACTUAL
            elif "general" in q_type_str:
                return QueryType.GENERAL
            else:
                return QueryType.HYBRID
        except Exception as e:
            print(f"Classifier Error: {e}")
            # Fallback to Hybrid on error
            return QueryType.HYBRID

# Global Singleton Instance
query_classifier = QueryClassifier()
