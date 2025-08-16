"""Factory for creating crawl state manager instances."""

from .crawl_state_manager import CrawlStateManager
from .memory_crawl_state_manager import MemoryCrawlStateManager
from .redis_crawl_state_manager import RedisCrawlStateManager
from ..settings import CrawlStateManagerSettings


def create_crawl_state_manager() -> CrawlStateManager:
    """
    Create a crawl state manager instance based on settings.
    
    Returns:
        CrawlStateManager: Manager instance based on configuration
    """
    settings = CrawlStateManagerSettings()
    
    if settings.storage_type == "redis":
        return RedisCrawlStateManager()
    elif settings.storage_type == "memory":
        return MemoryCrawlStateManager()
    else:
        raise ValueError(f"Unknown storage type: {settings.storage_type}")
