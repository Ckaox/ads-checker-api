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
        """Resolve Facebook username to page ID"""
        try:
            if self.access_token:
                # Use Graph API if we have token
                url = f"{self.base_url}/{username}"
                params = {"access_token": self.access_token}
                
                response = await self.client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("id")
            
            # Fallback: try to extract from public page
            page_url = f"https://www.facebook.com/{username}"
            response = await self.client.get(page_url)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for page ID in various places
                id_patterns = [
                    r'"page_id":"(\d+)"',
                    r'"pageID":"(\d+)"',
                    r'entity_id":"(\d+)"',
                    r'profile_id=(\d+)'
                ]
                
                for pattern in id_patterns:
                    match = re.search(pattern, content)
                    if match:
                        return match.group(1)
            
        except Exception as e:
            print(f"Error resolving username {username}: {e}")
        
        return None
    
    async def check_ads_presence(self, page_id: str) -> bool:
        """Check if a Facebook page has active ads"""
        try:
            # Method 1: Check via Ad Library scraping (most reliable)
            has_ads_scraping = await self._check_ads_via_scraping(page_id)
            if has_ads_scraping:
                return True
            
            # Method 2: Alternative Ad Library search
            has_ads_alternative = await self._check_ads_alternative_search(page_id)
            if has_ads_alternative:
                return True
            
            # Method 3: Use official API if available
            if self.access_token:
                has_ads_api = await self._check_ads_via_api(page_id)
                if has_ads_api is not None:
                    return has_ads_api
            
            return False
            
        except Exception as e:
            print(f"Error checking ads presence for page {page_id}: {e}")
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
        """Check ads by scraping Ad Library"""
        try:
            params = {
                "active_status": "active",
                "ad_type": "all",
                "country": "ALL",
                "search_type": "page",
                "view_all_page_id": page_id
            }
            
            response = await self.client.get(self.ad_library_url, params=params)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for indicators of active ads
                active_indicators = [
                    "active ads", "currently running", "ads are active",
                    '\"active_status\":\"ACTIVE\"', '\"status\":\"ACTIVE\"',
                    "ad_archive_result", "ads_archive",
                    f'page_id\":\"{page_id}\"', f"page_id={page_id}",
                    "advertisement", "sponsored"
                ]
                
                content_lower = content.lower()
                found_indicators = [ind for ind in active_indicators if ind.lower() in content_lower]
                
                if found_indicators:
                    print(f"Meta ads indicators found for {page_id}: {found_indicators[:2]}")
                    return True
                
                # Also check for JSON data structures
                if '\"data\":[' in content and page_id in content:
                    print(f"Meta ads data structure found for {page_id}")
                    return True
            
        except Exception as e:
            print(f"Error scraping ads for page {page_id}: {e}")
        
        return False
    
    async def _check_ads_alternative_search(self, page_id: str) -> bool:
        """Alternative method to check for Meta ads using different approaches"""
        try:
            # Method 1: Direct Ad Library API endpoint
            api_urls = [
                f"https://www.facebook.com/ads/library/api/?search_type=page&search_page_ids={page_id}&active_status=active&ad_type=all&country=ALL",
                f"https://graph.facebook.com/v18.0/ads_archive?search_page_ids={page_id}&ad_active_status=ACTIVE&ad_reached_countries=ALL&limit=1",
                f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&view_all_page_id={page_id}"
            ]
            
            for url in api_urls:
                try:
                    response = await self.client.get(url)
                    if response.status_code == 200:
                        content = response.text
                        content_lower = content.lower()
                        
                        # Look for JSON responses with ads data
                        if '"data":[' in content and len(content) > 100:
                            # Parse potential JSON response
                            try:
                                import json
                                data = json.loads(content)
                                if isinstance(data, dict) and data.get('data'):
                                    ads = data['data']
                                    if isinstance(ads, list) and len(ads) > 0:
                                        print(f"Meta ads found via API for {page_id}: {len(ads)} ads")
                                        return True
                            except:
                                pass
                        
                        # Look for HTML indicators
                        html_indicators = [
                            'data-testid="ad-card"',
                            'aria-label="advertisement"',
                            'class="ad-creative"',
                            '"active_status":"ACTIVE"',
                            '"ad_delivery_status":"active"',
                            'currently running',
                            'ads are active'
                        ]
                        
                        found_html = [ind for ind in html_indicators if ind.lower() in content_lower]
                        if found_html:
                            print(f"Meta ads HTML indicators found for {page_id}: {found_html[:2]}")
                            return True
                        
                except Exception as e:
                    print(f"Error checking alternative URL {url}: {e}")
                    continue
            
            # Method 2: Search by page name/domain if we can resolve it
            try:
                page_info = await self._get_page_info(page_id)
                if page_info and page_info.get('name'):
                    page_name = page_info['name']
                    search_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&q={page_name}"
                    
                    response = await self.client.get(search_url)
                    if response.status_code == 200:
                        content = response.text
                        
                        # Look for the page ID in search results
                        if page_id in content and ('active' in content.lower() or 'running' in content.lower()):
                            print(f"Meta ads found via name search for {page_id} ({page_name})")
                            return True
            except Exception as e:
                print(f"Error in page name search for {page_id}: {e}")
            
        except Exception as e:
            print(f"Error in alternative Meta ads search for {page_id}: {e}")
        
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
