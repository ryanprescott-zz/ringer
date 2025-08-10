"""CrawlRecordHandler - Abstract base class for handling crawl records."""

from abc import ABC, abstractmethod

from prospector.core.models import CrawlRecord


class CrawlRecordHandler(ABC):
    """Abstract base class for crawl record handlers."""
    
    @abstractmethod
    def handle(self, crawl_record: CrawlRecord, crawl_name: str, crawl_datetime: str) -> None:
        """
        Process a crawl record.
        
        Args:
            crawl_record: The crawl record to process
            crawl_name: Name of the crawl
            crawl_datetime: Datetime string of the crawl
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError
