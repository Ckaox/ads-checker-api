"""
Simplified service for identity resolution and ads detection
"""
from typing import Optional, Tuple
import asyncio

from app.schemas.simple import CheckRequest, CheckResponse
from app.resolvers.domain_resolver import DomainResolver
from app.resolvers.facebook_resolver import FacebookResolver
from app.providers.meta.simple_client import SimpleMetaClient
from app.providers.google.simple_client import SimpleGoogleClient
from app.services.cache_service import CacheService

class SimpleAdsService:
    """Simplified service that combines identity resolution and ads detection"""
    
    def __init__(self):
        self.domain_resolver = DomainResolver()
        self.facebook_resolver = FacebookResolver()
        self.meta_client = SimpleMetaClient()
        self.google_client = SimpleGoogleClient()
        self.cache = CacheService()
    
    async def check_ads(self, request: CheckRequest) -> CheckResponse:
        """
        Main method: resolve identities and check for active ads
        """
        # Validate input - treat empty strings as None
        domain = request.domain.strip() if request.domain else None
        facebook_page = request.facebook_page.strip() if request.facebook_page else None
        
        if not domain and not facebook_page:
            return CheckResponse(
                success=False,
                message="Either domain or facebook_page must be provided"
            )
        
        # Create cache key
        cache_key = f"check:{domain or 'none'}:{facebook_page or 'none'}"
        
        # Try cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return CheckResponse(**cached_result)
        
        try:
            # Step 1: Resolve identities
            domain, facebook_page, meta_page_id = await self._resolve_identities(
                domain, facebook_page
            )
            
            # Step 2: Check for ads in parallel
            has_meta_ads, has_google_ads = await self._check_ads_parallel(
                domain, meta_page_id
            )
            
            # Step 3: Create response
            response = CheckResponse(
                domain=domain,
                facebook_page=facebook_page,
                meta_page_id=meta_page_id,
                has_meta_ads=has_meta_ads,
                has_google_ads=has_google_ads,
                success=True,
                message=self._create_success_message(domain, facebook_page, has_meta_ads, has_google_ads)
            )
            
            # Cache result
            await self.cache.set(cache_key, response.model_dump(), ttl=3600)  # 1 hour cache
            
            return response
            
        except Exception as e:
            return CheckResponse(
                domain=domain,
                facebook_page=facebook_page,
                success=False,
                message=f"Error during check: {str(e)}"
            )
    
    async def _resolve_identities(
        self, 
        input_domain: Optional[str], 
        input_facebook_page: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Resolve missing identities"""
        
        domain = input_domain
        facebook_page = input_facebook_page
        meta_page_id = None
        
        # If we have domain but no Facebook page, try to find it
        if domain and not facebook_page:
            try:
                resolved_facebook = await self.domain_resolver.find_facebook_page(domain)
                if resolved_facebook:
                    facebook_page = resolved_facebook
            except Exception as e:
                print(f"Error resolving Facebook page for {domain}: {e}")
        
        # If we have Facebook page but no domain, try to find it
        if facebook_page and not domain:
            try:
                resolved_domain = await self.facebook_resolver.find_website_from_page(facebook_page)
                if resolved_domain:
                    domain = resolved_domain
            except Exception as e:
                print(f"Error resolving domain for {facebook_page}: {e}")
        
        # Extract Meta page ID from Facebook page
        if facebook_page:
            try:
                # Try facebook_resolver first
                meta_page_id = await self.facebook_resolver.extract_page_id(facebook_page)
                
                # If that fails, try using Meta client (has better Graph API access)
                if not meta_page_id:
                    print(f"⚠️  facebook_resolver failed, trying Meta client...")
                    meta_page_id = await self.meta_client.get_page_id(facebook_page)
                    if meta_page_id:
                        print(f"✅ Meta client got Page ID: {meta_page_id}")
            except Exception as e:
                print(f"Error extracting page ID from {facebook_page}: {e}")
        
        return domain, facebook_page, meta_page_id
    
    async def _check_ads_parallel(
        self, 
        domain: Optional[str], 
        meta_page_id: Optional[str]
    ) -> Tuple[bool, bool]:
        """Check for ads on both platforms in parallel"""
        
        # Create tasks for parallel execution
        tasks = []
        
        # Meta ads check
        if meta_page_id:
            tasks.append(self._check_meta_ads(meta_page_id))
        else:
            tasks.append(self._return_false())  # No Meta page ID
        
        # Google ads check
        if domain:
            tasks.append(self._check_google_ads(domain))
        else:
            tasks.append(self._return_false())  # No domain
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        has_meta_ads = results[0] if not isinstance(results[0], Exception) else False
        has_google_ads = results[1] if not isinstance(results[1], Exception) else False
        
        return has_meta_ads, has_google_ads
    
    async def _check_meta_ads(self, page_id: str) -> bool:
        """Check if Meta page has active ads"""
        try:
            if not page_id:
                print(f"⚠️  No Meta page ID available for ads check")
                return False
            
            print(f"\n🔍 Starting Meta ads check with Page ID: {page_id}")
            result = await self.meta_client.check_ads_presence(page_id)
            print(f"Meta ads check result: {result}")
            return result
        except Exception as e:
            print(f"❌ Error checking Meta ads for {page_id}: {e}")
            return False
    
    async def _check_google_ads(self, domain: str) -> bool:
        """Check if domain has active Google ads"""
        try:
            return await self.google_client.check_ads_presence(domain)
        except Exception as e:
            print(f"Error checking Google ads for {domain}: {e}")
            return False
    
    async def _return_false(self) -> bool:
        """Helper method to return False (for missing identifiers)"""
        return False
    
    def _create_success_message(
        self, 
        domain: Optional[str], 
        facebook_page: Optional[str], 
        has_meta_ads: bool, 
        has_google_ads: bool
    ) -> str:
        """Create a descriptive success message"""
        
        parts = []
        
        # Identity resolution
        if domain and facebook_page:
            parts.append("Resolved both domain and Facebook page")
        elif domain:
            parts.append("Domain provided")
        elif facebook_page:
            parts.append("Facebook page provided")
        
        # Ads detection
        ads_status = []
        if has_meta_ads:
            ads_status.append("Meta ads detected")
        if has_google_ads:
            ads_status.append("Google ads detected")
        
        if ads_status:
            parts.append(f"Active ads found: {', '.join(ads_status)}")
        else:
            parts.append("No active ads detected")
        
        return ". ".join(parts)
