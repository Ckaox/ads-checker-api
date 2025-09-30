import requests
import json
import sys

def test_api():
    url = "https://ads-checker-api.onrender.com/v1/check"
    payload = {"domain": "solfy.net"}
    
    sys.stdout.write("Testing solfy.net...\n")
    sys.stdout.flush()
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        data = response.json()
        
        # Write to file
        with open("render_test_result.json", "w") as f:
            json.dump(data, f, indent=2)
        
        sys.stdout.write(f"\nResults saved to render_test_result.json\n")
        sys.stdout.write(f"\nKey findings:\n")
        sys.stdout.write(f"- Facebook Page: {data.get('facebook_page', 'NULL')}\n")
        sys.stdout.write(f"- Meta Page ID: {data.get('meta_page_id', 'NULL')}\n")
        sys.stdout.write(f"- Has Meta Ads: {data.get('has_meta_ads', False)}\n")
        sys.stdout.write(f"- Has Google Ads: {data.get('has_google_ads', False)}\n")
        sys.stdout.flush()
        
        return data
    
    except Exception as e:
        sys.stdout.write(f"Error: {e}\n")
        sys.stdout.flush()
        return None

if __name__ == "__main__":
    test_api()
