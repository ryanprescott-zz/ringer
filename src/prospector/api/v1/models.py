"""Pydantic models for the Prospector FastAPI web service."""

from pydantic import BaseModel
from prospector.core.models import CrawlSpec


class CreateCrawlRequest(BaseModel):
    """Request model for creating a new crawl."""
    
    crawl_spec: CrawlSpec


class CreateCrawlResponse(BaseModel):
    """Response model for crawl submission."""
    
    crawl_id: str
    crawl_created_time: str


class StartCrawlRequest(BaseModel):
    """Request model for starting a crawl."""
    
    crawl_id: str


class StartCrawlResponse(BaseModel):
    """Response model for crawl start."""
    
    crawl_id: str
    crawl_started_time: str


class StopCrawlRequest(BaseModel):
    """Request model for stopping a crawl."""
    
    crawl_id: str


class StopCrawlResponse(BaseModel):
    """Response model for crawl stop."""
    
    crawl_id: str
    crawl_stopped_time: str


class DeleteCrawlRequest(BaseModel):
    """Request model for deleting a crawl."""
    
    crawl_id: str


class DeleteCrawlResponse(BaseModel):
    """Response model for crawl deletion."""
    
    crawl_id: str
    crawl_deleted_time: str
