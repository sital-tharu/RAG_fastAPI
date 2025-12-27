
print("Starting Groq verification...")
import os
import sys
import traceback
sys.path.append(os.getcwd())

try:
    from app.retrieval.query_classifier import QueryClassifier, QueryType
    from app.core.config import get_settings
    print(f"Imports successful. Key len: {len(get_settings().groq_api_key) if get_settings().groq_api_key else 0}")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

import asyncio
from langchain_groq import ChatGroq

async def verify():
    print("Testing RAW ChatGroq connection first...")
    try:
        llm = ChatGroq(
            model="llama-3.1-8b-instant", 
            api_key=get_settings().groq_api_key,
            temperature=0
        )
        print(f"Attempting to invoke with model: {llm.model_name}", flush=True)
        msg = await llm.ainvoke("Hi")
        print(f"Raw Test Success: {msg.content}")
    except Exception as e:
        print("Raw Test Failed:")
        traceback.print_exc()

    print("\nInitializing Classifier...")
    try:
        classifier = QueryClassifier()
        print(f"Classifier initialized.")
        
        print("\nTesting Query: 'What is the revenue of Apple?'")
        # We need to see the error inside classify if it swallows it
        # But classify catches and prints "Classifier Error: ..." then returns HYBRID
        # So we should look at stdout for that print.
        
        result = await classifier.classify("What is the revenue of Apple?")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())
