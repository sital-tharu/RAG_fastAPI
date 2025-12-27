
print("Debugging Config Loading...")
import os
from dotenv import load_dotenv
from app.core.config import Settings, get_settings

# 1. Check raw file
print("--- Raw .env Content ---")
try:
    with open(".env", "rb") as f:
        print(f.read())
except Exception as e:
    print(f"Error reading .env: {e}")

# 2. Check dotenv load
print("\n--- Dotenv Load ---")
load_dotenv()
print(f"os.environ['GROQ_API_KEY']: {os.environ.get('GROQ_API_KEY')}")
print(f"os.environ['groq_api_key']: {os.environ.get('groq_api_key')}")

# 3. Check Pydantic
print("\n--- Pydantic Settings ---")
try:
    s = Settings()
    print("Settings loaded successfully!")
    print(f"Settings.groq_api_key: {s.groq_api_key}")
except Exception as e:
    print("Settings failed to load:")
    print(e)
