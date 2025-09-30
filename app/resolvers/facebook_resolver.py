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
        Extract Meta page ID from Facebook URL
        """
        try:
            # Try to extract from URL patterns first
            page_id = self._extract_page_id_from_url(facebook_url)
            if page_id:
                return page_id
            
            # If not found in URL, try scraping the page
            clean_url = self._clean_facebook_url(facebook_url)
            if not clean_url:
                return None
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(clean_url)
                response.raise_for_status()
                
                # Look for page ID in HTML content
                page_id = self._extract_page_id_from_html(response.text)
                return page_id
                
        except Exception as e:
            print(f"Error extracting page ID from {facebook_url}: {e}")
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
    
    def _extract_page_id_from_url(self, url: str) -> Optional[str]:
        """Extract page ID from Facebook URL patterns"""
        
        # Pattern for direct page ID URLs
        patterns = [
            r'facebook\.com/pages/[^/]+/(\d+)',
            r'facebook\.com/profile\.php\?id=(\d+)',
            r'"page_id":"(\d+)"',
            r'pageID=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_page_id_from_html(self, html_content: str) -> Optional[str]:
        """Extract page ID from HTML content"""
        
        # Look for page ID in various HTML patterns
        patterns = [
            r'"page_id":"(\d+)"',
            r'"pageID":"(\d+)"',
            r'pageID=(\d+)',
            r'"entity_id":"(\d+)"',
            r'data-page-id="(\d+)"',
            r'"id":"(\d+)".*?"__typename":"Page"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                page_id = match.group(1)
                # Validate that it looks like a page ID (numeric, reasonable length)
                if page_id.isdigit() and 8 <= len(page_id) <= 20:
                    return page_id
        
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
