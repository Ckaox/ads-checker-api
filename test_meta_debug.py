#!/usr/bin/env python3
"""
Quick test to debug Meta ads detection with detailed logging
"""
import asyncio
import httpx
import json

async def test_meta_detection():
    """Test Meta ads detection with detailed output"""
    client = httpx.AsyncClient(timeout=60.0)
    
    print("🔍 META ADS DETECTION DEBUG TEST")
    print("=" * 60)
    
    # Test with domains from your image that should have Meta ads
    test_domains = [
        "solfy.net",
        "lesamis.cc",
        "heylenwarehouses.com",
        "creushop.com",  # Should NOT have Meta ads
        "nike.com"  # Known to have Meta ads
    ]
    
    for domain in test_domains:
        print(f"\n{'='*60}")
        print(f"🌐 Testing: {domain}")
        print(f"{'='*60}")
        
        try:
            response = await client.post(
                "http://localhost:8000/v1/check",
                json={"domain": domain}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n📊 RESULTS:")
                print(f"  Domain: {data.get('domain')}")
                print(f"  Facebook Page: {data.get('facebook_page')}")
                print(f"  Meta Page ID: {data.get('meta_page_id')}")
                print(f"  Has Meta Ads: {'✅ YES' if data.get('has_meta_ads') else '❌ NO'}")
                print(f"  Has Google Ads: {'✅ YES' if data.get('has_google_ads') else '❌ NO'}")
                print(f"  Message: {data.get('message')}")
                
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(f"Response: {response.text[:500]}")
        
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print(f"\n⏳ Waiting 3 seconds before next test...")
        await asyncio.sleep(3)
    
    await client.aclose()
    
    print(f"\n{'='*60}")
    print("✅ Debug test completed!")
    print("Check the logs above for detailed Meta ads detection process")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Make sure your API is running!")
    print("Run in another terminal: python main.py\n")
    
    try:
        asyncio.run(test_meta_detection())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
