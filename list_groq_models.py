
import os
import sys
# sys.path.append(os.getcwd())

from groq import Groq
from app.core.config import get_settings

try:
    key = get_settings().groq_api_key
    print(f"Using key: {key[:5]}...")
    client = Groq(api_key=key)
    
    print("Fetching models...")
    models = client.models.list()
    
    print("\nAvailable Models:")
    for m in models.data:
        print(f"- {m.id}")

except Exception as e:
    print(f"Error: {e}")
