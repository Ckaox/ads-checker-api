#!/usr/bin/env python3
"""
Test Page ID extraction specifically
"""
import asyncio
import httpx
import json

async def test_page_id_extraction():
    """Test that Page IDs are being extracted correctly"""
    client = httpx.AsyncClient(timeout=60.0)
    
    print("🔍 PAGE ID EXTRACTION TEST")
    print("=" * 60)
    print("This test checks if Meta Page IDs are being extracted")
    print("=" * 60)
    
    # Test domains from your image
    test_cases = [
        {"domain": "solfy.net", "expected_has_page_id": True},
        {"domain": "creushop.com", "expected_has_page_id": True},
        {"domain": "lesamis.cc", "expected_has_page_id": True},
        {"domain": "fiskaly.com", "expected_has_page_id": True},
        {"domain": "nike.com", "expected_has_page_id": True},
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        domain = case["domain"]
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_cases)}: {domain}")
        print(f"{'='*60}")
        
        try:
            response = await client.post(
                "http://localhost:8000/v1/check",
                json={"domain": domain}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                facebook_page = data.get('facebook_page')
                meta_page_id = data.get('meta_page_id')
                has_meta_ads = data.get('has_meta_ads')
                
                print(f"\n📊 RESULTS:")
                print(f"  ✓ Domain: {domain}")
                print(f"  ✓ Facebook Page: {facebook_page if facebook_page else '❌ NOT FOUND'}")
                print(f"  ✓ Meta Page ID: {meta_page_id if meta_page_id else '❌ NULL (PROBLEM!)'}")
                print(f"  ✓ Has Meta Ads: {'✅ YES' if has_meta_ads else '❌ NO'}")
                
                if meta_page_id:
                    print(f"\n  ✅ SUCCESS: Page ID extracted!")
                    results.append({"domain": domain, "success": True, "page_id": meta_page_id})
                else:
                    print(f"\n  ❌ FAILED: Page ID is NULL")
                    results.append({"domain": domain, "success": False, "page_id": None})
                
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                results.append({"domain": domain, "success": False, "error": response.status_code})
        
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({"domain": domain, "success": False, "error": str(e)})
        
        if i < len(test_cases):
            print(f"\n⏳ Waiting 3 seconds...")
            await asyncio.sleep(3)
    
    await client.aclose()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r.get('success'))
    total = len(results)
    
    print(f"\nPage ID Extraction: {success_count}/{total} successful ({(success_count/total)*100:.1f}%)")
    
    print(f"\n📋 DETAILS:")
    for result in results:
        domain = result['domain']
        if result.get('success'):
            page_id = result.get('page_id')
            print(f"  ✅ {domain}: {page_id}")
        else:
            print(f"  ❌ {domain}: FAILED")
    
    if success_count == total:
        print(f"\n🎉 ALL PAGE IDs EXTRACTED SUCCESSFULLY!")
        print(f"Now Meta ads detection should work!")
    elif success_count > 0:
        print(f"\n⚠️  PARTIAL SUCCESS: Some Page IDs extracted")
        print(f"Check the logs above to see why others failed")
    else:
        print(f"\n🚨 NO PAGE IDs EXTRACTED!")
        print(f"There's still an issue with Page ID extraction")
        print(f"Check the detailed logs above for clues")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Make sure your API is running!")
    print("Run in another terminal: python main.py\n")
    
    try:
        asyncio.run(test_page_id_extraction())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
