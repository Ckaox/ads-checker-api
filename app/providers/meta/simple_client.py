"""
Simplified Meta client - only for ads presence detection
"""
import re
import httpx
from typing import Optional
from urllib.parse import urlparse, parse_qs

from app.core.config import settings

class SimpleMetaClient:
    """Simplified client for Meta ads presence detection only"""
    
    def __init__(self):
        self.access_token = settings.META_ACCESS_TOKEN
        self.base_url = "https://graph.facebook.com/v18.0"
        self.ad_library_url = "https://www.facebook.com/ads/library"
        
        self.client = httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
    
    async def get_page_id(self, facebook_page: str) -> Optional[str]:
        """Extract Facebook Page ID from URL or username"""
        try:
            if facebook_page.isdigit():
                return facebook_page
            
            if "facebook.com" in facebook_page:
                patterns = [
                    r"facebook\.com/([^/?]+)",
                    r"facebook\.com/pages/[^/]+/(\d+)",
                    r"facebook\.com/profile\.php\?id=(\d+)"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, facebook_page)
                    if match:
                        page_identifier = match.group(1)
                        
                        if page_identifier.isdigit():
                            return page_identifier
                        else:
                            # Try to resolve username to ID
                            resolved_id = await self._resolve_username_to_id(page_identifier)
                            if resolved_id:
                                return resolved_id
            
        except Exception as e:
            print(f"Error extracting page ID from {facebook_page}: {e}")
        
        return None
    
    async def _resolve_username_to_id(self, username: str) -> Optional[str]:
        """Resolve Facebook username to page ID - Enhanced"""
        try:
            print(f"🔍 Resolving username to ID: {username}")
            
            # Method 1: Try Graph API WITHOUT token first (works for many public pages)
            try:
                url = f"{self.base_url}/{username}"
                response = await self.client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    page_id = data.get("id")
                    if page_id:
                        print(f"✅ Got Page ID from Graph API (no token): {page_id}")
                        return page_id
            except Exception as e:
                print(f"Graph API without token failed: {e}")
            
            # Method 2: Try with token if available
            if self.access_token:
                try:
                    url = f"{self.base_url}/{username}"
                    params = {"access_token": self.access_token}
                    
                    response = await self.client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        page_id = data.get("id")
                        if page_id:
                            print(f"✅ Got Page ID from Graph API (with token): {page_id}")
                            return page_id
                except Exception as e:
                    print(f"Graph API with token failed: {e}")
            
            # Method 3: Scrape the public page
            print(f"Trying to scrape page HTML...")
            page_url = f"https://www.facebook.com/{username}"
            response = await self.client.get(page_url, follow_redirects=True)
            
            if response.status_code == 200:
                content = response.text
                
                # Enhanced patterns
                id_patterns = [
                    r'"page_id":"(\d+)"',
                    r'"pageID":"(\d+)"',
                    r'"entity_id":"(\d+)"',
                    r'profile_id=(\d+)',
                    r'"userID":"(\d+)"',
                    r'"id":"(\d+)"[^}]*?"__typename":"Page"',
                    r'pageID[=:](\d+)',
                    r'fb://page/(\d+)',
                ]
                
                for pattern in id_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        page_id = match.group(1)
                        if page_id.isdigit() and 8 <= len(page_id) <= 20:
                            print(f"✅ Got Page ID from HTML scraping: {page_id}")
                            return page_id
            
            print(f"❌ Could not resolve Page ID for username: {username}")
        except Exception as e:
            print(f"❌ Error resolving username {username}: {e}")
        
        return None
    
    async def check_ads_presence(self, page_id: str) -> bool:
        """Check if a Facebook page has active ads"""
        try:
            print(f"\n{'='*60}")
            print(f"🔍 META ADS DETECTION START for Page ID: {page_id}")
            print(f"{'='*60}")
            
            if not page_id or not page_id.strip():
                print("❌ No page ID provided")
                return False
            
            # Method 1: Direct check (simplest and most reliable)
            print(f"\n📍 Method 1: Direct Ad Library check...")
            has_ads_direct = await self._check_ads_direct(page_id)
            if has_ads_direct:
                print(f"✅ Meta ads FOUND via direct check")
                return True
            
            # Method 2: Check via Ad Library scraping
            print(f"\n📍 Method 2: Ad Library scraping...")
            has_ads_scraping = await self._check_ads_via_scraping(page_id)
            if has_ads_scraping:
                print(f"✅ Meta ads FOUND via scraping")
                return True
            
            # Method 3: Alternative Ad Library search
            print(f"\n📍 Method 3: Alternative search...")
            has_ads_alternative = await self._check_ads_alternative_search(page_id)
            if has_ads_alternative:
                print(f"✅ Meta ads FOUND via alternative")
                return True
            
            # Method 4: Use official API if available
            if self.access_token:
                print(f"\n📍 Method 4: Official API...")
                has_ads_api = await self._check_ads_via_api(page_id)
                if has_ads_api is not None:
                    if has_ads_api:
                        print(f"✅ Meta ads FOUND via API")
                    else:
                        print(f"❌ Meta ads NOT found via API")
                    return has_ads_api
            
            print(f"\n❌ Meta ads NOT FOUND after all methods")
            print(f"{'='*60}\n")
            return False
            
        except Exception as e:
            print(f"❌ Error checking ads presence for page {page_id}: {e}")
            return False
    
    async def _check_ads_direct(self, page_id: str) -> bool:
        """Most direct and simple method to check for Meta ads"""
        try:
            # Use the public API endpoint that returns JSON
            url = f"https://www.facebook.com/ads/library/async/search_ads/"
            params = {
                "q": "",
                "ad_type": "all",
                "search_type": "page",
                "page_ids": page_id,
                "active_status": "active",
                "country": "ALL",
                "media_type": "all"
            }
            
            print(f"Requesting: {url}")
            response = await self.client.get(url, params=params)
            print(f"Status: {response.status_code}, Length: {len(response.text)} bytes")
            
            if response.status_code == 200:
                content = response.text
                
                # Try to parse as JSON
                try:
                    import json
                    data = json.loads(content)
                    
                    # Check various possible structures
                    if isinstance(data, dict):
                        # Look for ads in payload
                        payload = data.get('payload', data)
                        if isinstance(payload, dict):
                            results = payload.get('results', payload.get('ads', payload.get('data', [])))
                            if isinstance(results, list) and len(results) > 0:
                                print(f"✅ Found {len(results)} ads in JSON response")
                                return True
                        
                        # Check for isResultComplete or similar flags
                        if data.get('isResultComplete') is False or data.get('forwardCursor'):
                            # Has pagination, likely has results
                            print(f"✅ Pagination detected, ads likely present")
                            return True
                            
                except json.JSONDecodeError:
                    print(f"Not JSON, checking as HTML...")
                    # If not JSON, check as HTML
                    pass
                
                # Check content for positive indicators
                if 'ad_archive_id' in content or 'snapshot_url' in content:
                    print(f"✅ Ad archive content detected")
                    return True
                
                # Check for explicit "no ads" message
                if len(content) < 500 or 'no results' in content.lower() or '"results":[]' in content:
                    print(f"❌ No ads message or empty results")
                    return False
                    
        except Exception as e:
            print(f"Error in direct check: {e}")
        
        return False
    
    async def _check_ads_via_api(self, page_id: str) -> Optional[bool]:
        """Check ads using official Graph API"""
        try:
            url = f"{self.base_url}/ads_archive"
            params = {
                "search_page_ids": page_id,
                "ad_reached_countries": "ALL",
                "ad_active_status": "ACTIVE",
                "limit": 1,  # Just need to know if any exist
                "access_token": self.access_token
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                ads = data.get("data", [])
                return len(ads) > 0
            
        except Exception as e:
            print(f"Error checking ads via API for page {page_id}: {e}")
        
        return None
    
    async def _check_ads_via_scraping(self, page_id: str) -> bool:
        """Check ads by scraping Ad Library with improved detection"""
        try:
            # Try multiple URL formats for better success rate
            urls_to_try = [
                # Direct API endpoint
                f"https://www.facebook.com/ads/library/async/search/?q=&type=page&page_ids={page_id}&active_status=active&ad_type=all&countries[0]=ALL",
                # Regular library URL
                f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&view_all_page_id={page_id}",
                # Alternative format
                f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&q=&search_type=page&media_type=all&page_ids={page_id}",
            ]
            
            for url in urls_to_try:
                try:
                    print(f"Checking Meta ads for page {page_id} via: {url[:80]}...")
                    response = await self.client.get(url, follow_redirects=True)
                    
                    if response.status_code == 200:
                        content = response.text
                        content_lower = content.lower()
                        
                        # Debug: Check content length
                        print(f"Response length: {len(content)} bytes")
                        
                        # Method 1: Check for JSON data with ads
                        if '"data":' in content or '"payload":' in content:
                            try:
                                import json
                                # Try to find JSON in response
                                json_start = content.find('{')
                                if json_start != -1:
                                    json_content = content[json_start:]
                                    json_end = json_content.rfind('}') + 1
                                    if json_end > 0:
                                        json_str = json_content[:json_end]
                                        data = json.loads(json_str)
                                        
                                        # Check for ads in various structures
                                        if isinstance(data, dict):
                                            ads_data = data.get('data', data.get('payload', {}))
                                            if isinstance(ads_data, list) and len(ads_data) > 0:
                                                print(f"✅ Meta ads found via JSON: {len(ads_data)} ads")
                                                return True
                                            elif isinstance(ads_data, dict):
                                                results = ads_data.get('results', ads_data.get('ads', []))
                                                if results and len(results) > 0:
                                                    print(f"✅ Meta ads found via JSON nested: {len(results)} ads")
                                                    return True
                            except Exception as e:
                                print(f"JSON parsing attempt failed: {e}")
                        
                        # Method 2: Look for strong indicators
                        strong_indicators = [
                            ('"isActive":true', 'Active status flag'),
                            ('"delivery_status":"active"', 'Delivery status'),
                            ('data-ad-id=', 'Ad ID attribute'),
                            ('data-testid="ad_snapshot"', 'Ad snapshot element'),
                            ('"ad_archive_id":', 'Ad archive ID'),
                            ('"snapshot_url":', 'Snapshot URL'),
                            ('class="ad-creative', 'Ad creative class'),
                        ]
                        
                        for indicator, description in strong_indicators:
                            if indicator.lower() in content_lower:
                                print(f"✅ Meta ads found: {description}")
                                return True
                        
                        # Method 3: Count ad-related elements
                        ad_element_count = 0
                        ad_markers = ['ad_id', 'ad_creative', 'ad_snapshot', 'advertiser', 'ad_archive']
                        for marker in ad_markers:
                            ad_element_count += content_lower.count(marker)
                        
                        if ad_element_count > 5:  # Multiple ad elements suggest active ads
                            print(f"✅ Meta ads found: {ad_element_count} ad-related elements")
                            return True
                        
                        # Method 4: Check if page has ads but might be filtered
                        if page_id in content and any(x in content_lower for x in ['ads', 'advertisement', 'sponsored']):
                            # Check if there's actually content (not just "no ads" message)
                            no_ads_indicators = ['no ads', 'no results', 'no advertisements', 'not currently']
                            has_no_ads = any(ind in content_lower for ind in no_ads_indicators)
                            
                            if not has_no_ads and len(content) > 5000:  # Substantial content
                                print(f"✅ Meta ads suspected: Page mentioned with ad context")
                                return True
                    
                    elif response.status_code == 404:
                        print(f"Page {page_id} not found in Ad Library")
                        continue
                    else:
                        print(f"Status {response.status_code} for {url[:80]}")
                        
                except Exception as e:
                    print(f"Error checking URL: {e}")
                    continue
            
        except Exception as e:
            print(f"Error in Meta ads scraping for {page_id}: {e}")
        
        return False
    
    async def _check_ads_alternative_search(self, page_id: str) -> bool:
        """Alternative method using simpler, more reliable detection"""
        try:
            print(f"Trying alternative Meta ads detection for {page_id}")
            
            # Method 1: Try public Ad Library with different parameters
            simple_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&view_all_page_id={page_id}"
            
            try:
                response = await self.client.get(simple_url, follow_redirects=True)
                if response.status_code == 200:
                    content = response.text
                    
                    # Simple but effective checks
                    # If the page loads and has substantial content about ads
                    if len(content) > 10000:  # Substantial page load
                        # Check for specific ad library elements
                        if ('Ad library' in content or 'ads library' in content.lower()):
                            # Check if it's showing actual ads vs "no ads" message
                            has_ads_content = any(x in content for x in [
                                'ad_archive_id', 'ad_snapshot', 'ad_creative',
                                'Started running on', 'Platforms:', 'Advertiser'
                            ])
                            
                            has_no_ads = any(x in content.lower() for x in [
                                'no ads to show', 'no results found', 'no active ads',
                                'this page doesn\'t have ads'
                            ])
                            
                            if has_ads_content and not has_no_ads:
                                print(f"✅ Meta ads detected: Page has active ad content")
                                return True
                            elif has_no_ads:
                                print(f"❌ No Meta ads: Explicitly stated no ads")
                                return False
                        
            except Exception as e:
                print(f"Error in simple check: {e}")
            
            # Method 2: Even simpler - just check if page exists in Ad Library at all
            # Many pages with ads will load something, pages without won't
            minimal_url = f"https://www.facebook.com/ads/library/?id={page_id}"
            try:
                response = await self.client.get(minimal_url, follow_redirects=True)
                if response.status_code == 200 and len(response.text) > 5000:
                    content = response.text.lower()
                    
                    # If page loads with ad-related content and no negative indicators
                    if 'advertiser' in content or 'sponsored' in content or 'ad library' in content:
                        if 'no ads' not in content and 'no results' not in content:
                            print(f"✅ Meta ads suspected: Page exists in Ad Library")
                            return True
                            
            except Exception as e:
                print(f"Error in minimal check: {e}")
                        
        except Exception as e:
            print(f"Error in alternative Meta search for {page_id}: {e}")
        
        return False
    
    async def _get_page_info(self, page_id: str) -> Optional[dict]:
        """Get basic page information"""
        try:
            if self.access_token:
                url = f"{self.base_url}/{page_id}"
                params = {
                    "fields": "name,username,website,category",
                    "access_token": self.access_token
                }
                
                response = await self.client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
            
            # Fallback: try to get info from public page
            page_url = f"https://www.facebook.com/{page_id}"
            response = await self.client.get(page_url)
            
            if response.status_code == 200:
                content = response.text
                
                # Extract page name from HTML
                name_patterns = [
                    r'"name":"([^"]+)"',
                    r'<title>([^<]+)</title>',
                    r'"page_name":"([^"]+)"'
                ]
                
                for pattern in name_patterns:
                    match = re.search(pattern, content)
                    if match:
                        return {"name": match.group(1)}
            
        except Exception as e:
            print(f"Error getting page info for {page_id}: {e}")
        
        return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
