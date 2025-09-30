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
            if self.access_token:
                # Method 1: Use official API
                has_ads_api = await self._check_ads_via_api(page_id)
                if has_ads_api is not None:
                    return has_ads_api
            
            # Method 2: Check via Ad Library scraping
            return await self._check_ads_via_scraping(page_id)
            
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
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
