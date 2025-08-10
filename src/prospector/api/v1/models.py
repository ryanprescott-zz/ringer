"""Pydantic models for the Prospector FastAPI web service."""

from pydantic import BaseModel
from prospector.core.models import CrawlSpec


class SubmitCrawlRequest(BaseModel):
    """Request model for submitting a new crawl."""
    
    crawl_spec: CrawlSpec


class SubmitCrawlResponse(BaseModel):
    """Response model for crawl submission."""
    
    crawl_id: str
    crawl_submitted_time: str


class CrawlStartRequest(BaseModel):
    """Request model for starting a crawl."""
    
    crawl_id: str


class StartCrawlResponse(BaseModel):
    """Response model for crawl start."""
    
    crawl_id: str
    crawl_started_time: str


class CrawlStopRequest(BaseModel):
    """Request model for stopping a crawl."""
    
    crawl_id: str


class StopCrawlResponse(BaseModel):
    """Response model for crawl stop."""
    
    crawl_id: str
    crawl_stopped_time: str


class CrawlDeleteRequest(BaseModel):
    """Request model for deleting a crawl."""
    
    crawl_id: str


class DeleteCrawlResponse(BaseModel):
    """Response model for crawl deletion."""
    
    crawl_id: str
    crawl_deleted_time: str
