"""handlers - Implementation of handlers for Prospector."""

from .crawl_storage_handler import CrawlStorageHandler
from .fs_store_handler import FsStoreHandler
from .dh_store_handler import DhStoreHandler

__version__ = "1.0.0"
__all__ = [
    "CrawlRecordHandler",
    "FsStoreHandler",
    "DhStoreHandler",
]