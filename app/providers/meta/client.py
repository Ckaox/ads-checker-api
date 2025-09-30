"""
Meta (Facebook) Ads client for checking ad presence and retrieving ad data
"""
import re
import httpx
from typing import List, Optional
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from app.core.config import settings
from app.schemas.ads import AdItem
from app.providers.meta.honest_extractor import HonestMetaExtractor

class MetaClient:
    """Client for Meta Ad Library and Facebook Graph API"""
    
    def __init__(self):
        self.access_token = settings.META_ACCESS_TOKEN
        self.base_url = "https://graph.facebook.com/v18.0"
        self.ad_library_url = "https://www.facebook.com/ads/library"
        
        # HTTP client with timeout and retries
        self.client = httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def get_page_id(self, facebook_page: str) -> Optional[str]:
        """
        Extract or resolve Facebook Page ID from URL or username
        """
        try:
            # If it's already a numeric ID
            if facebook_page.isdigit():
                return facebook_page
            
            # Extract from URL patterns
            if "facebook.com" in facebook_page:
                # Handle various Facebook URL formats
                patterns = [
                    r"facebook\.com/([^/?]+)",
                    r"facebook\.com/pages/[^/]+/(\d+)",
                    r"facebook\.com/profile\.php\?id=(\d+)"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, facebook_page)
                    if match:
                        page_identifier = match.group(1)
                        
                        # If it's numeric, it's likely the page ID
                        if page_identifier.isdigit():
                            return page_identifier
                        
                        # Otherwise, try to resolve username to ID via Graph API
                        if self.access_token:
                            return await self._resolve_username_to_id(page_identifier)
                        
                        # Fallback: return the username for scraping
                        return page_identifier
            
            # If no URL pattern matched, treat as username
            if self.access_token:
                return await self._resolve_username_to_id(facebook_page)
            
            return facebook_page
            
        except Exception as e:
            print(f"Error extracting page ID from {facebook_page}: {e}")
            return None
    
    async def _resolve_username_to_id(self, username: str) -> Optional[str]:
        """Resolve Facebook username to page ID using Graph API"""
        if not self.access_token:
            return None
        
        try:
            url = f"{self.base_url}/{username}"
            params = {
                "fields": "id,name",
                "access_token": self.access_token
            }
            
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("id")
            
        except Exception as e:
            print(f"Error resolving username {username}: {e}")
        
        return None
    
    async def has_active_ads(self, page_id: str) -> bool:
        """
        Check if a Facebook page has active ads
        """
        try:
            # Try Graph API first if we have token
            if self.access_token:
                return await self._check_ads_via_api(page_id)
            
            # Fallback to Ad Library scraping
            return await self._check_ads_via_scraping(page_id)
            
        except Exception as e:
            print(f"Error checking active ads for page {page_id}: {e}")
            return False
    
    async def _check_ads_via_api(self, page_id: str) -> bool:
        """Check ads using Graph API (requires valid token)"""
        try:
            # Use Ad Library API endpoint
            url = f"{self.base_url}/ads_archive"
            params = {
                "search_page_ids": page_id,
                "ad_reached_countries": "ALL",
                "ad_active_status": "ACTIVE",
                "limit": 1,
                "access_token": self.access_token
            }
            
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return len(data.get("data", [])) > 0
            
        except Exception as e:
            print(f"Error checking ads via API for page {page_id}: {e}")
        
        return False
    
    async def _check_ads_via_scraping(self, page_id: str) -> bool:
        """Check ads by scraping Ad Library (improved method)"""
        try:
            # Try multiple Ad Library URLs
            ad_library_urls = [
                "https://www.facebook.com/ads/library",
                "https://adslibrary.facebook.com",
                "https://www.facebook.com/ads/library/api"
            ]
            
            for base_url in ad_library_urls:
                try:
                    params = {
                        "active_status": "active",
                        "ad_type": "all",
                        "country": "ALL",
                        "search_type": "page",
                        "view_all_page_id": page_id
                    }
                    
                    response = await self.client.get(base_url, params=params)
                    if response.status_code == 200:
                        content = response.text
                        
                        # Improved indicators with more patterns
                        active_indicators = [
                            "active ads", "currently running", "ads are active",
                            '"active_status":"ACTIVE"', '"status":"ACTIVE"',
                            "ad_archive_result", "ads_archive",
                            f'page_id":"{page_id}"', f"page_id={page_id}",
                            "Ad Library", "ads library", "advertisement",
                            "sponsored", "promoted", "boosted post"
                        ]
                        
                        content_lower = content.lower()
                        found_indicators = [ind for ind in active_indicators if ind.lower() in content_lower]
                        
                        if found_indicators:
                            print(f"Meta ads indicators found for {page_id}: {found_indicators[:3]}")
                            return True
                        
                        # Also check for JSON data structures
                        if '"data":[' in content and page_id in content:
                            print(f"Meta ads data structure found for {page_id}")
                            return True
                    
                except Exception as e:
                    print(f"Error with Ad Library URL {base_url}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error scraping ads for page {page_id}: {e}")
        
        return False
    
    async def get_active_ads_count(self, page_id: str) -> int:
        """Get count of active ads for a page"""
        try:
            if self.access_token:
                return await self._get_ads_count_via_api(page_id)
            
            # Fallback to scraping (less reliable for exact counts)
            return await self._get_ads_count_via_scraping(page_id)
            
        except Exception as e:
            print(f"Error getting ads count for page {page_id}: {e}")
            return 0
    
    async def _get_ads_count_via_api(self, page_id: str) -> int:
        """Get ads count using Graph API"""
        try:
            url = f"{self.base_url}/ads_archive"
            params = {
                "search_page_ids": page_id,
                "ad_reached_countries": "ALL",
                "ad_active_status": "ACTIVE",
                "limit": 100,  # Get more to count
                "access_token": self.access_token
            }
            
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return len(data.get("data", []))
            
        except Exception as e:
            print(f"Error getting ads count via API: {e}")
        
        return 0
    
    async def _get_ads_count_via_scraping(self, page_id: str) -> int:
        """Get ads count via scraping (approximate)"""
        # This is a simplified implementation
        # In practice, you'd need to parse the HTML more carefully
        has_ads = await self._check_ads_via_scraping(page_id)
        return 1 if has_ads else 0  # Simplified: return 1 if any ads found
    
    async def get_latest_ads(self, page_id: str, limit: int = 5) -> List[AdItem]:
        """Get latest ads for a page using honest extraction methods"""
        try:
            # Use the honest ads extractor (no fake content)
            extractor = HonestMetaExtractor(access_token=self.access_token)
            
            try:
                real_ads = await extractor.extract_honest_ads(page_id, limit)
                if real_ads:
                    print(f"Successfully extracted {len(real_ads)} real Meta ads for {page_id}")
                    return real_ads
                else:
                    print(f"No real Meta ads could be extracted for {page_id}")
                    return []
            finally:
                await extractor.close()
            
        except Exception as e:
            print(f"Error getting latest ads for page {page_id}: {e}")
            return []
    
    async def _get_latest_ads_via_api(self, page_id: str, limit: int) -> List[AdItem]:
        """Get latest ads using Graph API"""
        try:
            url = f"{self.base_url}/ads_archive"
            params = {
                "search_page_ids": page_id,
                "ad_reached_countries": "ALL",
                "ad_active_status": "ACTIVE",
                "limit": limit,
                "fields": "id,ad_creative_bodies,ad_creative_link_captions,ad_creative_link_titles,ad_delivery_start_time",
                "access_token": self.access_token
            }
            
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                ads = []
                
                for ad_data in data.get("data", []):
                    # Extract ad information
                    title = ""
                    body = ""
                    
                    # Get title from various fields
                    if "ad_creative_link_titles" in ad_data:
                        titles = ad_data["ad_creative_link_titles"]
                        if titles:
                            title = titles[0]
                    
                    # Get body from various fields
                    if "ad_creative_bodies" in ad_data:
                        bodies = ad_data["ad_creative_bodies"]
                        if bodies:
                            body = bodies[0]
                    elif "ad_creative_link_captions" in ad_data:
                        captions = ad_data["ad_creative_link_captions"]
                        if captions:
                            body = captions[0]
                    
                    # Parse creation date
                    created_at = None
                    if "ad_delivery_start_time" in ad_data:
                        try:
                            created_at = datetime.fromisoformat(
                                ad_data["ad_delivery_start_time"].replace("Z", "+00:00")
                            )
                        except:
                            pass
                    
                    ad_item = AdItem(
                        platform="meta",
                        title=title or "No title available",
                        body=body or "No description available",
                        ad_type="image",  # Default, could be enhanced
                        created_at=created_at,
                        ad_id=ad_data.get("id")
                    )
                    ads.append(ad_item)
                
                return ads
            
        except Exception as e:
            print(f"Error getting latest ads via API: {e}")
        
        return []
    
    async def _get_latest_ads_via_scraping(self, page_id: str, limit: int) -> List[AdItem]:
        """Get latest ads via scraping (simplified implementation)"""
        # This would require more complex HTML parsing
        # For now, return mock data if ads are detected
        has_ads = await self._check_ads_via_scraping(page_id)
        
        if has_ads:
            return [
                AdItem(
                    platform="meta",
                    title="Sample Meta Ad",
                    body="This is a sample ad detected via scraping",
                    ad_type="image",
                    created_at=datetime.utcnow(),
                    ad_id=f"scraped_{page_id}_1"
                )
            ]
        
        return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
