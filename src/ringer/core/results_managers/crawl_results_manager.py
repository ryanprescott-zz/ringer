"""CrawlResultsManager - Abstract base class for handling crawl records."""

from abc import ABC, abstractmethod

from typing import List
from ringer.core.models import (
    CrawlRecord,
    CrawlRecordSummary,
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
    def get_crawl_record_summaries(self, results_id: CrawlResultsId, record_count: int = 10, score_type: str = "composite") -> List[CrawlRecordSummary]:
        """
        Get crawl record summaries sorted by score type.
        
        Args:
            results_id: Identifier for the crawl results data set
            record_count: Number of record summaries to return (default: 10)
            score_type: Type of score to sort by ('composite' or analyzer name) (default: 'composite')
            
        Returns:
            List of CrawlRecordSummary objects sorted by score in descending order, 
            with score field containing the value used for sorting
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError

    @abstractmethod
    def get_crawl_records(self, results_id: CrawlResultsId, record_ids: List[str]) -> List[CrawlRecord]:
        """
        Get crawl records by their IDs.
        
        Args:
            results_id: Identifier for the crawl results data set
            record_ids: List of record IDs to retrieve
            
        Returns:
            List of CrawlRecord objects for the found record IDs
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError

    @abstractmethod
    def store_record(self, crawl_record, results_id: CrawlResultsId, crawl_id: str) -> None:
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

