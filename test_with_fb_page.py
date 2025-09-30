import requests
import json

def test_with_facebook_page():
    """Test when Facebook page is provided"""
    
    url = "https://ads-checker-api.onrender.com/v1/check"
    
    # Test cases where we KNOW the Facebook page
    test_cases = [
        {
            "name": "Nike (known brand with Facebook)",
            "payload": {
                "domain": "nike.com",
                "facebook_page": "https://www.facebook.com/nike"
            }
        },
        {
            "name": "Coca-Cola",
            "payload": {
                "domain": "coca-cola.com",
                "facebook_page": "https://www.facebook.com/CocaCola"
            }
        },
        {
            "name": "Solfy with guessed FB",
            "payload": {
                "domain": "solfy.net",
                "facebook_page": "https://www.facebook.com/solfy"
            }
        }
    ]
    
    print("🧪 TESTING WITH FACEBOOK PAGE PROVIDED")
    print("="*60)
    print("This tests if Meta Page ID extraction and ads detection")
    print("work when we already have the Facebook page URL")
    print("="*60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {case['name']}")
        print(f"{'='*60}")
        print(f"Payload: {json.dumps(case['payload'], indent=2)}")
        
        try:
            response = requests.post(url, json=case['payload'], timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                # Save to file
                with open(f"fb_test_{i}.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                print(f"\n✅ Response received (saved to fb_test_{i}.json)")
                print(json.dumps(data, indent=2))
                
                # Analysis
                print(f"\n📊 ANALYSIS:")
                fb_page = data.get('facebook_page')
                page_id = data.get('meta_page_id')
                has_meta = data.get('has_meta_ads')
                
                print(f"  Facebook Page: {fb_page if fb_page else '❌ NULL'}")
                print(f"  Meta Page ID: {page_id if page_id else '❌ NULL (PROBLEM!)'}")
                print(f"  Has Meta Ads: {'✅ YES' if has_meta else '❌ NO'}")
                
                if page_id:
                    print(f"\n  ✅ Page ID extracted successfully!")
                    if has_meta:
                        print(f"  ✅ Meta ads detected!")
                    else:
                        print(f"  ⚠️  Page ID exists but no ads detected")
                else:
                    print(f"\n  🚨 PROBLEM: Page ID is NULL")
                    print(f"  The facebook_resolver.extract_page_id() is failing!")
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(response.text[:500])
        
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        if i < len(test_cases):
            print(f"\n⏳ Waiting 3 seconds...")
            import time
            time.sleep(3)
    
    print(f"\n{'='*60}")
    print("🏁 TEST COMPLETED")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_with_facebook_page()
