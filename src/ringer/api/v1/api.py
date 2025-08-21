"""Main API router for Ringer v1 endpoints."""

from fastapi import APIRouter
from ringer.api.v1.routers import crawl, seeds, analyzers
from ringer.core.settings import RingerServiceSettings

# Load service settings
settings = RingerServiceSettings()

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
