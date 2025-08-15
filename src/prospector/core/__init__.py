"""core - Implementation of the Prospector core functionality."""

from .prospector import Prospector, CrawlState
from .models import (
    CrawlSpec,
    CrawlSeeds,
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
    "CrawlSeeds",
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
    "CrawlStorageHandler",
    "FsStoreHandler",
    "DhStoreHandler",
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
]
