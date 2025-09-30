"""
Simplified Google client - only for ads presence detection
"""
import re
import httpx
from typing import Optional
from urllib.parse import quote, urlparse
from selectolax.parser import HTMLParser

from app.core.config import settings

class SimpleGoogleClient:
    """Simplified client for Google ads presence detection only"""
    
    def __init__(self):
        self.transparency_center_url = "https://adstransparency.google.com"
        
        self.client = httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            }
        )
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize domain"""
        if not domain:
            return domain
        
        # Remove protocol if present
        if "://" in domain:
            domain = urlparse(domain).netloc or domain
        
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain.lower().strip()
    
    async def check_ads_presence(self, domain: str) -> bool:
        """Check if a domain has active Google ads"""
        try:
            domain = self._clean_domain(domain)
            
            # Method 1: Check website for Google Ads signals (most reliable)
            has_website_signals = await self._check_website_signals(domain)
            if has_website_signals:
                return True
            
            # Method 2: Check Google search for ads
            has_search_ads = await self._check_google_search_ads(domain)
            if has_search_ads:
                return True
            
            # Method 3: Check Google Ads Transparency Center
            has_transparency_ads = await self._check_transparency_center(domain)
            if has_transparency_ads:
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking Google ads presence for {domain}: {e}")
            return False
    
    async def _check_transparency_center(self, domain: str) -> bool:
        """Check Google Ads Transparency Center for active ads"""
        try:
            # Try multiple transparency center approaches
            search_terms = [domain, domain.replace('.com', ''), domain.split('.')[0]]
            
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
                        
                        if response.status_code == 200:
                            content = response.text
                            parser = HTMLParser(content)
                            
                            # Look for advertiser elements
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
                                            print(f"Google ads found via transparency: {text[:50]}...")
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
                            print(f"Google Ads signals found for {domain}: {found_signals[:2]}")
                            # If we find multiple categories or strong indicators, likely running ads
                            return len(found_signals) >= 2 or any("conversion" in signal.lower() for signal in found_signals)
                        
                except Exception:
                    continue  # Try next protocol
            
        except Exception as e:
            print(f"Error checking website signals for {domain}: {e}")
        
        return False
    
    async def _check_google_search_ads(self, domain: str) -> bool:
        """Check if domain shows ads in Google search results"""
        try:
            # Search for the domain name and brand terms
            search_terms = [
                domain,
                domain.replace('.com', '').replace('.net', '').replace('.org', ''),
                domain.split('.')[0]  # Just the brand name
            ]
            
            for term in search_terms:
                try:
                    # Search Google for the term
                    search_url = "https://www.google.com/search"
                    params = {
                        "q": term,
                        "hl": "en",
                        "gl": "us"
                    }
                    
                    response = await self.client.get(search_url, params=params)
                    
                    if response.status_code == 200:
                        content = response.text
                        parser = HTMLParser(content)
                        
                        # Look for sponsored/ad indicators in search results
                        ad_indicators = [
                            "[data-text-ad]", "[data-ad-result]", ".ads-ad",
                            ".commercial-unit-desktop-top", ".uEierd",  # Google ads containers
                            "[aria-label*='Ad']", "[aria-label*='Sponsored']",
                            ".ads-visurl", ".ad_cclk"  # Ad URL elements
                        ]
                        
                        for selector in ad_indicators:
                            ad_elements = parser.css(selector)
                            for element in ad_elements:
                                text = element.text().lower()
                                href = element.attributes.get('href', '')
                                
                                # Check if the ad is related to our domain
                                if (domain.lower() in text or 
                                    domain.lower() in href or
                                    term.lower() in text):
                                    print(f"Google search ad found for {domain}: {text[:50]}...")
                                    return True
                        
                        # Also check for "Ad" or "Sponsored" text near domain mentions
                        content_lower = content.lower()
                        if domain.lower() in content_lower:
                            # Look for ad indicators near domain mentions
                            domain_positions = [m.start() for m in re.finditer(re.escape(domain.lower()), content_lower)]
                            for pos in domain_positions:
                                # Check 200 characters before and after domain mention
                                snippet = content_lower[max(0, pos-200):pos+200]
                                if any(indicator in snippet for indicator in ['sponsored', 'ad·', '·ad', 'anuncio']):
                                    print(f"Google search ad context found for {domain}")
                                    return True
                        
                except Exception as e:
                    print(f"Error searching Google for {term}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error checking Google search ads for {domain}: {e}")
        
        return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
