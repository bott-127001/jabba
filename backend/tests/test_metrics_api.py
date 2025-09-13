import requests
import json

url = "http://localhost:8000/api/metrics/calculate_metrics"
payload = {
    "instrument_key": "NSE_INDEX|Nifty 50",
    "expiry_date": "2025-09-16"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
