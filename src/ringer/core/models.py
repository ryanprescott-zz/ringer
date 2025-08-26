"""Pydantic models for the Ringer application."""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class RunStateEnum(str, Enum):
    """Enumeration of crawl run states."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class SearchEngineEnum(str, Enum):
    """Enumeration of supported search engines."""
    GOOGLE = "Google"
    BING = "Bing"
    DUCKDUCKGO = "DuckDuckGo"


class RunState(BaseModel):
    """Represents a state change in a crawl's lifecycle."""
    state: RunStateEnum = Field(..., description="The run state")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this state was entered")

class WeightedKeyword(BaseModel):
    """A keyword with an associated weight for scoring."""
    
    keyword: str = Field(..., description="The keyword to search for")
    weight: float = Field(..., description="Weight for this keyword in scoring")

class WeightedRegex(BaseModel):
    """A regular expression with an associated weight for scoring."""
    
    regex: str = Field(..., description="The regular expression pattern to search for")
    weight: float = Field(..., description="Weight for this regex in scoring")
    flags: int = Field(default=0, description="Regex flags (e.g., re.IGNORECASE)")

class PromptInput(BaseModel):
    """Input for a prompt to the LLM service."""
    
    prompt: str = Field(..., description="The prompt string to send to the LLM")

    @field_validator('prompt')
    @classmethod
    def check_prompt_not_empty(cls, value: str) -> str:
        """Ensure the prompt is not empty."""
        if not value.strip():
            raise ValueError("Prompt cannot be empty")
        return value

class TopicListInput(BaseModel):
    """Input for a list of topics to score against."""
    
    topics: List[str] = Field(..., description="List of topics to score against")

    @field_validator('topics')
    @classmethod
    def check_topics_not_empty(cls, value: List[str]) -> List[str]:
        """Ensure the topics list is not empty."""
        if not value:
            raise ValueError("Topics list cannot be empty")
        return value

class FieldMap(BaseModel):
    """Mapping of field names to their types."""
    
    name_to_type: Dict[str, str] = Field(..., description="Mapping of field names to their types")

    @field_validator('name_to_type')
    @classmethod
    def check_map_not_empty(cls, value: Dict[str, str]) -> Dict[str, str]:
        """Ensure the field map is not empty."""
        if not value:
            raise ValueError("Field map cannot be empty")
        return value

class DhLlmGenerationInput(BaseModel):
    """Input for text generation."""
    
    prompt: str = Field(..., description="The prompt to generate text from")
    output_format: FieldMap = Field(..., description="Mapping of output fields to types")

class DhLlmGenerationRequest(BaseModel):
    """Request object for LLM generation service."""

    generation_input: DhLlmGenerationInput = Field(..., description="Input for text generation")
    text_inputs: List[str] = Field(..., description="List of text inputs to process")

class StoreCrawlRecordRequest(BaseModel):
    """Request object for crawl record storage service."""
    
    record: 'CrawlRecord' = Field(..., description="The crawl record to handle")
    crawl_id: str = Field(..., description="ID of the crawl")

class AnalyzerSpec(BaseModel):
    """Specification for a score analyzer."""
    
    name: str = Field(..., description="Name matching the analyzer class name")
    composite_weight: float = Field(..., description="Weight in composite scoring")

class KeywordScoringSpec(AnalyzerSpec):
    """Specification for keyword-based scoring."""
    
    keywords: List[WeightedKeyword] = Field(default=[], description="List of weighted keywords to score against")
    regexes: List[WeightedRegex] = Field(default=[], description="List of weighted regular expressions to score against")

    @model_validator(mode='after')
    def check_not_empty(self):
        """Ensure at least one keyword or regex is provided."""
        if not self.keywords and not self.regexes:
            raise ValueError("At least one keyword or regex must be provided")
        return self

class DhLlmScoringSpec(AnalyzerSpec):
    """Input for LLM service score analyzer."""

    scoring_input: PromptInput | TopicListInput = Field(..., description="Scoring input - either prompt or topics")


class CrawlResultsId(BaseModel):
    """Identifier for a crawl results data set."""
    
    collection_id: str = Field(..., description="Collection identifier for the crawl results")
    data_id: str = Field(..., description="Data identifier for the crawl results")


class SearchEngineSeed(BaseModel):
    """Specification for search engine seed generation."""
    
    search_engine: SearchEngineEnum = Field(..., description="Search engine to use")
    query: str = Field(..., description="Search query string")
    result_count: int = Field(..., description="Number of search results to collect as seeds", gt=0, le=100)

    @field_validator('query')
    @classmethod
    def check_query_not_empty(cls, value: str) -> str:
        """Ensure the query is not empty."""
        if not value.strip():
            raise ValueError("Search query cannot be empty")
        return value


class CrawlSpec(BaseModel):
    """Specification for a web crawl."""
    
    name: str = Field(..., description="Name of the crawl")
    seeds: List[str] = Field(..., description="List of seed URLs for the crawl")
    analyzer_specs: List[KeywordScoringSpec|DhLlmScoringSpec] = Field(..., description="Analyzers to use")
    worker_count: int = Field(default=1, description="Number of workers to use")
    domain_blacklist: Optional[List[str]] = Field(
        default=None, description="Domains to exclude from crawling"
    )
    results_id: Optional[CrawlResultsId] = Field(
        default=None, description="Identifier for the crawl results data set"
    )
    
    @field_validator('seeds')
    @classmethod
    def check_seeds_not_empty(cls, value: List[str]) -> List[str]:
        """Ensure the seeds list is not empty."""
        if not value:
            raise ValueError("Seeds list cannot be empty")
        return value
    
    @property
    def id(self) -> str:
        """Generate a hash ID for this crawl based on the name."""
        return hashlib.md5(self.name.encode()).hexdigest()
    
    def create_default_results_id(self) -> CrawlResultsId:
        """Create a default CrawlResultsId with unique collection_id and data_id."""
        collection_id = f"collection_{uuid.uuid4()}"
        data_id = f"data_{uuid.uuid4()}"
        return CrawlResultsId(collection_id=collection_id, data_id=data_id)


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


class CrawlStatus(BaseModel):
    """Status information for a crawl."""
    
    crawl_id: str = Field(..., description="ID of the crawl")
    crawl_name: str = Field(..., description="Name of the crawl")
    current_state: str = Field(..., description="Current run state")
    state_history: List[RunState] = Field(..., description="History of state changes")
    crawled_count: int = Field(..., description="Total URLs pulled from frontier")
    processed_count: int = Field(..., description="Successfully processed pages")
    error_count: int = Field(..., description="URLs that failed to process")
    frontier_size: int = Field(..., description="Current size of the frontier")

# Forward reference resolution for StoreCrawlRecordRequest
StoreCrawlRecordRequest.model_rebuild()
