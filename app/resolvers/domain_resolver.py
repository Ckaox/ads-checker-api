"""
Domain resolver for mapping between domains and Facebook pages
"""
import re
import httpx
from typing import Optional
from urllib.parse import urlparse, urljoin
from selectolax.parser import HTMLParser

from app.core.config import settings

class DomainResolver:
    """Resolver for mapping domains to Facebook pages and vice versa"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize domain"""
        if not domain:
            return ""
        
        # Remove protocol if present
        if "://" in domain:
            parsed = urlparse(domain)
            domain = parsed.netloc or domain
        
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain.lower().strip()
    
    def _extract_facebook_url(self, url: str) -> Optional[str]:
        """Extract and normalize Facebook URL"""
        if not url or "facebook.com" not in url.lower():
            return None
        
        # Clean up the URL
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # Parse and clean Facebook URL
        try:
            parsed = urlparse(url)
            if "facebook.com" in parsed.netloc.lower():
                # Remove query parameters and fragments for cleaner URL
                clean_path = parsed.path.rstrip('/')
                return f"https://facebook.com{clean_path}"
        except:
            pass
        
        return None
    
    async def domain_to_facebook(self, domain: str) -> Optional[str]:
        """
        Find Facebook page URL from a domain
        """
        try:
            domain = self._clean_domain(domain)
            if not domain:
                return None
            
            # Try both protocols
            for protocol in ["https", "http"]:
                try:
                    url = f"{protocol}://{domain}"
                    response = await self.client.get(url)
                    
                    if response.status_code == 200:
                        facebook_url = await self._extract_facebook_from_html(response.text, domain)
                        if facebook_url:
                            return facebook_url
                        
                except Exception as e:
                    print(f"Error fetching {protocol}://{domain}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error resolving Facebook page for domain {domain}: {e}")
            return None
    
    async def _extract_facebook_from_html(self, html: str, domain: str) -> Optional[str]:
        """Extract Facebook page URL from HTML content"""
        try:
            parser = HTMLParser(html)
            
            # Method 1: Look for Facebook links in common locations
            facebook_patterns = [
                # Direct links
                'a[href*="facebook.com"]',
                'a[href*="fb.com"]',
                # Social media sections
                '.social a[href*="facebook"]',
                '.social-media a[href*="facebook"]',
                '.footer a[href*="facebook"]',
                # Meta tags
                'meta[property="og:url"][content*="facebook"]',
                'meta[name="facebook"][content]',
            ]
            
            for pattern in facebook_patterns:
                elements = parser.css(pattern)
                for element in elements:
                    # Get URL from href or content attribute
                    url = element.attributes.get("href") or element.attributes.get("content")
                    if url:
                        facebook_url = self._extract_facebook_url(url)
                        if facebook_url and self._is_valid_facebook_page(facebook_url):
                            return facebook_url
            
            # Method 2: Search in text content for Facebook URLs
            facebook_urls = re.findall(
                r'https?://(?:www\.)?(?:facebook\.com|fb\.com)/[^\s<>"\']+',
                html,
                re.IGNORECASE
            )
            
            for url in facebook_urls:
                facebook_url = self._extract_facebook_url(url)
                if facebook_url and self._is_valid_facebook_page(facebook_url):
                    return facebook_url
            
            # Method 3: Look for Facebook widget or plugin code
            if "facebook.com" in html.lower():
                # Look for Facebook page plugin or social plugin code
                fb_plugin_patterns = [
                    r'data-href=["\']([^"\']*facebook\.com[^"\']*)["\']',
                    r'fb-page[^>]*data-href=["\']([^"\']*)["\']',
                    r'facebook\.com/plugins/page\.php\?href=([^&"\']*)',
                ]
                
                for pattern in fb_plugin_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        facebook_url = self._extract_facebook_url(match)
                        if facebook_url and self._is_valid_facebook_page(facebook_url):
                            return facebook_url
            
            return None
            
        except Exception as e:
            print(f"Error extracting Facebook URL from HTML: {e}")
            return None
    
    def _is_valid_facebook_page(self, url: str) -> bool:
        """Check if the Facebook URL looks like a valid page URL"""
        if not url:
            return False
        
        # Parse URL
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Skip certain paths that are not page URLs
            invalid_paths = [
                "/login", "/register", "/privacy", "/terms",
                "/help", "/support", "/sharer", "/dialog",
                "/tr", "/plugins", "/share", "/like"
            ]
            
            for invalid_path in invalid_paths:
                if invalid_path in path:
                    return False
            
            # Valid page patterns
            valid_patterns = [
                r"^/[a-zA-Z0-9._-]+/?$",  # Simple username
                r"^/pages/[^/]+/\d+/?$",   # Pages with ID
                r"^/profile\.php\?id=\d+", # Profile with numeric ID
            ]
            
            return any(re.match(pattern, path) for pattern in valid_patterns)
            
        except:
            return False
    
    async def facebook_to_domain(self, facebook_page: str) -> Optional[str]:
        """
        Find domain from a Facebook page
        """
        try:
            # Clean Facebook URL
            facebook_url = self._extract_facebook_url(facebook_page)
            if not facebook_url:
                return None
            
            # Fetch Facebook page
            response = await self.client.get(facebook_url)
            if response.status_code != 200:
                return None
            
            return await self._extract_domain_from_facebook_html(response.text)
            
        except Exception as e:
            print(f"Error resolving domain from Facebook page {facebook_page}: {e}")
            return None
    
    async def _extract_domain_from_facebook_html(self, html: str) -> Optional[str]:
        """Extract domain from Facebook page HTML"""
        try:
            parser = HTMLParser(html)
            
            # Method 1: Look for website links in About section or page info
            website_patterns = [
                # Direct website links
                'a[href]:not([href*="facebook.com"]):not([href*="instagram.com"]):not([href*="twitter.com"])',
                # About section links
                '.about a[href^="http"]',
                '.page-info a[href^="http"]',
                # Meta tags
                'meta[property="og:url"][content]',
                'link[rel="canonical"][href]'
            ]
            
            for pattern in website_patterns:
                elements = parser.css(pattern)
                for element in elements:
                    url = element.attributes.get("href") or element.attributes.get("content")
                    if url and self._is_external_website(url):
                        domain = self._extract_domain_from_url(url)
                        if domain:
                            return domain
            
            # Method 2: Search in text content for website URLs
            website_urls = re.findall(
                r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                html,
                re.IGNORECASE
            )
            
            for url in website_urls:
                if self._is_external_website(f"https://{url}"):
                    return self._clean_domain(url)
            
            return None
            
        except Exception as e:
            print(f"Error extracting domain from Facebook HTML: {e}")
            return None
    
    def _is_external_website(self, url: str) -> bool:
        """Check if URL is an external website (not social media)"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Skip social media and other non-business domains
            social_domains = [
                "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
                "youtube.com", "tiktok.com", "snapchat.com", "pinterest.com",
                "whatsapp.com", "telegram.org", "discord.com"
            ]
            
            return not any(social in domain for social in social_domains)
            
        except:
            return False
    
    def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract clean domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            
            return domain.lower() if domain else None
            
        except:
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
