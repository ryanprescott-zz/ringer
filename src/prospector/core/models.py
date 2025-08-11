"""Pydantic models for the Prospector application."""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class RunStateEnum(str, Enum):
    """Enumeration of crawl run states."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class RunState(BaseModel):
    """Represents a state change in a crawl's lifecycle."""
    state: RunStateEnum = Field(..., description="The run state")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this state was entered")


class WeightedKeyword(BaseModel):
    """A keyword with an associated weight for scoring."""
    
    keyword: str = Field(..., description="The keyword to search for")
    weight: float = Field(..., description="Weight for this keyword in scoring")


class LLMScoreServiceInput(BaseModel):
    """Input for LLM service score analyzer."""
    
    text: str = Field(..., description="The text string to score")
    prompt: Optional[str] = Field(default=None, description="Optional LLM prompt string")


class LLMScoreRequest(BaseModel):
    """Request object for LLM scoring service."""
    
    prompt: str = Field(..., description="The prompt string for the LLM")
    model_output_format: Dict[str, str] = Field(..., description="Output format specification")


class StoreCrawlRecordRequest(BaseModel):
    """Request object for crawl record storage service."""
    
    record: 'CrawlRecord' = Field(..., description="The crawl record to handle")
    crawl_id: str = Field(..., description="ID of the crawl")


class AnalyzerSpec(BaseModel):
    """Specification for a score analyzer."""
    
    name: str = Field(..., description="Name matching the analyzer class name")
    composite_weight: float = Field(..., description="Weight in composite scoring")
    params: Any = Field(..., description="Parameters specific to the analyzer")


class CrawlSpec(BaseModel):
    """Specification for a web crawl."""
    
    name: str = Field(..., description="Name of the crawl")
    seed_urls: List[str] = Field(..., description="Initial URLs to crawl")
    analyzer_specs: List[AnalyzerSpec] = Field(..., description="Analyzers to use")
    worker_count: int = Field(default=1, description="Number of workers to use")
    domain_blacklist: Optional[List[str]] = Field(
        default=None, description="Domains to exclude from crawling"
    )
    
    @property
    def id(self) -> str:
        """Generate a hash ID for this crawl based on the name."""
        return hashlib.md5(self.name.encode()).hexdigest()


class CrawlRecord(BaseModel):
    """Record of a crawled web page."""
    url: str = Field(..., description="The crawled URL")
    page_source: str = Field(..., description="Raw page source content")
    extracted_content: Any = Field(..., description="Extracted content from the page")
    links: List[str] = Field(..., description="Links found on the page")
    scores: Dict[str, float] = Field(..., description="Scores from each analyzer")
    composite_score: float = Field(..., description="Weighted composite score")
    timestamp: datetime = Field(default_factory=datetime.now, description="Crawl timestamp")

    @property
    def id(self) -> str:
        """Generate a hash ID for this record based on the url."""
        return hashlib.md5(self.url.encode()).hexdigest()

# Forward reference resolution for StoreCrawlRecordRequest
StoreCrawlRecordRequest.model_rebuild()
