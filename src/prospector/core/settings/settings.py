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
    
    timeout: int = 30
    user_agent: str = "Prospector/1.0"
    javascript_enabled: bool = True
    
    model_config = {
        "env_prefix": "playwright_scraper_"
    }


class LLMServiceScoreAnalyzerSettings(BaseSettings):
    """Settings for score analyzers."""
    
    llm_service_url: str = "http://localhost:8000/score"
    llm_request_timeout: int = 60
    llm_default_prompt: str = "Please score the relevance and quality of the following text content on a scale from 0.0 to 1.0, where 1.0 represents highly relevant and high-quality content:"
    llm_model_output_format: Dict[str, str] = {"score": "string"}
    
    model_config = {
        "env_prefix": "llm_service_score_analyzer_"
    }


class FsStoreHandlerSettings(BaseSettings):
    """Settings for Filesystem data storage handlng of crawl records."""
    
    # Crawl result storage directory
    output_directory: str = "./crawl_data"

    # Record storage directory
    record_directory: str = "records"

    model_config = {
        "env_prefix": "fs_store_handler_"
    }

class ServiceCallHandlerSettings(BaseSettings):
    """Settings for service call storage of crawl records."""

    # Service handler settings
    service_url: str = "http://localhost:8000/handle_record"
    service_timeout_sec: int = 30
    service_max_retries: int = 3
    service_retry_exponential_base: int = 2

    model_config = {
        "env_prefix": "service_call_handler_"
    }


class ProspectorServiceSettings(BaseSettings):
    """Settings for the FastAPI web service."""
    
    base_router_path: str = "/api/v1"
    openapi_prefix: str = "/api/static"
    model_config = {
        "env_prefix": "prospector_service_"
    }
