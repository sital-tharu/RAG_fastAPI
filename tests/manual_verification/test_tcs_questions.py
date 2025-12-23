import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
TICKER = "TCS.NS"

QUESTIONS = [
    "What was the total revenue of TCS.NS in FY2023?",
    "What was the Net Profit Margin of TCS.NS in FY2023?",
    "Compare the total revenue of TCS.NS between FY2022 and FY2023. Which year was higher?",
    "What were the total assets of TCS.NS in FY2023?",
    "What was the Capital Expenditure (CapEx) of TCS.NS in FY2023, and from which statement is it derived?",
    "Is there enough data to calculate the Return on Equity (ROE) for FY2023? If yes, provide the value. If not, explain why.",
    "Will the stock price of TCS go up next year?"
]

def wait_for_server():
    print("Waiting for server...")
    for _ in range(10):
        try:
            r = requests.get(f"{BASE_URL}/health")
            if r.status_code == 200:
                print("Server is up!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(2)
    print("Server failed to start.")
    return False

def ask(query):
    with open("test_results.txt", "a", encoding="utf-8") as f:
        f.write(f"\n❓ Q: {query}\n")
        print(f"\n❓ Q: {query}")
        try:
            response = requests.post(
                f"{BASE_URL}/query/",
                json={"query": query, "ticker": TICKER},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer provided")
                f.write(f"✅ A: {answer}\n")
                print(f"✅ A: {answer}")
            else:
                f.write(f"❌ Error {response.status_code}: {response.text}\n")
                print(f"❌ Error {response.status_code}: {response.text}")
        except Exception as e:
            f.write(f"❌ Exception: {e}\n")
            print(f"❌ Exception: {e}")

def main():
    if not wait_for_server():
        sys.exit(1)
    
    for q in QUESTIONS:
        ask(q)

if __name__ == "__main__":
    main()
