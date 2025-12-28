
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.llm.llm_service import LLMService

async def test_llm_service():
    print("🚀 Initializing LLMService...")
    try:
        service = LLMService()
        
        # Verify model name
        print(f"ℹ️  Model configured: {service.llm.model_name}")
        
        print("\n🧪 Testing Generate Answer (Simulating Failure Case)...")
        # Simulate the exact context that is failing in production
        real_context = """
=== STRUCTURED FINANCIAL DATA (High Confidence) ===
- Operating Revenue: 5,076,000,000.0 (FY2025 Q3, income_statement)
- Net Profit: 200,000.0 (FY2025 Q3, income_statement)
"""
        response = await service.generate_answer(
            question="What is the revenue for INFY.NS?",
            context=real_context
        )
        
        print(f"📝 Response:\n{response}")
        
        if "100 billion" in response and "Error" not in response:
            print("\n✅ Test PASSED: Correct response received.")
        elif "Rate limit" in response:
            print("\n⚠️ Test PARTIAL: Rate limit handled gracefully.")
        else:
            print(f"\n❌ Test FAILED: Unexpected response.")
            
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: App crashed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_service())
