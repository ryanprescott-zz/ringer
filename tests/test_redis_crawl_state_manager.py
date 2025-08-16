"""Tests for RedisCrawlStateManager."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Tuple

from prospector.core.state_managers.redis_crawl_state_manager import RedisCrawlStateManager
from prospector.core.models import CrawlSpec, RunState, RunStateEnum, WeightedKeyword
from prospector.core.score_analyzers import KeywordScoreAnalyzer


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_client.exists.return_value = False
    mock_client.hset.return_value = None
    mock_client.hget.return_value = None
    mock_client.hgetall.return_value = {}
    mock_client.llen.return_value = 0
    mock_client.lpush.return_value = None
    mock_client.rpop.return_value = None
    mock_client.sadd.return_value = None
    mock_client.sismember.return_value = False
    mock_client.hincrby.return_value = 1
    mock_client.delete.return_value = None
    mock_client.keys.return_value = []
    return mock_client


@pytest.fixture
def sample_crawl_spec():
    """Create a sample crawl specification."""
    return CrawlSpec(
        name="Test Crawl",
        seeds=["https://example.com"],
        max_pages=10,
        analyzer_specs=[
            {
                "type": "keyword",
                "name": "test_keyword_analyzer",
                "composite_weight": 1.0,
                "keywords": [
                    {"keyword": "test", "weight": 1.0}
                ]
            }
        ]
    )


@pytest.fixture
def sample_run_state():
    """Create a sample run state."""
    return RunState(
        state=RunStateEnum.RUNNING,
        timestamp=datetime.now(),
        message="Test message"
    )


class TestRedisCrawlStateManager:
    """Tests for RedisCrawlStateManager class."""
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_init_success(self, mock_redis_module, mock_redis):
        """Test successful initialization."""
        mock_redis_module.Redis.return_value = mock_redis
        
        manager = RedisCrawlStateManager()
        
        assert manager.redis == mock_redis
        mock_redis.ping.assert_called_once()
        mock_redis_module.Redis.assert_called_once()
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_init_connection_failure(self, mock_redis_module):
        """Test initialization with Redis connection failure."""
        mock_redis_instance = Mock()
        mock_redis_instance.ping.side_effect = Exception("Connection failed")
        mock_redis_module.Redis.return_value = mock_redis_instance
        
        with pytest.raises(Exception, match="Connection failed"):
            RedisCrawlStateManager()
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_key_generation(self, mock_redis_module, mock_redis):
        """Test Redis key generation."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        assert manager._key("test_crawl", "state") == "crawl:test_crawl:state"
        assert manager._key("another_crawl", "urls") == "crawl:another_crawl:urls"
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_create_crawl(self, mock_redis_module, mock_redis, sample_crawl_spec):
        """Test crawl creation."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        manager.create_crawl(sample_crawl_spec)
        
        # Verify spec was stored
        expected_key = f"crawl:{sample_crawl_spec.id}:spec"
        mock_redis.hset.assert_any_call(expected_key, "spec", json.dumps(sample_crawl_spec.model_dump(), default=str))
        
        # Verify counters were initialized
        counters_key = f"crawl:{sample_crawl_spec.id}:counters"
        mock_redis.hset.assert_any_call(counters_key, "queued", 0)
        mock_redis.hset.assert_any_call(counters_key, "crawled", 0)
        mock_redis.hset.assert_any_call(counters_key, "processed", 0)
        mock_redis.hset.assert_any_call(counters_key, "errors", 0)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_delete_crawl(self, mock_redis_module, mock_redis):
        """Test crawl deletion."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.keys.return_value = [
            b"crawl:test_crawl:spec",
            b"crawl:test_crawl:state",
            b"crawl:test_crawl:urls",
            b"crawl:test_crawl:visited",
            b"crawl:test_crawl:counters"
        ]
        
        manager = RedisCrawlStateManager()
        manager.delete_crawl("test_crawl")
        
        # Verify keys were found and deleted
        mock_redis.keys.assert_called_once_with("crawl:test_crawl:*")
        mock_redis.delete.assert_called_once_with(
            b"crawl:test_crawl:spec",
            b"crawl:test_crawl:state",
            b"crawl:test_crawl:urls",
            b"crawl:test_crawl:visited",
            b"crawl:test_crawl:counters"
        )
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_add_state(self, mock_redis_module, mock_redis, sample_run_state):
        """Test adding a run state."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        manager.add_state("test_crawl", sample_run_state)
        
        expected_key = "crawl:test_crawl:state"
        expected_data = json.dumps(sample_run_state.model_dump(), default=str)
        mock_redis.lpush.assert_called_once_with(expected_key, expected_data)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_get_current_state_with_states(self, mock_redis_module, mock_redis, sample_run_state):
        """Test getting current state when states exist."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.llen.return_value = 1
        mock_redis.lindex.return_value = json.dumps(sample_run_state.model_dump(), default=str)
        
        manager = RedisCrawlStateManager()
        result = manager.get_current_state("test_crawl")
        
        assert result == RunStateEnum.RUNNING
        mock_redis.lindex.assert_called_once_with("crawl:test_crawl:state", 0)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_get_current_state_no_states(self, mock_redis_module, mock_redis):
        """Test getting current state when no states exist."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.llen.return_value = 0
        
        manager = RedisCrawlStateManager()
        result = manager.get_current_state("test_crawl")
        
        assert result == RunStateEnum.CREATED
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_get_state_history(self, mock_redis_module, mock_redis, sample_run_state):
        """Test getting state history."""
        mock_redis_module.Redis.return_value = mock_redis
        state_data = json.dumps(sample_run_state.model_dump(), default=str)
        mock_redis.lrange.return_value = [state_data.encode(), state_data.encode()]
        
        manager = RedisCrawlStateManager()
        result = manager.get_state_history("test_crawl")
        
        assert len(result) == 2
        assert all(isinstance(state, RunState) for state in result)
        assert all(state.state == RunStateEnum.RUNNING for state in result)
        mock_redis.lrange.assert_called_once_with("crawl:test_crawl:state", 0, -1)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_add_urls_with_scores(self, mock_redis_module, mock_redis):
        """Test adding URLs with scores."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        url_scores = [(0.8, "https://example1.com"), (0.6, "https://example2.com")]
        manager.add_urls_with_scores("test_crawl", url_scores)
        
        # Verify URLs were added to priority queue (sorted set)
        urls_key = "crawl:test_crawl:urls"
        mock_redis.zadd.assert_called_once_with(urls_key, {
            "https://example1.com": 0.8,
            "https://example2.com": 0.6
        })
        
        # Verify counter was updated
        counters_key = "crawl:test_crawl:counters"
        mock_redis.hincrby.assert_called_once_with(counters_key, "queued", 2)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_get_next_url_with_urls(self, mock_redis_module, mock_redis):
        """Test getting next URL when URLs are available."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.zpopmax.return_value = [("https://example.com", 0.8)]
        
        manager = RedisCrawlStateManager()
        result = manager.get_next_url("test_crawl")
        
        assert result == "https://example.com"
        mock_redis.zpopmax.assert_called_once_with("crawl:test_crawl:urls")
        
        # Verify URL was marked as visited
        visited_key = "crawl:test_crawl:visited"
        mock_redis.sadd.assert_called_once_with(visited_key, "https://example.com")
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_get_next_url_no_urls(self, mock_redis_module, mock_redis):
        """Test getting next URL when no URLs are available."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.zpopmax.return_value = []
        
        manager = RedisCrawlStateManager()
        result = manager.get_next_url("test_crawl")
        
        assert result is None
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_is_url_visited_true(self, mock_redis_module, mock_redis):
        """Test checking if URL is visited (true case)."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.sismember.return_value = True
        
        manager = RedisCrawlStateManager()
        result = manager.is_url_visited("test_crawl", "https://example.com")
        
        assert result is True
        mock_redis.sismember.assert_called_once_with("crawl:test_crawl:visited", "https://example.com")
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_is_url_visited_false(self, mock_redis_module, mock_redis):
        """Test checking if URL is visited (false case)."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.sismember.return_value = False
        
        manager = RedisCrawlStateManager()
        result = manager.is_url_visited("test_crawl", "https://example.com")
        
        assert result is False
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_increment_crawled_count(self, mock_redis_module, mock_redis):
        """Test incrementing crawled count."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        manager.increment_crawled_count("test_crawl")
        
        mock_redis.hincrby.assert_called_once_with("crawl:test_crawl:counters", "crawled", 1)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_increment_processed_count(self, mock_redis_module, mock_redis):
        """Test incrementing processed count."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        manager.increment_processed_count("test_crawl")
        
        mock_redis.hincrby.assert_called_once_with("crawl:test_crawl:counters", "processed", 1)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_increment_error_count(self, mock_redis_module, mock_redis):
        """Test incrementing error count."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        manager.increment_error_count("test_crawl")
        
        mock_redis.hincrby.assert_called_once_with("crawl:test_crawl:counters", "errors", 1)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_get_status_counts(self, mock_redis_module, mock_redis):
        """Test getting status counts."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.hmget.return_value = [b'10', b'5', b'3', b'1']
        
        manager = RedisCrawlStateManager()
        result = manager.get_status_counts("test_crawl")
        
        assert result == (10, 5, 3, 1)
        mock_redis.hmget.assert_called_once_with(
            "crawl:test_crawl:counters", 
            "queued", "crawled", "processed", "errors"
        )
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_get_status_counts_missing_values(self, mock_redis_module, mock_redis):
        """Test getting status counts with missing values."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.hmget.return_value = [None, b'5', None, b'1']
        
        manager = RedisCrawlStateManager()
        result = manager.get_status_counts("test_crawl")
        
        assert result == (0, 5, 0, 1)
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_duplicate_url_handling(self, mock_redis_module, mock_redis):
        """Test that duplicate URLs are handled correctly."""
        mock_redis_module.Redis.return_value = mock_redis
        manager = RedisCrawlStateManager()
        
        # Add same URL twice with different scores
        url_scores1 = [(0.8, "https://example.com")]
        url_scores2 = [(0.9, "https://example.com")]
        
        manager.add_urls_with_scores("test_crawl", url_scores1)
        manager.add_urls_with_scores("test_crawl", url_scores2)
        
        # Redis sorted sets should handle duplicates by updating the score
        assert mock_redis.zadd.call_count == 2
    
    @patch('prospector.core.state_managers.redis_crawl_state_manager.redis')
    def test_redis_connection_error_handling(self, mock_redis_module, mock_redis):
        """Test handling of Redis connection errors during operations."""
        mock_redis_module.Redis.return_value = mock_redis
        mock_redis.zadd.side_effect = Exception("Redis connection lost")
        
        manager = RedisCrawlStateManager()
        
        # Should raise the Redis exception
        with pytest.raises(Exception, match="Redis connection lost"):
            manager.add_urls_with_scores("test_crawl", [(0.8, "https://example.com")])
