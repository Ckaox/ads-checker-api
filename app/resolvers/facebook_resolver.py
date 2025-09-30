"""
Facebook page resolver for finding domains and extracting page IDs
"""
import re
import httpx
from typing import Optional
from urllib.parse import urlparse, urljoin
from selectolax.parser import HTMLParser

from app.core.config import settings


class FacebookResolver:
    """Resolver for Facebook page operations"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(settings.HTTP_TIMEOUT)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def find_website_from_page(self, facebook_url: str) -> Optional[str]:
        """
        Extract website domain from Facebook page
        """
        try:
            # Clean and validate Facebook URL
            clean_url = self._clean_facebook_url(facebook_url)
            if not clean_url:
                return None
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(clean_url)
                response.raise_for_status()
                
                # Parse HTML content
                parser = HTMLParser(response.text)
                
                # Look for website links in various places
                website = self._extract_website_from_html(parser)
                
                if website:
                    return self._clean_domain(website)
                
                return None
                
        except Exception as e:
            print(f"Error finding website from Facebook page {facebook_url}: {e}")
            return None
    
    async def extract_page_id(self, facebook_url: str) -> Optional[str]:
        """
        Extract Meta page ID from Facebook URL - Enhanced version
        """
        try:
            print(f"\n🔍 Extracting Page ID from: {facebook_url}")
            
            # Method 1: Try to extract from URL patterns first (quickest)
            page_id = self._extract_page_id_from_url(facebook_url)
            if page_id:
                print(f"✅ Page ID extracted from URL: {page_id}")
                return page_id
            
            # Method 2: Try Graph API lookup (if we can extract username)
            page_id = await self._try_graph_api_lookup(facebook_url)
            if page_id:
                print(f"✅ Page ID from Graph API: {page_id}")
                return page_id
            
            # Method 3: Scrape the page HTML
            clean_url = self._clean_facebook_url(facebook_url)
            if not clean_url:
                print(f"❌ Could not clean Facebook URL")
                return None
            
            print(f"Fetching page: {clean_url}")
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(clean_url)
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Look for page ID in HTML content
                    page_id = self._extract_page_id_from_html(response.text)
                    if page_id:
                        print(f"✅ Page ID extracted from HTML: {page_id}")
                        return page_id
                    
                    # Method 4: Try alternative HTML patterns
                    page_id = self._extract_page_id_alternative(response.text)
                    if page_id:
                        print(f"✅ Page ID from alternative patterns: {page_id}")
                        return page_id
            
            print(f"❌ Could not extract Page ID from any method")
            return None
                
        except Exception as e:
            print(f"❌ Error extracting page ID from {facebook_url}: {e}")
            return None
    
    def _clean_facebook_url(self, url: str) -> Optional[str]:
        """Clean and validate Facebook URL"""
        if not url:
            return None
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse URL
        parsed = urlparse(url)
        
        # Check if it's a Facebook URL
        if 'facebook.com' not in parsed.netloc:
            return None
        
        # Clean the path
        path = parsed.path.strip('/')
        if not path:
            return None
        
        # Construct clean URL
        return f"https://www.facebook.com/{path}"
    
    def _extract_website_from_html(self, parser: HTMLParser) -> Optional[str]:
        """Extract website URL from Facebook page HTML"""
        
        # Look for website links in various selectors
        selectors = [
            'a[href*="http"]:not([href*="facebook.com"])',
            '[data-testid="page_website"] a',
            '.about a[href*="http"]:not([href*="facebook.com"])',
            '.contact-info a[href*="http"]:not([href*="facebook.com"])'
        ]
        
        for selector in selectors:
            links = parser.css(selector)
            for link in links:
                href = link.attributes.get('href', '')
                if href and self._is_valid_website_url(href):
                    return href
        
        # Look in text content for URLs
        text_content = parser.text()
        urls = re.findall(r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_content)
        for url in urls:
            if not any(social in url.lower() for social in ['facebook', 'instagram', 'twitter', 'linkedin']):
                return f"https://{url}"
        
        return None
    
    async def _try_graph_api_lookup(self, facebook_url: str) -> Optional[str]:
        """Try to get page ID using Graph API (public data, no token needed)"""
        try:
            # Extract username from URL
            username = self._extract_username_from_url(facebook_url)
            if not username:
                return None
            
            print(f"Trying Graph API lookup for username: {username}")
            
            # Use Graph API v18.0 - public data doesn't need token for basic info
            api_url = f"https://graph.facebook.com/v18.0/{username}"
            params = {
                "fields": "id",
                "access_token": ""  # Try without token first (public pages)
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try without token
                response = await client.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data:
                        return data['id']
        
        except Exception as e:
            print(f"Graph API lookup failed: {e}")
        
        return None
    
    def _extract_username_from_url(self, url: str) -> Optional[str]:
        """Extract username/page name from Facebook URL"""
        try:
            # Clean URL first
            url = self._clean_facebook_url(url)
            if not url:
                return None
            
            # Parse URL
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            # Remove common prefixes
            path = re.sub(r'^(www\.)?facebook\.com/', '', path)
            
            # Split and get first part (username)
            parts = path.split('/')
            if parts:
                username = parts[0]
                # Filter out invalid usernames
                if username and username not in ['pages', 'profile.php', 'groups']:
                    return username
        
        except Exception as e:
            print(f"Error extracting username: {e}")
        
        return None
    
    def _extract_page_id_from_url(self, url: str) -> Optional[str]:
        """Extract page ID from Facebook URL patterns"""
        
        # Pattern for direct page ID URLs
        patterns = [
            r'facebook\.com/pages/[^/]+/(\d+)',
            r'facebook\.com/profile\.php\?id=(\d+)',
            r'[?&]id=(\d+)',
            r'pageID[=:](\d+)',
            r'page_id[=:](\d+)',
            r'/(\d{10,})(?:/|$)',  # 10+ digit number in path
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                page_id = match.group(1)
                # Validate it looks like a page ID (8-20 digits)
                if page_id.isdigit() and 8 <= len(page_id) <= 20:
                    return page_id
        
        return None
    
    def _extract_page_id_from_html(self, html_content: str) -> Optional[str]:
        """Extract page ID from HTML content"""
        
        # Look for page ID in various HTML patterns
        patterns = [
            r'"page_id":"(\d+)"',
            r'"pageID":"(\d+)"',
            r'pageID[=:](\d+)',
            r'"entity_id":"(\d+)"',
            r'data-page-id="(\d+)"',
            r'"id":"(\d+)"[^}]*?"__typename":"Page"',
            r'"pageid":"(\d+)"',
            r'page_id[=:](\d+)',
            r'"pageId":"(\d+)"',
            r'fb://page/(\d+)',
            r'"userID":"(\d+)"',  # Sometimes it's called userID
            r'"user_id":"(\d+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                page_id = match.group(1)
                # Validate that it looks like a page ID (numeric, reasonable length)
                if page_id.isdigit() and 8 <= len(page_id) <= 20:
                    print(f"Found page ID with pattern: {pattern[:30]}...")
                    return page_id
        
        return None
    
    def _extract_page_id_alternative(self, html_content: str) -> Optional[str]:
        """Alternative method to extract page ID using different approaches"""
        try:
            # Method 1: Look for page ID in JSON-LD or structured data
            json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
            json_matches = re.findall(json_ld_pattern, html_content, re.DOTALL)
            
            for json_str in json_matches:
                try:
                    import json
                    data = json.loads(json_str)
                    # Look for Facebook page ID in various fields
                    if isinstance(data, dict):
                        for key in ['@id', 'identifier', 'sameAs']:
                            value = data.get(key, '')
                            if isinstance(value, str) and 'facebook.com' in value:
                                page_id = self._extract_page_id_from_url(value)
                                if page_id:
                                    return page_id
                except:
                    pass
            
            # Method 2: Look for page ID in meta tags
            meta_patterns = [
                r'<meta[^>]*property="fb:page_id"[^>]*content="(\d+)"',
                r'<meta[^>]*property="al:ios:url"[^>]*content="[^"]*?(\d{10,})',
                r'<meta[^>]*property="al:android:url"[^>]*content="[^"]*?(\d{10,})',
            ]
            
            for pattern in meta_patterns:
                match = re.search(pattern, html_content)
                if match:
                    page_id = match.group(1)
                    if page_id.isdigit() and 8 <= len(page_id) <= 20:
                        print(f"Found page ID in meta tag")
                        return page_id
            
            # Method 3: Look for page ID in any large JSON blob
            # Find all potential JSON objects
            json_pattern = r'\{[^{}]*"(?:page_?id|pageID|entity_id)"[^{}]*\}'
            json_matches = re.findall(json_pattern, html_content, re.IGNORECASE)
            
            for json_str in json_matches:
                try:
                    import json
                    data = json.loads(json_str)
                    for key in ['page_id', 'pageID', 'pageid', 'entity_id', 'id']:
                        if key in data:
                            page_id = str(data[key])
                            if page_id.isdigit() and 8 <= len(page_id) <= 20:
                                return page_id
                except:
                    # Try regex on the string
                    id_match = re.search(r'"(?:page_?id|pageID)"[:\s]*"?(\d+)"?', json_str, re.IGNORECASE)
                    if id_match:
                        page_id = id_match.group(1)
                        if page_id.isdigit() and 8 <= len(page_id) <= 20:
                            return page_id
            
            # Method 4: Look for numeric IDs in obvious places (last resort)
            # Look for patterns like "fbid":123456789
            fbid_pattern = r'(?:fbid|fb_id)["\s:]+(\d{8,20})'
            match = re.search(fbid_pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)
                
        except Exception as e:
            print(f"Error in alternative extraction: {e}")
        
        return None
    
    def _is_valid_website_url(self, url: str) -> bool:
        """Check if URL is a valid website (not social media)"""
        if not url:
            return False
        
        # Skip social media URLs
        social_domains = [
            'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com',
            'youtube.com', 'tiktok.com', 'snapchat.com', 'pinterest.com'
        ]
        
        for domain in social_domains:
            if domain in url.lower():
                return False
        
        # Check if it's a proper HTTP URL
        return url.startswith(('http://', 'https://'))
    
    def _clean_domain(self, url: str) -> str:
        """Extract clean domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
        except:
            return url
