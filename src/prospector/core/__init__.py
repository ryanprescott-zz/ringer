"""core - Implementation of the Prospector core functionality."""

from .prospector import Prospector, CrawlState
from .models import (
    CrawlSpec,
    AnalyzerSpec,
    WeightedKeyword,
    CrawlRecord,
    LLMScoreServiceInput,
    LLMScoreRequest,
    StoreCrawlRecordRequest,
    RunStateEnum,
    RunState,
)

from .score_analyzers import (
    ScoreAnalyzer,
    KeywordScoreAnalyzer,
    LLMServiceScoreAnalyzer
)
from .scrapers import Scraper, PlaywrightScraper
from .storage_handlers import (
    CrawlStorageHandler,
    FsStoreHandler,
    DhStoreHandler,
)

__version__ = "1.0.0"
__all__ = [
    "Prospector",
    "CrawlState",
    "CrawlSpec",
    "AnalyzerSpec", 
    "WeightedKeyword",
    "CrawlRecord",
    "ScoreAnalyzer",
    "KeywordScoreAnalyzer",
    "Scraper",
    "PlaywrightScraper",
    "CrawlStorageHandler",
    "FsStoreHandler",
    "DhStoreHandler",
    "StoreCrawlRecordRequest",
    "LLMScoreServiceInput",
    "LLMScoreRequest",
    "LLMServiceScoreAnalyzer",
    "RunStateEnum",
    "RunState",
]
