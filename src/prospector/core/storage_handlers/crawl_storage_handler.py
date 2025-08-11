"""CrawlRecordHandler - Abstract base class for handling crawl records."""

from abc import ABC, abstractmethod

from prospector.core.models import (
    CrawlRecord,
    CrawlSpec

)

class CrawlStorageHandler(ABC):
    """Abstract base class for crawl storage processing."""
    
    @abstractmethod
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """
        Create a new crawl with the given spec.
        
        Args:
            crawl_spec: Specification of the crawl to create.
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


    @abstractmethod
    def store_record(self, crawl_record: CrawlRecord, crawl_name: str) -> None:
        """
        Store a crawl record.
        
        Args:
            crawl_record: The crawl record to process
            crawl_name: Name of the crawl
        Raises:
            NotImplementedError: If not implemented by subclass
        """

        raise NotImplementedError


    @abstractmethod
    def delete_crawl(self, crawl_name: str) -> None:
        """
        Delete a crawl by crawl name.
        
        Args:
            crawl_name: the name of the crawl to delete.

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        
        raise NotImplementedError
