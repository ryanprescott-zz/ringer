"""Storage implementations for Prospector."""

from .crawl_state_storage import (
    CrawlStateStorage,
    MemoryCrawlStateStorage,
    RedisCrawlStateStorage,
    create_crawl_state_storage
)

__version__ = "1.0.0"
__all__ = [
    "CrawlStateStorage",
    "MemoryCrawlStateStorage", 
    "RedisCrawlStateStorage",
    "create_crawl_state_storage"
]
