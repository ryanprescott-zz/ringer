"""Results management package for handling crawl record storage."""

from .crawl_results_manager import CrawlResultsManager
from .fs_crawl_results_manager import FsCrawlResultsManager
from .dh_crawl_results_manager import DhCrawlResultsManager
from .crawl_results_manager_factory import create_crawl_results_manager

__all__ = [
    "CrawlResultsManager",
    "FsCrawlResultsManager", 
    "DhCrawlResultsManager"
]
