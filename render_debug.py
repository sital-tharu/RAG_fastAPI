import requests
import json
import sys

API_KEY = "rnd_pdK4TKpHT5Eg6rrzaWZpjRoBp70Y"
BASE_URL = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

def get_service_logs():
    # 1. Get Service ID
    print("Fetching services...")
    resp = requests.get(f"{BASE_URL}/services", headers=headers)
    if resp.status_code != 200:
        print(f"Error fetching services: {resp.text}")
        return

    services = resp.json()
    rag_service = next((s for s in services if s['service']['name'] == 'financial-rag'), None)
    
    if not rag_service:
        print("Service 'financial-rag' not found.")
        print("Available services:", [s['service']['name'] for s in services])
        return

    service_id = rag_service['service']['id']
    print(f"Found Service ID: {service_id}")

    # 2. Get Latest Deploy
    params = {"limit": 1}
    resp = requests.get(f"{BASE_URL}/services/{service_id}/deploys", headers=headers, params=params)
    if resp.status_code != 200:
        print(f"Error fetching deploys: {resp.text}")
        return

    deploys = resp.json()
    if not deploys:
        print("No deploys found.")
        return

    deploy_id = deploys[0]['deploy']['id']
    status = deploys[0]['deploy']['status']
    print(f"Latest Deploy ID: {deploy_id} (Status: {status})")

    # 3. Get Logs used only for failure analysis
    # NOTE: Render API doesn't always expose raw logs via simple endpoint easily without streams,
    # but we can check the deploy details first.
    
    print("-" * 50)
    print("DEPLOY DETAILS:")
    print(json.dumps(deploys[0], indent=2))

if __name__ == "__main__":
    get_service_logs()
