"""Results management package for handling crawl record storage."""

from .crawl_results_manager import CrawlResultsManager
from .dh_crawl_results_manager import DhCrawlResultsManager
from .sqlite_crawl_results_manager import SQLiteCrawlResultsManager
from .crawl_results_manager_factory import create_crawl_results_manager

__all__ = [
    "CrawlResultsManager",
    "DhCrawlResultsManager",
    "SQLiteCrawlResultsManager",
    "create_crawl_results_manager"
]
