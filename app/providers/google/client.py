"""
Google Ads client for checking ad presence and retrieving ad data
"""
import re
import httpx
from typing import List, Optional
from datetime import datetime
from urllib.parse import quote, urlparse
from selectolax.parser import HTMLParser

from app.core.config import settings
from app.schemas.ads import AdItem
from app.providers.google.honest_extractor import HonestGoogleExtractor

class GoogleClient:
    """Client for Google Ads Transparency Center and related services"""
    
    def __init__(self):
        self.transparency_center_url = "https://adstransparency.google.com"
        
        # HTTP client with realistic headers
        self.client = httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize domain name"""
        if not domain:
            return ""
        
        # Remove protocol if present
        if "://" in domain:
            domain = urlparse(domain).netloc or domain
        
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Remove trailing slash
        domain = domain.rstrip("/")
        
        return domain.lower()
    
    async def has_active_ads(self, domain: str) -> bool:
        """
        Check if a domain has active Google Ads
        """
        try:
            domain = self._clean_domain(domain)
            if not domain:
                return False
            
            # Method 1: Check Google Ads Transparency Center
            transparency_result = await self._check_transparency_center(domain)
            if transparency_result:
                return True
            
            # Method 2: Check for Google Ads signals on the website
            website_signals = await self._check_website_signals(domain)
            
            return website_signals
            
        except Exception as e:
            print(f"Error checking Google Ads for domain {domain}: {e}")
            return False
    
    async def _check_transparency_center(self, domain: str) -> bool:
        """Check Google Ads Transparency Center for active ads (improved)"""
        try:
            # Try multiple transparency center approaches
            search_terms = [domain, domain.replace('.com', ''), domain.split('.')[0]]
            
            # Updated transparency center URLs
            base_urls = [
                "https://adstransparency.google.com",
                "https://transparencyreport.google.com/political-ads",
                "https://ads.google.com/transparency"
            ]
            
            for base_url in base_urls:
                for term in search_terms:
                    try:
                        search_url = f"{base_url}/advertiser" if "/advertiser" not in base_url else base_url
                        params = {"q": term}
                        
                        response = await self.client.get(search_url, params=params)
                        print(f"Transparency check for '{term}' at {base_url}: {response.status_code}")
                        
                        if response.status_code == 200:
                            content = response.text
                            parser = HTMLParser(content)
                            
                            # Updated selectors for current Google structure
                            selectors = [
                                "[data-advertiser-id]", ".advertiser-card", ".advertiser-result",
                                "[href*='/advertiser/']", ".search-result", ".ad-result",
                                "[data-ad-id]", ".transparency-result"
                            ]
                            
                            for selector in selectors:
                                elements = parser.css(selector)
                                if elements:
                                    for element in elements:
                                        text = element.text().lower()
                                        if domain.lower() in text or term.lower() in text:
                                            print(f"Google ads found via transparency: {text[:100]}")
                                            return True
                            
                            # Check content for indicators
                            content_lower = content.lower()
                            indicators = [
                                "active ads", "currently running", "ads running",
                                f"{domain} ads", f"{term} advertiser",
                                "advertisement", "sponsored content"
                            ]
                            
                            found = [ind for ind in indicators if ind in content_lower]
                            if found:
                                print(f"Google ads indicators found: {found[:2]}")
                                return True
                        
                    except Exception as e:
                        print(f"Error checking {base_url} for {term}: {e}")
                        continue
            
        except Exception as e:
            print(f"Error checking transparency center for {domain}: {e}")
        
        return False
    
    async def _check_website_signals(self, domain: str) -> bool:
        """Check the website itself for Google Ads signals"""
        try:
            # Try both http and https
            for protocol in ["https", "http"]:
                try:
                    url = f"{protocol}://{domain}"
                    response = await self.client.get(url, follow_redirects=True)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Comprehensive Google Ads signals detection
                        google_ads_signals = {
                            "Google Tag Manager": ["googletag.cmd", "gtag(", "gtm.js"],
                            "Google Ads Scripts": ["googleadservices.com", "googlesyndication.com"],
                            "AdSense": ["google_ad_client", "adsbygoogle", "data-ad-client"],
                            "DoubleClick": ["doubleclick.net", "googleads.g.doubleclick"],
                            "Google Analytics Enhanced": ["gtag('config', 'AW-", "google_conversion_id"],
                            "Remarketing": ["google_remarketing_only", "google_conversion_label"],
                            "Shopping Ads": ["merchant_id", "google_business_vertical"],
                            "Display Network": ["googlesyndication.com/pagead", "partner.googleadservices.com"],
                            "YouTube Ads": ["youtube.com/embed", "googlevideo.com"]
                        }
                        
                        content_lower = content.lower()
                        found_signals = []
                        
                        for category, patterns in google_ads_signals.items():
                            for pattern in patterns:
                                if pattern.lower() in content_lower:
                                    found_signals.append(f"{category}: {pattern}")
                        
                        if found_signals:
                            print(f"Google Ads signals found for {domain}: {found_signals[:3]}")
                            # If we find multiple categories or strong indicators, likely running ads
                            return len(found_signals) >= 2 or any("conversion" in signal.lower() for signal in found_signals)
                        
                except Exception:
                    continue  # Try next protocol
            
        except Exception as e:
            print(f"Error checking website signals for {domain}: {e}")
        
        return False
    
    async def get_active_ads_count(self, domain: str) -> int:
        """Get count of active Google Ads for a domain"""
        try:
            domain = self._clean_domain(domain)
            
            # Check transparency center for ad count
            count = await self._get_ads_count_from_transparency(domain)
            if count > 0:
                return count
            
            # Fallback: if we detect ads signals, estimate count
            has_ads = await self._check_website_signals(domain)
            return 1 if has_ads else 0
            
        except Exception as e:
            print(f"Error getting Google Ads count for {domain}: {e}")
            return 0
    
    async def _get_ads_count_from_transparency(self, domain: str) -> int:
        """Get ads count from Google Ads Transparency Center"""
        try:
            # This is a simplified implementation
            # In practice, you'd need to navigate through the transparency center
            # and parse the advertiser page to get exact counts
            
            has_ads = await self._check_transparency_center(domain)
            return 1 if has_ads else 0  # Simplified count
            
        except Exception as e:
            print(f"Error getting ads count from transparency center: {e}")
            return 0
    
    async def get_latest_ads(self, domain: str, limit: int = 5) -> List[AdItem]:
        """Get latest Google Ads for a domain using honest extraction methods"""
        try:
            domain = self._clean_domain(domain)
            
            # Use the honest ads extractor (no fake content)
            extractor = HonestGoogleExtractor()
            
            try:
                real_ads = await extractor.extract_honest_ads(domain, limit)
                if real_ads:
                    print(f"Successfully extracted {len(real_ads)} real Google ads for {domain}")
                    return real_ads
                else:
                    print(f"No real Google ads could be extracted for {domain}")
                    return []
            finally:
                await extractor.close()
            
        except Exception as e:
            print(f"Error getting latest Google Ads for {domain}: {e}")
            return []
    
    async def _get_ads_from_transparency(self, domain: str, limit: int) -> List[AdItem]:
        """Get ads from Google Ads Transparency Center"""
        try:
            # Search for advertiser
            search_url = f"{self.transparency_center_url}/advertiser"
            params = {"q": domain}
            
            response = await self.client.get(search_url, params=params)
            if response.status_code != 200:
                return []
            
            parser = HTMLParser(response.text)
            ads = []
            
            # Look for advertiser links
            advertiser_links = parser.css("a[href*='/advertiser/']")
            
            for link in advertiser_links[:1]:  # Check first advertiser
                href = link.attributes.get("href", "")
                if href:
                    # Get advertiser page
                    advertiser_url = f"{self.transparency_center_url}{href}"
                    
                    try:
                        advertiser_response = await self.client.get(advertiser_url)
                        if advertiser_response.status_code == 200:
                            advertiser_parser = HTMLParser(advertiser_response.text)
                            
                            # Look for ad elements (these selectors may need adjustment)
                            ad_elements = advertiser_parser.css(".ad-creative") or advertiser_parser.css("[data-ad-id]")
                            
                            for ad_element in ad_elements[:limit]:
                                # Extract ad information
                                title_elem = ad_element.css_first(".ad-title") or ad_element.css_first("h3")
                                body_elem = ad_element.css_first(".ad-description") or ad_element.css_first("p")
                                
                                title = title_elem.text() if title_elem else f"Google Ad for {domain}"
                                body = body_elem.text() if body_elem else "Google Ads content"
                                
                                ad_item = AdItem(
                                    platform="google",
                                    title=title,
                                    body=body,
                                    ad_type="display",  # Could be search, display, video, etc.
                                    created_at=datetime.utcnow(),  # Transparency center doesn't always show dates
                                    ad_id=f"google_{domain}_{len(ads)}"
                                )
                                ads.append(ad_item)
                    
                    except Exception as e:
                        print(f"Error fetching advertiser page: {e}")
                        continue
            
            return ads
            
        except Exception as e:
            print(f"Error getting ads from transparency center: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
