"""core - Implementation of the Prospector core functionality."""

from .prospector import Prospector, CrawlState
from .models import (
    CrawlSpec,
    SearchEngineSeed,
    SearchEngineEnum,
    AnalyzerSpec,
    WeightedKeyword,
    KeywordScoringSpec,
    CrawlRecord,
    PromptInput,
    TopicListInput,
    LLMScoringSpec,
    FieldMap,
    LLMGenerationInput,
    LLMGenerationRequest,
    StoreCrawlRecordRequest,
    RunStateEnum,
    RunState,
    CrawlStatus,
)

from .score_analyzers import (
    ScoreAnalyzer,
    KeywordScoreAnalyzer,
    LLMServiceScoreAnalyzer
)
from .scrapers import Scraper, PlaywrightScraper
from .results_management import (
    CrawlResultsManager,
    FsCrawlResultsManager,
    DhCrawlResultsManager,
)
from .state_management import (
    CrawlStateManager,
    MemoryCrawlStateManager,
    RedisCrawlStateManager,
    create_crawl_state_manager
)
from .utils import ScoreAnalyzerInfoUtil

__version__ = "1.0.0"
__all__ = [
    "Prospector",
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
    "FsCrawlResultsManager",
    "DhCrawlResultsManager",
    "CrawlStateManager",
    "MemoryCrawlStateManager",
    "RedisCrawlStateManager",
    "create_crawl_state_manager",
    "StoreCrawlRecordRequest",
    "PromptInput",
    "TopicListInput",
    "LLMScoringSpec",
    "FieldMap",
    "LLMGenerationInput",
    "LLMGenerationRequest",
    "LLMServiceScoreAnalyzer",
    "RunStateEnum",
    "RunState",
    "CrawlStatus",
    "ScoreAnalyzerInfoUtil",
]
