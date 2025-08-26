"""CrawlResultsManager - Abstract base class for handling crawl records."""

from abc import ABC, abstractmethod

from ringer.core.models import (
    CrawlRecord,
    CrawlSpec,
    CrawlResultsId
)

class CrawlResultsManager(ABC):
    """Abstract base class for crawl results processing."""
    
    @abstractmethod
    def create_crawl(self, crawl_spec: CrawlSpec, results_id: 'CrawlResultsId') -> str:
        """
        Create a new crawl with the given spec and results ID.
        
        Args:
            crawl_spec: Specification of the crawl to create.
            results_id: Identifier for the crawl results data set.
            
        Returns:
            str: Storage ID for the created crawl
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


    @abstractmethod
    def store_record(self, crawl_record: CrawlRecord, storage_id: str) -> None:
        """
        Store a crawl record.
        
        Args:
            crawl_record: The crawl record to process
            storage_id: Storage ID for the crawl
        Raises:
            NotImplementedError: If not implemented by subclass
        """

        raise NotImplementedError


    @abstractmethod
    def delete_crawl(self, storage_id: str) -> None:
        """
        Delete a crawl by storage ID.
        
        Args:
            storage_id: the storage ID of the crawl to delete.

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        
        raise NotImplementedError
