"""
API v1 router - Simplified
"""
from fastapi import APIRouter
from app.api.v1.endpoints import simple

# Create API router with prefix
api_router = APIRouter()

# Include simplified endpoint
api_router.include_router(simple.router, tags=["ads-check"])
