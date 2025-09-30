"""
FastAPI dependencies
"""
from app.services.ads_service import AdsService
from app.services.cache_service import CacheService
from app.providers.meta.client import MetaClient
from app.providers.google.client import GoogleClient
from app.resolvers.domain_resolver import DomainResolver

# Global service instances (will be initialized on startup)
_cache_service = None
_meta_client = None
_google_client = None
_domain_resolver = None
_ads_service = None

def get_cache_service() -> CacheService:
    """Get cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

def get_meta_client() -> MetaClient:
    """Get Meta client instance"""
    global _meta_client
    if _meta_client is None:
        _meta_client = MetaClient()
    return _meta_client

def get_google_client() -> GoogleClient:
    """Get Google client instance"""
    global _google_client
    if _google_client is None:
        _google_client = GoogleClient()
    return _google_client

def get_domain_resolver() -> DomainResolver:
    """Get domain resolver instance"""
    global _domain_resolver
    if _domain_resolver is None:
        _domain_resolver = DomainResolver()
    return _domain_resolver

def get_ads_service() -> AdsService:
    """Get ads service instance"""
    global _ads_service
    if _ads_service is None:
        _ads_service = AdsService(
            cache_service=get_cache_service(),
            meta_client=get_meta_client(),
            google_client=get_google_client(),
            domain_resolver=get_domain_resolver()
        )
    return _ads_service
