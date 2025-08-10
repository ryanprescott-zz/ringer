"""handlers - Implementation of handlers for Prospector."""

from .crawl_record_handler import CrawlRecordHandler
from .fs_store_handler import FsStoreCrawlRecordHandler
from .service_call_handler import ServiceCrawlRecordHandler

__version__ = "1.0.0"
__all__ = [
    "CrawlRecordHandler",
    "FsStoreCrawlRecordHandler",
    "ServiceCrawlRecordHandler",
]