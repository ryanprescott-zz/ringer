"""Settings for the Prospector application."""

import os
from enum import Enum
from typing import Dict, List
from pydantic_settings import BaseSettings


class HandlerType(str, Enum):
    """Enum for crawl record handler types."""
    FILE_SYSTEM = "file_system"
    DH = "dh"


class ProspectorSettings(BaseSettings):
    """Settings for the main Prospector application."""
    
    max_workers: int = 10
    prohibited_file_types: List[str] = []
    handler_type: HandlerType = HandlerType.FILE_SYSTEM
    
    model_config = {
        "env_prefix": "prospector_"
    }


class PlaywrightScraperSettings(BaseSettings):
    """Settings for the Playwright web scraper."""
    
    timeout: int = 60
    user_agent: str = "Prospector/1.0"
    javascript_enabled: bool = True
    
    model_config = {
        "env_prefix": "playwright_scraper_"
    }


class LLMServiceScoreAnalyzerSettings(BaseSettings):
    """Settings for score analyzers."""
    
    llm_service_url: str = "http://localhost:8000/score"
    llm_request_timeout: int = 60
    llm_default_prompt_template: str = "Please score the vtext content on a scale from 0.0 to 1.0 based on how much the content deals with one or more of the following topics. A score of 1.0 indicates that one or more of the topics is appears extensively in the text. Here are the topics: "
    llm_output_format: Dict[str, str] = {"score": "string"}
    
    model_config = {
        "env_prefix": "llm_service_score_analyzer_"
    }


class FsCrawlResultsManagerSettings(BaseSettings):
    """Settings for Filesystem data storage handling of crawl records."""
    
    # Crawl result storage directory
    crawl_data_dir: str = "./crawl_data"

    model_config = {
        "env_prefix": "fs_crawl_results_manager_"
    }

class DhCrawlResultsManagerSettings(BaseSettings):
    """Settings for service call storage of crawl records."""

    # Service handler settings
    service_url: str = "http://localhost:8000/handle_record"
    service_timeout_sec: int = 30
    service_max_retries: int = 3
    service_retry_exponential_base: int = 2

    model_config = {
        "env_prefix": "dh_crawl_results_manager_"
    }


class SearchEngineSettings(BaseSettings):
    """Settings for search engine integration."""
    
    google_base_url: str = "https://www.google.com/search"
    bing_base_url: str = "https://www.bing.com/search"
    duckduckgo_base_url: str = "https://duckduckgo.com/"
    
    request_timeout: int = 30
    rate_limit_delay: float = 2.0
    max_retries: int = 3
    
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    model_config = {
        "env_prefix": "search_engine_"
    }


class CrawlStateManagerSettings(BaseSettings):
    """Settings for crawl state management."""
    
    storage_type: str = "memory"  # "redis", "sqlite", "memory"
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_key_prefix: str = "prospector"
    sqlite_path: str = "./crawl_state.db"
    
    model_config = {
        "env_prefix": "crawl_state_manager_"
    }


class ProspectorServiceSettings(BaseSettings):
    """Settings for the FastAPI web service."""
    
    base_router_path: str = "/api/v1"
    openapi_prefix: str = "/api/static"
    model_config = {
        "env_prefix": "prospector_service_"
    }
