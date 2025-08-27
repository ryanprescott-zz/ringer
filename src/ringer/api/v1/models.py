"""Pydantic models for the Ringer FastAPI web service."""

from typing import List, Optional
from pydantic import BaseModel, Field
from ringer.core.models import CrawlSpec, RunState, SearchEngineSeed, CrawlResultsId, CrawlRecordSummary, CrawlRecord
import uuid


class CreateCrawlRequest(BaseModel):
    """Request model for creating a new crawl."""
    
    crawl_spec: CrawlSpec
    results_id: CrawlResultsId = Field(
        default_factory=lambda: CreateCrawlRequest._create_default_results_id(),
        description="Identifier for the crawl results data set"
    )
    
    @staticmethod
    def _create_default_results_id() -> CrawlResultsId:
        """Create a default CrawlResultsId with unique collection_id and data_id."""
        collection_id = f"collection_{uuid.uuid4()}"
        data_id = f"data_{uuid.uuid4()}"
        return CrawlResultsId(collection_id=collection_id, data_id=data_id)


class CreateCrawlResponse(BaseModel):
    """Response model for crawl submission."""
    
    crawl_id: str
    run_state: RunState


class StartCrawlResponse(BaseModel):
    """Response model for crawl start."""
    
    crawl_id: str
    run_state: RunState


class StopCrawlResponse(BaseModel):
    """Response model for crawl stop."""
    
    crawl_id: str
    run_state: RunState


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


class CrawlRecordSummaryRequest(BaseModel):
    """Request model for retrieving crawl record summaries."""
    
    record_count: int = Field(gt=0, description="Number of record summaries to return")
    score_type: str = Field(description="Type of score to use for sorting (e.g., 'composite', 'keyword')")


class CrawlRecordSummaryResponse(BaseModel):
    """Response model for crawl record summaries."""
    
    records: List[CrawlRecordSummary]


class CrawlRecordRequest(BaseModel):
    """Request model for retrieving crawl records."""
    
    record_ids: List[str] = Field(description="List of record IDs to retrieve")


class CrawlRecordResponse(BaseModel):
    """Response model for crawl records."""
    
    records: List[CrawlRecord]
