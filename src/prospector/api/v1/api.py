"""Main API router for Prospector v1 endpoints."""

from fastapi import APIRouter
from prospector.api.v1.routers import crawl, seeds, analyzers
from prospector.core.settings import ProspectorServiceSettings

# Load service settings
settings = ProspectorServiceSettings()

# Create the main API router
api_router = APIRouter()

# Include the crawl router with the configured base path
api_router.include_router(
    crawl.router,
)

# Include the seeds router
api_router.include_router(
    seeds.router,
)

# Include the analyzers router
api_router.include_router(
    analyzers.router,
)
