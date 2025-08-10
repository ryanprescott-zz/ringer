"""FastAPI application for the Prospector web crawler service."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from prospector.core.prospector import Prospector
from prospector.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifespan.
    
    Creates a Prospector instance at startup and ensures proper cleanup at shutdown.
    
    Args:
        app: The FastAPI application instance
        
    Yields:
        None: Control back to FastAPI during application runtime
    """
    # Startup: Create and store Prospector instance
    prospector = Prospector()
    app.state.prospector = prospector
    
    yield
    
    # Shutdown: Clean up Prospector resources
    prospector.shutdown()


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Prospector Web Crawler API",
    description="A best-first-search web crawler with intelligent content prioritization",
    version="1.0.0",
    lifespan=lifespan
)

# Include the API router
app.include_router(api_router)


@app.get("/")
def read_root():
    """
    Root endpoint providing basic API information.
    
    Returns:
        dict: Basic API information and status
    """
    return {
        "message": "Prospector Web Crawler API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Health status information
    """
    return {"status": "healthy"}
