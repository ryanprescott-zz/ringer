"""core - Implementation of the Prospector core functionality."""

from .prospector import Prospector, CrawlState
from .models import (
    CrawlSpec,
    AnalyzerSpec,
    WeightedKeyword,
    CrawlRecord,
    LLMScoreServiceInput,
    LLMScoreRequest,
    HandleCrawlRecordRequest,
)

from .score_analyzers import (
    ScoreAnalyzer,
    KeywordScoreAnalyzer,
    LLMServiceScoreAnalyzer
)
from .scrapers import Scraper, PlaywrightScraper
from .handlers import (
    CrawlRecordHandler,
    FsStoreCrawlRecordHandler,
    ServiceCrawlRecordHandler,
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
    "CrawlRecordHandler",
    "FsStoreCrawlRecordHandler",
    "HandleCrawlRecordRequest",
    "LLMScoreServiceInput",
    "LLMScoreRequest",
    "LLMServiceScoreAnalyzer",
    "HandleCrawlRecordRequest",
]