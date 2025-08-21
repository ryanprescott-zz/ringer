"""Factory for creating crawl results manager instances."""

from .crawl_results_manager import CrawlResultsManager
from .fs_crawl_results_manager import FsCrawlResultsManager
from .dh_crawl_results_manager import DhCrawlResultsManager
from ..settings import CrawlResultsManagerSettings, ResultsManagerType


def create_crawl_results_manager() -> CrawlResultsManager:
    """
    Create a crawl results manager instance based on settings.
    
    Returns:
        CrawlResultsManager: Manager instance based on configuration
    """
    settings = CrawlResultsManagerSettings()
    
    if settings.manager_type == ResultsManagerType.FILE_SYSTEM:
        return FsCrawlResultsManager()
    elif settings.manager_type == ResultsManagerType.DH:
        return DhCrawlResultsManager()
    else:
        raise ValueError(f"Unknown results manager type: {settings.manager_type}")
