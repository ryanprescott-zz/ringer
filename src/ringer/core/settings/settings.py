"""Settings for the Ringer application."""

import os
from enum import Enum
from typing import Dict, List
from pydantic_settings import BaseSettings


class ResultsManagerType(str, Enum):
    """Enum for crawl results manager types."""
    FILE_SYSTEM = "file_system"
    DH = "dh"
    SQLITE = "sqlite"


class RingerSettings(BaseSettings):
    """Settings for the main Ringer application."""
    
    max_workers: int = 10
    prohibited_file_types: List[str] = []
    
    model_config = {
        "env_prefix": "ringer_"
    }


class PlaywrightScraperSettings(BaseSettings):
    """Settings for the Playwright web scraper."""
    
    timeout: int = 60
    user_agent: str = "Ringer/1.0"
    javascript_enabled: bool = True
    proxy_server: str|None = None
    
    model_config = {
        "env_prefix": "playwright_scraper_"
    }


class DhLlmScoreAnalyzerSettings(BaseSettings):
    """Settings for score analyzers."""
    
    service_url: str = "http://localhost:8000/score"
    request_timeout: int = 60
    default_prompt_template: str = "Please score the vtext content on a scale from 0.0 to 1.0 based on how much the content deals with one or more of the following topics. A score of 1.0 indicates that one or more of the topics is appears extensively in the text. Here are the topics: "
    output_format: Dict[str, str] = {"score": "string"}
    
    model_config = {
        "env_prefix": "dh_llm_score_analyzer_"
    }

class CrawlResultsManagerSettings(BaseSettings):
    """Settings for crawl results management."""
    
    manager_type: ResultsManagerType = ResultsManagerType.SQLITE

    model_config = {
        "env_prefix": "crawl_results_manager_"
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

    # DH crawl results manager settings
    service_url: str = "http://localhost:8000/"
    service_timeout_sec: int = 30
    service_max_retries: int = 3
    service_retry_exponential_base: int = 2

    model_config = {
        "env_prefix": "dh_crawl_results_manager_"
    }


class SQLiteCrawlResultsManagerSettings(BaseSettings):
    """Settings for SQLite database storage of crawl records."""
    
    database_path: str = "datastore/crawl_results.db"
    echo_sql: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    
    model_config = {
        "env_prefix": "sqlite_crawl_results_manager_"
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
    redis_key_prefix: str = "ringer"
    sqlite_path: str = "./crawl_state.db"
    
    model_config = {
        "env_prefix": "crawl_state_manager_"
    }


class RingerServiceSettings(BaseSettings):
    """Settings for the FastAPI web service."""
    
    base_router_path: str = "/api/v1"
    openapi_prefix: str = "/api/static"
    model_config = {
        "env_prefix": "ringer_service_"
    }
