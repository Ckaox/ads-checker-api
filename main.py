"""
Ads Checker API - Main application entry point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.v1.router import api_router
from app.core.config import settings

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Ads Checker API starting up...")
    yield
    # Shutdown
    print("🛑 Ads Checker API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Ads Checker API",
    description="API para verificar y analizar anuncios activos en Meta y Google Ads",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/v1")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Ads Checker API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "ads-checker-api",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Use PORT from environment (Render sets this) or fallback to settings
    port = int(os.environ.get("PORT", settings.API_PORT))
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=port,
        reload=settings.DEBUG
    )
