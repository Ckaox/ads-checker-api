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
        Find Facebook page URL from a domain - Enhanced with multiple methods
        """
        try:
            domain = self._clean_domain(domain)
            if not domain:
                return None
            
            print(f"\n🔍 Searching for Facebook page for domain: {domain}")
            
            # Method 1: Check website HTML for Facebook links
            print(f"📍 Method 1: Checking website HTML...")
            for protocol in ["https", "http"]:
                try:
                    url = f"{protocol}://{domain}"
                    response = await self.client.get(url)
                    
                    if response.status_code == 200:
                        facebook_url = await self._extract_facebook_from_html(response.text, domain)
                        if facebook_url:
                            print(f"✅ Found in HTML: {facebook_url}")
                            return facebook_url
                        
                except Exception as e:
                    print(f"Error fetching {protocol}://{domain}: {e}")
                    continue
            
            # Method 2: Search Google for "{domain} facebook"
            print(f"📍 Method 2: Searching Google...")
            facebook_url = await self._search_facebook_via_google(domain)
            if facebook_url:
                print(f"✅ Found via Google: {facebook_url}")
                return facebook_url
            
            # Method 3: Try common Facebook URL patterns
            print(f"📍 Method 3: Trying common patterns...")
            facebook_url = await self._try_common_facebook_patterns(domain)
            if facebook_url:
                print(f"✅ Found via pattern: {facebook_url}")
                return facebook_url
            
            print(f"❌ No Facebook page found for {domain}")
            return None
            
        except Exception as e:
            print(f"❌ Error resolving Facebook page for domain {domain}: {e}")
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
    
    async def _search_facebook_via_google(self, domain: str) -> Optional[str]:
        """Search Google for Facebook page of the domain"""
        try:
            # Extract brand name from domain
            brand = domain.split('.')[0]
            
            # Search queries to try
            queries = [
                f"{domain} facebook",
                f"{brand} facebook page",
                f'site:facebook.com "{brand}"'
            ]
            
            for query in queries:
                try:
                    search_url = "https://www.google.com/search"
                    params = {
                        "q": query,
                        "hl": "en"
                    }
                    
                    response = await self.client.get(search_url, params=params)
                    
                    if response.status_code == 200:
                        # Look for Facebook URLs in search results
                        facebook_urls = re.findall(
                            r'(https?://(?:www\.)?facebook\.com/[a-zA-Z0-9._-]+)/?',
                            response.text
                        )
                        
                        for url in facebook_urls:
                            # Clean and validate
                            clean_url = self._extract_facebook_url(url)
                            if clean_url and self._is_valid_facebook_page(clean_url):
                                # Verify it's not a generic/unrelated page
                                if brand.lower() in clean_url.lower() or await self._verify_facebook_page_matches_domain(clean_url, domain):
                                    return clean_url
                
                except Exception as e:
                    print(f"Error searching Google with query '{query}': {e}")
                    continue
            
        except Exception as e:
            print(f"Error in Google search: {e}")
        
        return None
    
    async def _try_common_facebook_patterns(self, domain: str) -> Optional[str]:
        """Try common Facebook URL patterns based on domain"""
        try:
            brand = domain.split('.')[0]
            
            # Common patterns
            patterns = [
                f"https://www.facebook.com/{brand}",
                f"https://www.facebook.com/{brand.capitalize()}",
                f"https://www.facebook.com/{brand.upper()}",
                f"https://www.facebook.com/{brand.replace('-', '')}",
                f"https://www.facebook.com/{brand.replace('_', '')}",
                f"https://www.facebook.com/{domain.replace('.', '')}",
            ]
            
            for pattern_url in patterns:
                try:
                    response = await self.client.get(pattern_url)
                    
                    # If page exists and looks valid (not redirect to home, not 404)
                    if response.status_code == 200:
                        # Check if it's actually a page and not Facebook home
                        if "facebook.com/login" not in response.url.path and \
                           "Page Not Found" not in response.text:
                            return pattern_url
                
                except Exception:
                    continue
            
        except Exception as e:
            print(f"Error trying common patterns: {e}")
        
        return None
    
    async def _verify_facebook_page_matches_domain(self, facebook_url: str, domain: str) -> bool:
        """Verify that a Facebook page actually belongs to the domain"""
        try:
            # Fetch the Facebook page
            response = await self.client.get(facebook_url)
            
            if response.status_code == 200:
                html = response.text.lower()
                domain_lower = domain.lower()
                
                # Check if domain is mentioned in the page
                if domain_lower in html:
                    return True
                
                # Check if domain is in website link
                website_match = re.search(r'(?:website|site).*?href="([^"]*)"', html, re.IGNORECASE)
                if website_match:
                    website = website_match.group(1).lower()
                    if domain_lower in website:
                        return True
            
        except Exception:
            pass
        
        return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
