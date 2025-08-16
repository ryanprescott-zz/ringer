"""In-memory implementation of crawl state storage."""

import threading
from typing import Dict, List, Optional, Tuple
from sortedcontainers import SortedSet

from .crawl_state_storage import CrawlStateStorage
from ..models import CrawlSpec, RunState, RunStateEnum


class ScoreUrlTuple:
    """A tuple-like class that sorts by score but compares equality by URL."""
    
    def __init__(self, score: float, url: str):
        self.score = score
        self.url = url
    
    def __lt__(self, other):
        # Sort by score descending (higher scores first)
        return self.score > other.score
    
    def __eq__(self, other):
        # Equality based on URL for uniqueness
        return self.url == other.url
    
    def __hash__(self):
        # Hash based on URL for set operations
        return hash(self.url)
    
    def __repr__(self):
        return f"ScoreUrlTuple({self.score}, '{self.url}')"
    
    def __iter__(self):
        # Allow tuple unpacking: score, url = tuple_obj
        yield self.score
        yield self.url


class MemoryCrawlStateStorage(CrawlStateStorage):
    """In-memory implementation of crawl state storage."""
    
    def __init__(self):
        """Initialize the memory storage."""
        self._lock = threading.RLock()
        self._crawls: Dict[str, Dict] = {}
    
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """Create a new crawl in memory storage."""
        with self._lock:
            crawl_id = crawl_spec.id
            if crawl_id in self._crawls:
                raise ValueError(f"Crawl {crawl_id} already exists")
            
            self._crawls[crawl_id] = {
                'spec': crawl_spec,
                'state_history': [RunState(state=RunStateEnum.CREATED)],
                'frontier': SortedSet(),
                'visited_urls': set(),
                'crawled_count': 0,
                'processed_count': 0,
                'error_count': 0,
            }
    
    def delete_crawl(self, crawl_id: str) -> None:
        """Delete a crawl from memory storage."""
        with self._lock:
            if crawl_id in self._crawls:
                del self._crawls[crawl_id]
    
    def get_current_state(self, crawl_id: str) -> RunStateEnum:
        """Get the current run state of a crawl."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            state_history = self._crawls[crawl_id]['state_history']
            return state_history[-1].state if state_history else RunStateEnum.CREATED
    
    def add_state(self, crawl_id: str, run_state: RunState) -> None:
        """Add a new state to the crawl's history."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            self._crawls[crawl_id]['state_history'].append(run_state)
    
    def get_state_history(self, crawl_id: str) -> List[RunState]:
        """Get the complete state history for a crawl."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            return self._crawls[crawl_id]['state_history'].copy()
    
    def add_urls_with_scores(self, crawl_id: str, url_scores: List[Tuple[float, str]]) -> None:
        """Add URLs with their scores to the frontier."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            frontier = self._crawls[crawl_id]['frontier']
            visited_urls = self._crawls[crawl_id]['visited_urls']
            
            for score, url in url_scores:
                if url not in visited_urls:
                    score_url_tuple = ScoreUrlTuple(score, url)
                    frontier.add(score_url_tuple)
    
    def get_next_url(self, crawl_id: str) -> Optional[str]:
        """Get the next URL to process from the frontier."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            frontier = self._crawls[crawl_id]['frontier']
            visited_urls = self._crawls[crawl_id]['visited_urls']
            
            if not frontier:
                return None
            
            # Get highest scoring URL
            score_url_tuple = frontier.pop(0)
            url = score_url_tuple.url
            visited_urls.add(url)
            
            return url
    
    def is_url_visited(self, crawl_id: str, url: str) -> bool:
        """Check if a URL has been visited."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            return url in self._crawls[crawl_id]['visited_urls']
    
    def increment_crawled_count(self, crawl_id: str) -> None:
        """Thread-safe increment of crawled URL count."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            self._crawls[crawl_id]['crawled_count'] += 1
    
    def increment_processed_count(self, crawl_id: str) -> None:
        """Thread-safe increment of processed page count."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            self._crawls[crawl_id]['processed_count'] += 1
    
    def increment_error_count(self, crawl_id: str) -> None:
        """Thread-safe increment of error count."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            self._crawls[crawl_id]['error_count'] += 1
    
    def get_status_counts(self, crawl_id: str) -> Tuple[int, int, int, int]:
        """Get thread-safe snapshot of status counts."""
        with self._lock:
            if crawl_id not in self._crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            crawl_data = self._crawls[crawl_id]
            return (
                crawl_data['crawled_count'],
                crawl_data['processed_count'],
                crawl_data['error_count'],
                len(crawl_data['frontier'])
            )
