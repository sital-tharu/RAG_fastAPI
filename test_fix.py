
import requests
import json

url = "http://127.0.0.1:8000/api/v1/query/"
headers = {"Content-Type": "application/json"}
payload = {
    "query": "What is the revenue for INFY.NS?",
    "ticker": "INFY.NS"
}

try:
    print(f"Sending query: {payload['query']}")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        ans = response.json().get("answer", "")
        print(f"✅ Status 200. Full Answer: {ans}")
        if "Cannot determine" in ans:
            print("❌ FAILURE: 'Cannot determine'")
        elif "Error" in ans or "Exception" in ans:
            print("❌ FAILURE: Application Error returned")
        else:
            print("✅ SUCCESS: Valid Answer")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")
