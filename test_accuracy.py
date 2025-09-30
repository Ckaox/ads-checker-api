#!/usr/bin/env python3
"""
Test accuracy improvements with real domains from the comparison data
"""
import asyncio
import httpx
import json

async def test_accuracy_improvements():
    """Test the improved API with domains that should have ads"""
    client = httpx.AsyncClient(timeout=60.0)
    
    print("🎯 TESTING IMPROVED ADS DETECTION ACCURACY")
    print("Testing domains from comparison data")
    print("=" * 60)
    
    # Test cases from the image - domains that should have ads
    test_cases = [
        {
            "name": "Solfy.net (should have Google: ✓, Meta: ✓)",
            "payload": {"domain": "solfy.net"},
            "expected_google": True,
            "expected_meta": True
        },
        {
            "name": "Creushop.com (should have Google: ✓, Meta: ❌)",
            "payload": {"domain": "creushop.com"},
            "expected_google": True,
            "expected_meta": False
        },
        {
            "name": "Fiskaly.com (should have Google: ✓, Meta: ❌)",
            "payload": {"domain": "fiskaly.com"},
            "expected_google": True,
            "expected_meta": False
        },
        {
            "name": "Equilis.net (should have Google: ✓, Meta: ❌)",
            "payload": {"domain": "equilis.net"},
            "expected_google": True,
            "expected_meta": False
        },
        {
            "name": "Clubpilates.es (should have Google: ✓, Meta: ❌)",
            "payload": {"domain": "clubpilates.es"},
            "expected_google": True,
            "expected_meta": False
        },
        {
            "name": "Test empty facebook_page handling",
            "payload": {"domain": "nike.com", "facebook_page": ""},
            "expected_google": True,
            "expected_meta": True
        }
    ]
    
    results = {
        "google_correct": 0,
        "meta_correct": 0,
        "total_tests": len(test_cases),
        "details": []
    }
    
    try:
        for i, case in enumerate(test_cases, 1):
            print(f"\n🌐 TEST {i}: {case['name']}")
            print(f"Payload: {json.dumps(case['payload'])}")
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
                    
                    # Check accuracy
                    has_google = data.get('has_google_ads', False)
                    has_meta = data.get('has_meta_ads', False)
                    
                    google_correct = has_google == case.get('expected_google', None)
                    meta_correct = has_meta == case.get('expected_meta', None)
                    
                    if case.get('expected_google') is not None:
                        if google_correct:
                            results["google_correct"] += 1
                        print(f"  Google Ads: {'✅' if has_google else '❌'} (Expected: {'✅' if case['expected_google'] else '❌'}) {'✅ CORRECT' if google_correct else '❌ WRONG'}")
                    
                    if case.get('expected_meta') is not None:
                        if meta_correct:
                            results["meta_correct"] += 1
                        print(f"  Meta Ads: {'✅' if has_meta else '❌'} (Expected: {'✅' if case['expected_meta'] else '❌'}) {'✅ CORRECT' if meta_correct else '❌ WRONG'}")
                    
                    results["details"].append({
                        "domain": case["payload"].get("domain"),
                        "has_google": has_google,
                        "has_meta": has_meta,
                        "google_correct": google_correct,
                        "meta_correct": meta_correct,
                        "message": data.get("message", "")
                    })
                    
                else:
                    print(f"❌ ERROR: {response.status_code}")
                    print(f"Response: {response.text}")
                
            except Exception as e:
                print(f"❌ EXCEPTION: {e}")
            
            if i < len(test_cases):
                print(f"\n⏳ Waiting 5 seconds...")
                await asyncio.sleep(5)
    
    finally:
        await client.aclose()
    
    # Print summary
    print(f"\n" + "=" * 60)
    print(f"📊 ACCURACY TEST RESULTS")
    print(f"=" * 60)
    
    google_accuracy = (results["google_correct"] / results["total_tests"]) * 100
    meta_accuracy = (results["meta_correct"] / results["total_tests"]) * 100
    
    print(f"Google Ads Detection: {results['google_correct']}/{results['total_tests']} correct ({google_accuracy:.1f}%)")
    print(f"Meta Ads Detection: {results['meta_correct']}/{results['total_tests']} correct ({meta_accuracy:.1f}%)")
    
    print(f"\n📋 DETAILED RESULTS:")
    for detail in results["details"]:
        domain = detail["domain"]
        google_status = "✅" if detail["has_google"] else "❌"
        meta_status = "✅" if detail["has_meta"] else "❌"
        google_acc = "✅" if detail["google_correct"] else "❌"
        meta_acc = "✅" if detail["meta_correct"] else "❌"
        
        print(f"  {domain}: Google {google_status} {google_acc} | Meta {meta_status} {meta_acc}")
    
    print(f"\n🎉 ACCURACY TEST COMPLETED")
    print(f"Note: Run your local API server first: python main.py")

if __name__ == "__main__":
    asyncio.run(test_accuracy_improvements())
