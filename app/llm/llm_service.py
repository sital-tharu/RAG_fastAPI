from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from app.core.config import get_settings
from app.llm.prompt_templates import FINANCIAL_QA_PROMPT

settings = get_settings()

class LLMService:
    def __init__(self):
        # Initialize Google Gemini
        # Temperature 0 for maximum factuality
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0
        )
        
        self.chain = LLMChain(
            llm=self.llm,
            prompt=FINANCIAL_QA_PROMPT
        )

    async def generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer from LLM based on context
        """
        if not context.strip():
            return "I cannot answer this question as no relevant financial data was found in my database for this company."
            
        try:
            response = await self.chain.arun(
                question=question,
                context=context
            )
            return response
        except Exception as e:
            return f"Error generating answer: {str(e)}"
