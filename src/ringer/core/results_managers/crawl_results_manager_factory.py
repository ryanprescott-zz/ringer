"""Factory for creating crawl results manager instances."""

from .crawl_results_manager import CrawlResultsManager
from .dh_crawl_results_manager import DhCrawlResultsManager
from .sqlite_crawl_results_manager import SQLiteCrawlResultsManager
from ..settings import CrawlResultsManagerSettings, ResultsManagerType


def create_crawl_results_manager() -> CrawlResultsManager:
    """
    Create a crawl results manager instance based on settings.
    
    Returns:
        CrawlResultsManager: Manager instance based on configuration
    """
    settings = CrawlResultsManagerSettings()
    
    if settings.manager_type == ResultsManagerType.FILE_SYSTEM:
        raise ValueError("FILE_SYSTEM results manager type is deprecated. Use SQLITE instead.")
    elif settings.manager_type == ResultsManagerType.DH:
        return DhCrawlResultsManager()
    elif settings.manager_type == ResultsManagerType.SQLITE:
        return SQLiteCrawlResultsManager()
    else:
        raise ValueError(f"Unknown results manager type: {settings.manager_type}")
