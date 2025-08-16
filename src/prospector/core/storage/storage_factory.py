"""Factory for creating crawl state storage instances."""

from .crawl_state_storage import CrawlStateStorage
from .memory_crawl_state_storage import MemoryCrawlStateStorage
from .redis_crawl_state_storage import RedisCrawlStateStorage
from ..settings import CrawlStateStorageSettings


def create_crawl_state_storage() -> CrawlStateStorage:
    """
    Create a crawl state storage instance based on settings.
    
    Returns:
        CrawlStateStorage: Storage instance based on configuration
    """
    settings = CrawlStateStorageSettings()
    
    if settings.storage_type == "redis":
        return RedisCrawlStateStorage()
    elif settings.storage_type == "memory":
        return MemoryCrawlStateStorage()
    else:
        raise ValueError(f"Unknown storage type: {settings.storage_type}")
