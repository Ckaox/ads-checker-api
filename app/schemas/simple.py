"""
Simplified schemas for the single endpoint
"""
from pydantic import BaseModel, Field
from typing import Optional

class CheckRequest(BaseModel):
    """Request schema for the check endpoint"""
    domain: Optional[str] = Field(None, description="Website domain (e.g., 'example.com')")
    facebook_page: Optional[str] = Field(None, description="Facebook page URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "domain": "nike.com",
                "facebook_page": "https://www.facebook.com/nike"
            }
        }

class CheckResponse(BaseModel):
    """Response schema for the check endpoint"""
    # Resolved identifiers
    domain: Optional[str] = Field(None, description="Resolved domain")
    facebook_page: Optional[str] = Field(None, description="Resolved Facebook page URL")
    meta_page_id: Optional[str] = Field(None, description="Meta page ID if found")
    
    # Ads detection results
    has_meta_ads: bool = Field(False, description="Whether Meta ads are detected")
    has_google_ads: bool = Field(False, description="Whether Google ads are detected")
    
    # Status information
    success: bool = Field(True, description="Whether the check was successful")
    message: Optional[str] = Field(None, description="Additional information or error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "domain": "nike.com",
                "facebook_page": "https://www.facebook.com/nike",
                "meta_page_id": "15087023681",
                "has_meta_ads": True,
                "has_google_ads": True,
                "success": True,
                "message": "Successfully resolved identifiers and detected ads"
            }
        }
