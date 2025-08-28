"""core - Implementation of the Ringer core functionality."""

from .ringer import Ringer, CrawlState
from .models import (
    CrawlSpec,
    SearchEngineSeed,
    SearchEngineEnum,
    AnalyzerSpec,
    WeightedKeyword,
    KeywordScoringSpec,
    CrawlRecord,
    PromptInput,
    TextInput,
    DhLlmScoringSpec,
    DhLlmScoreRequest,
    StoreCrawlRecordRequest,
    RunStateEnum,
    RunState,
    CrawlStatus,
)

from .score_analyzers import (
    ScoreAnalyzer,
    KeywordScoreAnalyzer,
    DhLlmScoreAnalyzer
)
from .scrapers import Scraper, PlaywrightScraper
from .results_managers import (
    CrawlResultsManager,
    DhCrawlResultsManager,
)
from .state_managers import (
    CrawlStateManager,
    MemoryCrawlStateManager,
    RedisCrawlStateManager,
    create_crawl_state_manager
)
from .utils import ScoreAnalyzerInfoUtil

__version__ = "1.0.0"
__all__ = [
    "Ringer",
    "CrawlState",
    "CrawlSpec",
    "SearchEngineSeed",
    "SearchEngineEnum",
    "AnalyzerSpec", 
    "WeightedKeyword",
    "KeywordScoringSpec",
    "CrawlRecord",
    "ScoreAnalyzer",
    "KeywordScoreAnalyzer",
    "Scraper",
    "PlaywrightScraper",
    "CrawlResultsManager",
    "DhCrawlResultsManager",
    "CrawlStateManager",
    "MemoryCrawlStateManager",
    "RedisCrawlStateManager",
    "create_crawl_state_manager",
    "StoreCrawlRecordRequest",
    "PromptInput",
    "TextInput",
    "DhLlmScoringSpec",
    "DhLlmScoreRequest",
    "DhLlmScoreAnalyzer",
    "RunStateEnum",
    "RunState",
    "CrawlStatus",
    "ScoreAnalyzerInfoUtil",
]
