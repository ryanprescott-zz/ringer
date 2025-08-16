"""Abstract base class for crawl state management."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from ..models import CrawlSpec, RunState, RunStateEnum


class CrawlStateManager(ABC):
    """Abstract base class for crawl state management backends."""
    
    @abstractmethod
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """
        Create a new crawl in storage.
        
        Args:
            crawl_spec: Specification for the crawl to create
        """
        pass
    
    @abstractmethod
    def delete_crawl(self, crawl_id: str) -> None:
        """
        Delete a crawl from storage.
        
        Args:
            crawl_id: ID of the crawl to delete
        """
        pass
    
    @abstractmethod
    def get_current_state(self, crawl_id: str) -> RunStateEnum:
        """
        Get the current run state of a crawl.
        
        Args:
            crawl_id: ID of the crawl
            
        Returns:
            Current run state
        """
        pass
    
    @abstractmethod
    def add_state(self, crawl_id: str, run_state: RunState) -> None:
        """
        Add a new state to the crawl's history.
        
        Args:
            crawl_id: ID of the crawl
            run_state: The RunState object to add
        """
        pass
    
    @abstractmethod
    def get_state_history(self, crawl_id: str) -> List[RunState]:
        """
        Get the complete state history for a crawl.
        
        Args:
            crawl_id: ID of the crawl
            
        Returns:
            List of RunState objects in chronological order
        """
        pass
    
    @abstractmethod
    def add_urls_with_scores(self, crawl_id: str, url_scores: List[Tuple[float, str]]) -> None:
        """
        Add URLs with their scores to the frontier.
        
        Args:
            crawl_id: ID of the crawl
            url_scores: List of (score, url) tuples
        """
        pass
    
    @abstractmethod
    def get_next_url(self, crawl_id: str) -> Optional[str]:
        """
        Get the next URL to process from the frontier.
        
        Args:
            crawl_id: ID of the crawl
            
        Returns:
            Next URL to process, or None if frontier is empty
        """
        pass
    
    @abstractmethod
    def is_url_visited(self, crawl_id: str, url: str) -> bool:
        """
        Check if a URL has been visited.
        
        Args:
            crawl_id: ID of the crawl
            url: URL to check
            
        Returns:
            True if URL has been visited
        """
        pass
    
    @abstractmethod
    def increment_crawled_count(self, crawl_id: str) -> None:
        """
        Thread-safe increment of crawled URL count.
        
        Args:
            crawl_id: ID of the crawl
        """
        pass
    
    @abstractmethod
    def increment_processed_count(self, crawl_id: str) -> None:
        """
        Thread-safe increment of processed page count.
        
        Args:
            crawl_id: ID of the crawl
        """
        pass
    
    @abstractmethod
    def increment_error_count(self, crawl_id: str) -> None:
        """
        Thread-safe increment of error count.
        
        Args:
            crawl_id: ID of the crawl
        """
        pass
    
    @abstractmethod
    def get_status_counts(self, crawl_id: str) -> Tuple[int, int, int, int]:
        """
        Get thread-safe snapshot of status counts.
        
        Args:
            crawl_id: ID of the crawl
            
        Returns:
            Tuple of (crawled_count, processed_count, error_count, frontier_size)
        """
        pass
