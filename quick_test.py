import requests
import json

url = "https://ads-checker-api.onrender.com/v1/check"
payload = {"domain": "solfy.net"}

print("Testing:", url)
print("Payload:", json.dumps(payload))
print("\nSending request...")

response = requests.post(url, json=payload, timeout=120)

print(f"Status: {response.status_code}")
print(f"\nResponse:")
print(json.dumps(response.json(), indent=2))

data = response.json()
print(f"\n{'='*60}")
print("ANALYSIS:")
print(f"{'='*60}")
print(f"Domain: {data.get('domain')}")
print(f"Facebook Page: {data.get('facebook_page')}")
print(f"Meta Page ID: {data.get('meta_page_id')}")
print(f"Has Meta Ads: {data.get('has_meta_ads')}")
print(f"Has Google Ads: {data.get('has_google_ads')}")

if not data.get('meta_page_id'):
    print(f"\n🚨 PROBLEM: Meta Page ID is NULL")
    print(f"This is why Meta ads are not being detected!")
