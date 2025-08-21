"""FastAPI router for seed URL collection endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Request
from ringer.api.v1.models import (
    SeedUrlScrapeRequest, SeedUrlScrapeResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/seeds",
    tags=["seeds"],
)


@router.post("/collect", response_model=SeedUrlScrapeResponse)
async def collect_seed_urls(request: SeedUrlScrapeRequest, app_request: Request) -> SeedUrlScrapeResponse:
    """
    Collect seed URLs from search engines.
    
    Args:
        request: The seed URL scrape request containing search engine specifications
        app_request: FastAPI request object to access application state
        
    Returns:
        SeedUrlScrapeResponse: Response containing collected seed URLs
        
    Raises:
        HTTPException: If seed URL collection fails
    """
    try:
        ringer = app_request.app.state.ringer
        seed_urls = await ringer.collect_seed_urls_from_search_engines(request.search_engine_seeds)
        
        return SeedUrlScrapeResponse(
            seed_urls=seed_urls
        )
    except Exception as e:
        logger.error(f"Failed to collect seed URLs: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
