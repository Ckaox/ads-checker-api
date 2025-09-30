#!/usr/bin/env python3
"""
Test the Render deployed API
"""
import asyncio
import httpx
import json

async def test_render_api():
    """Test the production API on Render"""
    
    base_url = "https://ads-checker-api.onrender.com"
    
    print("🌐 TESTING RENDER API")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Test 1: Health check
        print("\n📍 Test 1: Health Check")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ API is alive!")
                print(f"Response: {response.text}")
            else:
                print(f"❌ Health check failed")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Check API with solfy.net
        print("\n" + "=" * 60)
        print("📍 Test 2: Check solfy.net (should have Meta ads)")
        print("=" * 60)
        try:
            payload = {"domain": "solfy.net"}
            print(f"Request: POST {base_url}/v1/check")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                f"{base_url}/v1/check",
                json=payload
            )
            
            print(f"\nStatus: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ SUCCESS! Response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Analyze results
                print(f"\n{'='*60}")
                print("📊 ANALYSIS:")
                print(f"{'='*60}")
                print(f"Domain: {data.get('domain')}")
                print(f"Facebook Page: {data.get('facebook_page') or '❌ NOT FOUND'}")
                print(f"Meta Page ID: {data.get('meta_page_id') or '❌ NULL (PROBLEM!)'}")
                print(f"Has Meta Ads: {'✅ YES' if data.get('has_meta_ads') else '❌ NO'}")
                print(f"Has Google Ads: {'✅ YES' if data.get('has_google_ads') else '❌ NO'}")
                
                if not data.get('meta_page_id'):
                    print(f"\n🚨 ISSUE IDENTIFIED:")
                    print(f"  Meta Page ID is NULL!")
                    print(f"  This means the Facebook page resolution or Page ID extraction failed.")
                    print(f"  Without a Page ID, Meta ads cannot be detected.")
                
                if not data.get('facebook_page'):
                    print(f"\n🚨 ISSUE IDENTIFIED:")
                    print(f"  Facebook page was not found!")
                    print(f"  The domain resolver couldn't find the Facebook page for this domain.")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Test 3: Check with nike.com (known to have Facebook)
        print("\n" + "=" * 60)
        print("📍 Test 3: Check nike.com (known brand)")
        print("=" * 60)
        try:
            payload = {"domain": "nike.com"}
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                f"{base_url}/v1/check",
                json=payload
            )
            
            print(f"\nStatus: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                print(f"\n📊 Nike Results:")
                print(f"  Facebook Page: {data.get('facebook_page') or 'NOT FOUND'}")
                print(f"  Meta Page ID: {data.get('meta_page_id') or 'NULL'}")
                print(f"  Has Meta Ads: {'✅ YES' if data.get('has_meta_ads') else '❌ NO'}")
            else:
                print(f"❌ Error: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print(f"\n{'='*60}")
    print("🏁 TEST COMPLETED")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_render_api())
