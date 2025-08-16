"""Pydantic models for the Prospector FastAPI web service."""

from typing import List, Optional
from pydantic import BaseModel
from prospector.core.models import CrawlSpec, RunState, SearchEngineSeed


class CreateCrawlRequest(BaseModel):
    """Request model for creating a new crawl."""
    
    crawl_spec: CrawlSpec


class CreateCrawlResponse(BaseModel):
    """Response model for crawl submission."""
    
    crawl_id: str
    run_state: RunState


class StartCrawlRequest(BaseModel):
    """Request model for starting a crawl."""
    
    crawl_id: str


class StartCrawlResponse(BaseModel):
    """Response model for crawl start."""
    
    crawl_id: str
    run_state: RunState


class StopCrawlRequest(BaseModel):
    """Request model for stopping a crawl."""
    
    crawl_id: str


class StopCrawlResponse(BaseModel):
    """Response model for crawl stop."""
    
    crawl_id: str
    run_state: RunState


class DeleteCrawlRequest(BaseModel):
    """Request model for deleting a crawl."""
    
    crawl_id: str


class DeleteCrawlResponse(BaseModel):
    """Response model for crawl deletion."""
    
    crawl_id: str
    crawl_deleted_time: str


class SeedUrlScrapeRequest(BaseModel):
    """Request model for collecting seed URLs from search engines."""
    
    search_engine_seeds: List[SearchEngineSeed]


class SeedUrlScrapeResponse(BaseModel):
    """Response model for seed URL collection."""
    
    seed_urls: List[str]


class FieldDescriptor(BaseModel):
    """Descriptor for a field in an analyzer spec."""
    
    name: str
    type: str
    description: str
    required: bool
    default: Optional[str] = None


class AnalyzerInfo(BaseModel):
    """Information about a score analyzer."""
    
    name: str
    description: str
    spec_fields: List[FieldDescriptor]


class AnalyzerInfoResponse(BaseModel):
    """Response model for analyzer information."""
    
    analyzers: List[AnalyzerInfo]


class CrawlStatus(BaseModel):
    """Status information for a crawl."""
    
    crawl_id: str
    crawl_name: str
    current_state: str  # RunStateEnum as string
    state_history: List[RunState]
    crawled_count: int
    processed_count: int
    error_count: int
    frontier_size: int


class CrawlStatusResponse(BaseModel):
    """Response model for crawl status."""
    
    status: CrawlStatus


class CrawlStatusListResponse(BaseModel):
    """Response model for list of crawl statuses."""
    
    crawls: List[CrawlStatus]


class CrawlInfo(BaseModel):
    """Information about a crawl including spec and status."""
    
    crawl_spec: CrawlSpec
    crawl_status: CrawlStatus


class CrawlInfoResponse(BaseModel):
    """Response model for crawl information."""
    
    info: CrawlInfo


class CrawlInfoListResponse(BaseModel):
    """Response model for list of crawl information."""
    
    crawls: List[CrawlInfo]
