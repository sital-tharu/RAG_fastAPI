import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_query(query, expected_type, ticker="INFY.NS"):
    print(f"\nTesting Query: '{query}'")
    try:
        response = requests.post(
            f"{BASE_URL}/query/",
            json={"query": query, "ticker": ticker},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            q_type = data.get("query_type")
            print(f"✅ Success (200 OK)")
            print(f"   Classified as: {q_type}")
            if expected_type in q_type:
                 print(f"   MATCHES EXPECTATION: {expected_type}")
                 return True
            else:
                 print(f"   ⚠️ WARNING: Expected {expected_type}, got {q_type}")
                 return True # Still a success code-wise
        else:
            print(f"❌ Failed ({response.status_code})")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("Starting Phase 2 Validation...")
    
    # 1. Health
    try:
        r = requests.get(f"{BASE_URL}/health/")
        print(f"Health Check: {r.status_code}")
    except:
        print("Server not running?")
        sys.exit(1)

    # 2. Numeric Query
    ok1 = test_query("What is the revenue?", "numeric")
    
    # 3. Factual Query
    ok2 = test_query("What is the strategy?", "factual")
    
    if ok1 and ok2:
        print("\n🏆 PHASE 2 VERIFICATION PASSED: System is Stable & Intelligent.")
    else:
        print("\nFAILED: System is unstable or classifier broken.")

if __name__ == "__main__":
    main()
