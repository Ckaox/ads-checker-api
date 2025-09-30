#!/usr/bin/env python3
"""
Test simple para la API simplificada
"""
import asyncio
import httpx
import json

async def test_simple_api():
    """Test de la API simplificada"""
    client = httpx.AsyncClient(timeout=30.0)
    
    print("🎯 TESTING SIMPLIFIED ADS CHECKER API")
    print("Single endpoint: POST /v1/check")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            "name": "Solo dominio",
            "payload": {"domain": "micole.net"},
            "expected": "Debe encontrar Facebook page y detectar ads"
        },
        {
            "name": "Solo Facebook page",
            "payload": {"facebook_page": "https://www.facebook.com/micoleoficial/"},
            "expected": "Debe encontrar dominio y detectar ads"
        },
        {
            "name": "Ambos proporcionados",
            "payload": {
                "domain": "tmdc.es",
                "facebook_page": "https://www.facebook.com/tmdc.es/"
            },
            "expected": "Debe validar y detectar ads"
        },
        {
            "name": "Dominio sin ads",
            "payload": {"domain": "example.com"},
            "expected": "No debe detectar ads"
        }
    ]
    
    try:
        for i, case in enumerate(test_cases, 1):
            print(f"\n🌐 TEST {i}: {case['name']}")
            print(f"Payload: {json.dumps(case['payload'])}")
            print(f"Expected: {case['expected']}")
            print("-" * 50)
            
            try:
                response = await client.post(
                    "http://localhost:8000/v1/check",
                    json=case["payload"]
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"✅ SUCCESS!")
                    print(f"📋 RESPONSE:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Analyze results
                    print(f"\n📊 ANALYSIS:")
                    print(f"  Domain resolved: {data.get('domain', 'None')}")
                    print(f"  Facebook page: {data.get('facebook_page', 'None')}")
                    print(f"  Meta page ID: {data.get('meta_page_id', 'None')}")
                    print(f"  Has Meta ads: {'✅' if data.get('has_meta_ads') else '❌'}")
                    print(f"  Has Google ads: {'✅' if data.get('has_google_ads') else '❌'}")
                    print(f"  Message: {data.get('message', 'None')}")
                    
                else:
                    print(f"❌ ERROR: {response.status_code}")
                    print(f"Response: {response.text}")
                
            except Exception as e:
                print(f"❌ EXCEPTION: {e}")
            
            if i < len(test_cases):
                print(f"\n⏳ Waiting 3 seconds...")
                await asyncio.sleep(3)
    
    finally:
        await client.aclose()
    
    print(f"\n✅ SIMPLE API TEST COMPLETED")
    print(f"\n🎉 SUMMARY:")
    print(f"  ✅ Single endpoint: POST /v1/check")
    print(f"  ✅ Input: domain and/or facebook_page")
    print(f"  ✅ Output: resolved identities + boolean ads detection")
    print(f"  ✅ No complex schemas or multiple endpoints")
    print(f"  ✅ Clean and focused functionality")

if __name__ == "__main__":
    asyncio.run(test_simple_api())
