"""Persistent storage implementations for CrawlState."""

import json
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime

from ..models import CrawlSpec, RunState, RunStateEnum
from ..settings import CrawlStateStorageSettings


logger = logging.getLogger(__name__)


class CrawlStateStorage(ABC):
    """Abstract base class for crawl state storage backends."""
    
    @abstractmethod
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """Create a new crawl in storage."""
        pass
    
    @abstractmethod
    def delete_crawl(self, crawl_id: str) -> None:
        """Delete a crawl from storage."""
        pass
    
    @abstractmethod
    def add_state(self, crawl_id: str, run_state: RunState) -> None:
        """Add a new state to the crawl's history."""
        pass
    
    @abstractmethod
    def get_current_state(self, crawl_id: str) -> RunStateEnum:
        """Get the current run state of the crawl."""
        pass
    
    @abstractmethod
    def get_state_history(self, crawl_id: str) -> List[RunState]:
        """Get the complete state history."""
        pass
    
    @abstractmethod
    def add_urls_with_scores(self, crawl_id: str, url_scores: List[Tuple[float, str]]) -> None:
        """Add URLs with their scores to the frontier."""
        pass
    
    @abstractmethod
    def get_next_url(self, crawl_id: str) -> Optional[str]:
        """Get the next URL to process from the frontier."""
        pass
    
    @abstractmethod
    def is_url_visited(self, crawl_id: str, url: str) -> bool:
        """Check if a URL has been visited."""
        pass
    
    @abstractmethod
    def increment_crawled_count(self, crawl_id: str) -> None:
        """Increment the crawled URL count."""
        pass
    
    @abstractmethod
    def increment_processed_count(self, crawl_id: str) -> None:
        """Increment the processed page count."""
        pass
    
    @abstractmethod
    def increment_error_count(self, crawl_id: str) -> None:
        """Increment the error count."""
        pass
    
    @abstractmethod
    def get_status_counts(self, crawl_id: str) -> Tuple[int, int, int, int]:
        """Get thread-safe snapshot of status counts."""
        pass


class MemoryCrawlStateStorage(CrawlStateStorage):
    """In-memory storage implementation (original behavior)."""
    
    def __init__(self):
        self.crawls: Dict[str, dict] = {}
        self.lock = threading.Lock()
    
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """Create a new crawl in memory storage."""
        with self.lock:
            self.crawls[crawl_spec.id] = {
                'spec': crawl_spec,
                'frontier': [],  # List of (score, url) tuples, kept sorted
                'visited_urls': set(),
                'state_history': [],
                'crawled_count': 0,
                'processed_count': 0,
                'error_count': 0
            }
    
    def delete_crawl(self, crawl_id: str) -> None:
        """Delete a crawl from memory storage."""
        with self.lock:
            if crawl_id in self.crawls:
                del self.crawls[crawl_id]
    
    def add_state(self, crawl_id: str, run_state: RunState) -> None:
        """Add a new state to the crawl's history."""
        with self.lock:
            if crawl_id in self.crawls:
                self.crawls[crawl_id]['state_history'].append(run_state)
    
    def get_current_state(self, crawl_id: str) -> RunStateEnum:
        """Get the current run state of the crawl."""
        with self.lock:
            if crawl_id not in self.crawls:
                return RunStateEnum.CREATED
            history = self.crawls[crawl_id]['state_history']
            if not history:
                return RunStateEnum.CREATED
            return history[-1].state
    
    def get_state_history(self, crawl_id: str) -> List[RunState]:
        """Get the complete state history."""
        with self.lock:
            if crawl_id in self.crawls:
                return self.crawls[crawl_id]['state_history'].copy()
            return []
    
    def add_urls_with_scores(self, crawl_id: str, url_scores: List[Tuple[float, str]]) -> None:
        """Add URLs with their scores to the frontier."""
        with self.lock:
            if crawl_id not in self.crawls:
                return
            
            crawl_data = self.crawls[crawl_id]
            for score, url in url_scores:
                if url not in crawl_data['visited_urls']:
                    # Insert in sorted order (highest score first)
                    frontier = crawl_data['frontier']
                    inserted = False
                    for i, (existing_score, existing_url) in enumerate(frontier):
                        if existing_url == url:
                            # URL already in frontier, skip
                            inserted = True
                            break
                        if score > existing_score:
                            frontier.insert(i, (score, url))
                            inserted = True
                            break
                    if not inserted:
                        frontier.append((score, url))
    
    def get_next_url(self, crawl_id: str) -> Optional[str]:
        """Get the next URL to process from the frontier."""
        with self.lock:
            if crawl_id not in self.crawls:
                return None
            
            crawl_data = self.crawls[crawl_id]
            frontier = crawl_data['frontier']
            visited = crawl_data['visited_urls']
            
            while frontier:
                score, url = frontier.pop(0)  # Get highest scoring URL
                if url not in visited:
                    visited.add(url)
                    return url
            return None
    
    def is_url_visited(self, crawl_id: str, url: str) -> bool:
        """Check if a URL has been visited."""
        with self.lock:
            if crawl_id in self.crawls:
                return url in self.crawls[crawl_id]['visited_urls']
            return False
    
    def increment_crawled_count(self, crawl_id: str) -> None:
        """Increment the crawled URL count."""
        with self.lock:
            if crawl_id in self.crawls:
                self.crawls[crawl_id]['crawled_count'] += 1
    
    def increment_processed_count(self, crawl_id: str) -> None:
        """Increment the processed page count."""
        with self.lock:
            if crawl_id in self.crawls:
                self.crawls[crawl_id]['processed_count'] += 1
    
    def increment_error_count(self, crawl_id: str) -> None:
        """Increment the error count."""
        with self.lock:
            if crawl_id in self.crawls:
                self.crawls[crawl_id]['error_count'] += 1
    
    def get_status_counts(self, crawl_id: str) -> Tuple[int, int, int, int]:
        """Get thread-safe snapshot of status counts."""
        with self.lock:
            if crawl_id in self.crawls:
                crawl_data = self.crawls[crawl_id]
                return (
                    crawl_data['crawled_count'],
                    crawl_data['processed_count'],
                    crawl_data['error_count'],
                    len(crawl_data['frontier'])
                )
            return (0, 0, 0, 0)


class RedisCrawlStateStorage(CrawlStateStorage):
    """Redis-based storage implementation for high performance and persistence."""
    
    def __init__(self):
        self.settings = CrawlStateStorageSettings()
        try:
            import redis
            self.redis = redis.from_url(
                self.settings.redis_url,
                db=self.settings.redis_db,
                decode_responses=True
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Connected to Redis at {self.settings.redis_url}")
        except ImportError:
            raise ImportError("Redis package not installed. Install with: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def _key(self, crawl_id: str, suffix: str) -> str:
        """Generate Redis key with prefix."""
        return f"{self.settings.redis_key_prefix}:crawl:{crawl_id}:{suffix}"
    
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """Create a new crawl in Redis storage."""
        crawl_id = crawl_spec.id
        
        # Store crawl spec as JSON
        spec_key = self._key(crawl_id, "spec")
        self.redis.set(spec_key, crawl_spec.model_dump_json())
        
        # Initialize counters
        counters_key = self._key(crawl_id, "counters")
        self.redis.hset(counters_key, mapping={
            "crawled_count": 0,
            "processed_count": 0,
            "error_count": 0
        })
        
        # Initialize empty collections
        frontier_key = self._key(crawl_id, "frontier")
        visited_key = self._key(crawl_id, "visited")
        states_key = self._key(crawl_id, "states")
        
        # Ensure keys exist (Redis will create them when first used)
        self.redis.zadd(frontier_key, {}, nx=True)  # Empty sorted set
        self.redis.sadd(visited_key, "")  # Empty set with dummy value
        self.redis.srem(visited_key, "")  # Remove dummy value
        self.redis.lpush(states_key, "")  # Empty list with dummy value
        self.redis.lpop(states_key)  # Remove dummy value
    
    def delete_crawl(self, crawl_id: str) -> None:
        """Delete a crawl from Redis storage."""
        keys_to_delete = [
            self._key(crawl_id, "spec"),
            self._key(crawl_id, "frontier"),
            self._key(crawl_id, "visited"),
            self._key(crawl_id, "states"),
            self._key(crawl_id, "counters")
        ]
        self.redis.delete(*keys_to_delete)
    
    def add_state(self, crawl_id: str, run_state: RunState) -> None:
        """Add a new state to the crawl's history."""
        states_key = self._key(crawl_id, "states")
        state_json = run_state.model_dump_json()
        self.redis.rpush(states_key, state_json)
    
    def get_current_state(self, crawl_id: str) -> RunStateEnum:
        """Get the current run state of the crawl."""
        states_key = self._key(crawl_id, "states")
        latest_state_json = self.redis.lindex(states_key, -1)
        
        if latest_state_json:
            state_data = json.loads(latest_state_json)
            return RunStateEnum(state_data['state'])
        return RunStateEnum.CREATED
    
    def get_state_history(self, crawl_id: str) -> List[RunState]:
        """Get the complete state history."""
        states_key = self._key(crawl_id, "states")
        state_jsons = self.redis.lrange(states_key, 0, -1)
        
        states = []
        for state_json in state_jsons:
            state_data = json.loads(state_json)
            # Parse timestamp string back to datetime
            if isinstance(state_data['timestamp'], str):
                state_data['timestamp'] = datetime.fromisoformat(state_data['timestamp'].replace('Z', '+00:00'))
            states.append(RunState(**state_data))
        return states
    
    def add_urls_with_scores(self, crawl_id: str, url_scores: List[Tuple[float, str]]) -> None:
        """Add URLs with their scores to the frontier."""
        frontier_key = self._key(crawl_id, "frontier")
        visited_key = self._key(crawl_id, "visited")
        
        # Use Lua script for atomic operation
        lua_script = """
        local frontier_key = KEYS[1]
        local visited_key = KEYS[2]
        local url_scores = cjson.decode(ARGV[1])
        
        for i, item in ipairs(url_scores) do
            local score = item[1]
            local url = item[2]
            
            -- Only add if not visited
            if redis.call('SISMEMBER', visited_key, url) == 0 then
                redis.call('ZADD', frontier_key, score, url)
            end
        end
        """
        
        url_scores_json = json.dumps(url_scores)
        self.redis.eval(lua_script, 2, frontier_key, visited_key, url_scores_json)
    
    def get_next_url(self, crawl_id: str) -> Optional[str]:
        """Get the next URL to process from the frontier."""
        frontier_key = self._key(crawl_id, "frontier")
        visited_key = self._key(crawl_id, "visited")
        
        # Use Lua script for atomic pop-and-mark-visited
        lua_script = """
        local frontier_key = KEYS[1]
        local visited_key = KEYS[2]
        
        -- Get highest scoring URL (ZPOPMAX returns score and member)
        local result = redis.call('ZPOPMAX', frontier_key)
        if #result > 0 then
            local url = result[1]
            -- Add to visited set
            redis.call('SADD', visited_key, url)
            return url
        end
        return nil
        """
        
        result = self.redis.eval(lua_script, 2, frontier_key, visited_key)
        return result if result else None
    
    def is_url_visited(self, crawl_id: str, url: str) -> bool:
        """Check if a URL has been visited."""
        visited_key = self._key(crawl_id, "visited")
        return bool(self.redis.sismember(visited_key, url))
    
    def increment_crawled_count(self, crawl_id: str) -> None:
        """Increment the crawled URL count."""
        counters_key = self._key(crawl_id, "counters")
        self.redis.hincrby(counters_key, "crawled_count", 1)
    
    def increment_processed_count(self, crawl_id: str) -> None:
        """Increment the processed page count."""
        counters_key = self._key(crawl_id, "counters")
        self.redis.hincrby(counters_key, "processed_count", 1)
    
    def increment_error_count(self, crawl_id: str) -> None:
        """Increment the error count."""
        counters_key = self._key(crawl_id, "counters")
        self.redis.hincrby(counters_key, "error_count", 1)
    
    def get_status_counts(self, crawl_id: str) -> Tuple[int, int, int, int]:
        """Get thread-safe snapshot of status counts."""
        counters_key = self._key(crawl_id, "counters")
        frontier_key = self._key(crawl_id, "frontier")
        
        # Get all counters and frontier size atomically
        pipeline = self.redis.pipeline()
        pipeline.hgetall(counters_key)
        pipeline.zcard(frontier_key)
        results = pipeline.execute()
        
        counters = results[0]
        frontier_size = results[1]
        
        return (
            int(counters.get('crawled_count', 0)),
            int(counters.get('processed_count', 0)),
            int(counters.get('error_count', 0)),
            frontier_size
        )


def create_crawl_state_storage() -> CrawlStateStorage:
    """Factory function to create appropriate storage backend."""
    settings = CrawlStateStorageSettings()
    
    if settings.storage_type == "redis":
        return RedisCrawlStateStorage()
    elif settings.storage_type == "memory":
        return MemoryCrawlStateStorage()
    else:
        raise ValueError(f"Unknown storage type: {settings.storage_type}")
