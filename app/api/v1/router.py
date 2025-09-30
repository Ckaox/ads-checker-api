"""
API v1 router - Simplified
"""
from fastapi import APIRouter
from app.api.v1.endpoints import simple

router = APIRouter()

# Include simplified endpoint
router.include_router(simple.router, tags=["ads-check"])
