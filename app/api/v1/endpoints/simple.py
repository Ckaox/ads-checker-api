"""
Simplified single endpoint for ads checking
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.simple import CheckRequest, CheckResponse
from app.services.simple_service import SimpleAdsService

router = APIRouter()

# Dependency to get the service
async def get_ads_service() -> SimpleAdsService:
    return SimpleAdsService()

@router.post("/check", response_model=CheckResponse)
async def check_ads(
    request: CheckRequest,
    service: SimpleAdsService = Depends(get_ads_service)
) -> CheckResponse:
    """
    Check for active ads and resolve identities
    
    This endpoint:
    1. Resolves missing identifiers (domain ↔ Facebook page)
    2. Detects active ads on Meta and Google platforms
    3. Returns a simple boolean result for each platform
    
    **Input**: Provide either domain, Facebook page, or both
    **Output**: Resolved identifiers + boolean ads detection results
    
    **Examples:**
    - Input: `{"domain": "nike.com"}` → Finds Facebook page + checks ads
    - Input: `{"facebook_page": "https://facebook.com/nike"}` → Finds domain + checks ads
    - Input: `{"domain": "nike.com", "facebook_page": "https://facebook.com/nike"}` → Validates + checks ads
    """
    try:
        result = await service.check_ads(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
