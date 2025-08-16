"""Storage implementations for Prospector."""

from .crawl_state_storage import CrawlStateStorage
from .memory_crawl_state_storage import MemoryCrawlStateStorage
from .redis_crawl_state_storage import RedisCrawlStateStorage
from .storage_factory import create_crawl_state_storage

__version__ = "1.0.0"
__all__ = [
    "CrawlStateStorage",
    "MemoryCrawlStateStorage", 
    "RedisCrawlStateStorage",
    "create_crawl_state_storage"
]
