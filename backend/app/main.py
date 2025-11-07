"""FastAPI application entry point."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import Settings, get_settings
from app.routers import maps
from app.models import HealthResponse
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="HeyPico Maps API",
    description="Google Maps integration for Open WebUI with local LLM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"API Key Configured: {'Yes' if settings.google_maps_api_key else 'No'}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(maps.router, prefix="/api/maps", tags=["maps"])

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "HeyPico Maps API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and configuration information.
    """
    return HealthResponse(
        status="healthy",
        service="heypico-maps-api",
        version="1.0.0",
        maps_api_configured=bool(settings.google_maps_api_key)
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )
