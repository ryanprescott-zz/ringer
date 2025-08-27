"""CrawlResultsManager - Abstract base class for handling crawl records."""

from abc import ABC, abstractmethod

from typing import List
from ringer.core.models import (
    CrawlRecord,
    CrawlSpec,
    CrawlResultsId
)

class CrawlResultsManager(ABC):
    """Abstract base class for crawl results processing."""
    
    @abstractmethod
    def create_crawl(self, crawl_spec: CrawlSpec, results_id: 'CrawlResultsId') -> None:
        """
        Create a new crawl with the given spec and results ID.
        
        Args:
            crawl_spec: Specification of the crawl to create.
            results_id: Identifier for the crawl results data set.
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError


    @abstractmethod
    def store_record(self, crawl_record: CrawlRecord, results_id: CrawlResultsId, crawl_id: str) -> None:
        """
        Store a crawl record.
        
        Args:
            crawl_record: The crawl record to process
            results_id: Identifier for the crawl results data set
            crawl_id: Unique identifier for the crawl
        Raises:
            NotImplementedError: If not implemented by subclass
        """

        raise NotImplementedError


    @abstractmethod
    def delete_crawl(self, results_id: CrawlResultsId) -> None:
        """
        Delete a crawl by results ID.
        
        Args:
            results_id: the results ID of the crawl to delete.

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        
        raise NotImplementedError

    @abstractmethod
    def get_crawl_records(self, results_id: CrawlResultsId, record_count: int, score_type: str) -> List[CrawlRecord]:
        """
        Get crawl records sorted by score type.
        
        Args:
            results_id: Identifier for the crawl results data set
            record_count: Number of records to return
            score_type: Type of score to sort by ('composite' or analyzer name)
            
        Returns:
            List of CrawlRecord objects sorted by score in descending order
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError
