"""Redis implementation of crawl state management."""

import json
import logging
import threading
import redis
from datetime import datetime
from typing import List, Optional, Tuple

from .crawl_state_manager import CrawlStateManager
from ..models import CrawlSpec, RunState, RunStateEnum
from ..settings import CrawlStateManagerSettings


logger = logging.getLogger(__name__)


class RedisCrawlStateManager(CrawlStateManager):
    """Redis-based storage implementation for high performance and persistence."""
    
    def __init__(self):
        self.settings = CrawlStateManagerSettings()
        try:
            self.redis = redis.Redis(
                host=getattr(self.settings, 'redis_host', 'localhost'),
                port=getattr(self.settings, 'redis_port', 6379),
                db=getattr(self.settings, 'redis_db', 0),
                decode_responses=True
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Connected to Redis")
        except ImportError:
            raise ImportError("Redis package not installed. Install with: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def _key(self, crawl_id: str, suffix: str) -> str:
        """Generate Redis key with prefix."""
        return f"crawl:{crawl_id}:{suffix}"
    
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """Create a new crawl in Redis storage."""
        crawl_id = crawl_spec.id
        
        # Store crawl spec
        spec_key = self._key(crawl_id, "spec")
        self.redis.hset(spec_key, "spec", json.dumps(crawl_spec.model_dump(), default=str))
        
        # Initialize counters
        counters_key = self._key(crawl_id, "counters")
        self.redis.hset(counters_key, "queued", 0)
        self.redis.hset(counters_key, "crawled", 0)
        self.redis.hset(counters_key, "processed", 0)
        self.redis.hset(counters_key, "errors", 0)
    
    def delete_crawl(self, crawl_id: str) -> None:
        """Delete a crawl from Redis storage."""
        pattern = f"crawl:{crawl_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
    
    def add_state(self, crawl_id: str, run_state: RunState) -> None:
        """Add a new state to the crawl's history."""
        states_key = self._key(crawl_id, "state")
        state_json = json.dumps(run_state.model_dump(), default=str)
        self.redis.lpush(states_key, state_json)
    
    def get_current_state(self, crawl_id: str) -> RunStateEnum:
        """Get the current run state of the crawl."""
        states_key = self._key(crawl_id, "state")
        if self.redis.llen(states_key) > 0:
            latest_state_json = self.redis.lindex(states_key, 0)
            if latest_state_json:
                state_data = json.loads(latest_state_json)
                return RunStateEnum(state_data['state'])
        return RunStateEnum.CREATED
    
    def get_state_history(self, crawl_id: str) -> List[RunState]:
        """Get the complete state history."""
        states_key = self._key(crawl_id, "state")
        state_jsons = self.redis.lrange(states_key, 0, -1)
        
        states = []
        for state_json in state_jsons:
            if isinstance(state_json, bytes):
                state_json = state_json.decode('utf-8')
            state_data = json.loads(state_json)
            # Parse timestamp string back to datetime
            if isinstance(state_data['timestamp'], str):
                state_data['timestamp'] = datetime.fromisoformat(state_data['timestamp'].replace('Z', '+00:00'))
            states.append(RunState(**state_data))
        return states
    
    def add_urls_with_scores(self, crawl_id: str, url_scores: List[Tuple[float, str]]) -> None:
        """Add URLs with their scores to the frontier."""
        urls_key = self._key(crawl_id, "urls")
        counters_key = self._key(crawl_id, "counters")
        
        # Convert to Redis zadd format: {url: score}
        url_score_dict = {url: score for score, url in url_scores}
        self.redis.zadd(urls_key, url_score_dict)
        
        # Update queued counter
        self.redis.hincrby(counters_key, "queued", len(url_scores))
    
    def get_next_url(self, crawl_id: str) -> Optional[str]:
        """Get the next URL to process from the frontier."""
        urls_key = self._key(crawl_id, "urls")
        visited_key = self._key(crawl_id, "visited")
        
        # Get highest scoring URL
        result = self.redis.zpopmax(urls_key)
        if result:
            url = result[0][0]  # zpopmax returns [(member, score)]
            # Mark as visited
            self.redis.sadd(visited_key, url)
            return url
        return None
    
    def is_url_visited(self, crawl_id: str, url: str) -> bool:
        """Check if a URL has been visited."""
        visited_key = self._key(crawl_id, "visited")
        return bool(self.redis.sismember(visited_key, url))
    
    def increment_crawled_count(self, crawl_id: str) -> None:
        """Increment the crawled URL count."""
        counters_key = self._key(crawl_id, "counters")
        self.redis.hincrby(counters_key, "crawled", 1)
    
    def increment_processed_count(self, crawl_id: str) -> None:
        """Increment the processed page count."""
        counters_key = self._key(crawl_id, "counters")
        self.redis.hincrby(counters_key, "processed", 1)
    
    def increment_error_count(self, crawl_id: str) -> None:
        """Increment the error count."""
        counters_key = self._key(crawl_id, "counters")
        self.redis.hincrby(counters_key, "errors", 1)
    
    def get_status_counts(self, crawl_id: str) -> Tuple[int, int, int, int]:
        """Get thread-safe snapshot of status counts."""
        counters_key = self._key(crawl_id, "counters")
        
        # Get all counter values
        values = self.redis.hmget(counters_key, "queued", "crawled", "processed", "errors")
        
        # Convert bytes to int, handling None values
        def safe_int(val):
            if val is None:
                return 0
            if isinstance(val, bytes):
                return int(val.decode('utf-8'))
            return int(val)
        
        return tuple(safe_int(val) for val in values)
