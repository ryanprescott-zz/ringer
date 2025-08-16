"""Tests for main Prospector class."""

import pytest
from unittest.mock import Mock, patch
import threading
import time

from prospector.core import (
    Prospector,
    CrawlState,
    CrawlSpec,
    AnalyzerSpec,
    WeightedKeyword,
    RunStateEnum,
)
from prospector.core.models import (
    KeywordScoringSpec,
    LLMScoringSpec,
    TopicListInput,
)


class TestCrawlState:
    """Tests for CrawlState class."""
    
    def test_init(self, sample_crawl_spec):
        """Test CrawlState initialization."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        assert state.crawl_spec == sample_crawl_spec
        assert len(state.analyzers) == 0
        assert state.current_state == RunStateEnum.CREATED
        
        # Check that counters are initialized to 0
        crawled, processed, errors, frontier_size = state.get_status_counts()
        assert crawled == 0
        assert processed == 0
        assert errors == 0
        assert frontier_size == 0
    
    def test_add_urls_with_scores(self, sample_crawl_spec):
        """Test adding URLs with scores to frontier."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        url_scores = [(0.8, "https://test1.com"), (0.6, "https://test2.com")]
        state.add_urls_with_scores(url_scores)
        
        # Check that URLs were added to frontier
        crawled, processed, errors, frontier_size = state.get_status_counts()
        assert frontier_size == 2
        
        # Check that higher score comes first
        first_url = state.get_next_url()
        assert first_url == "https://test1.com"  # Should be the higher scored URL
    
    def test_get_next_url(self, sample_crawl_spec):
        """Test getting next URL from frontier."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        # Add some URLs with different scores
        url_scores = [(0.8, "https://high.com"), (0.2, "https://low.com")]
        state.add_urls_with_scores(url_scores)
        
        # Should get highest scoring URL first
        next_url = state.get_next_url()
        assert next_url == "https://high.com"
        
        # Check that frontier size decreased
        crawled, processed, errors, frontier_size = state.get_status_counts()
        assert frontier_size == 1
    
    def test_get_next_url_empty_frontier(self, sample_crawl_spec):
        """Test getting next URL when frontier is empty."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        # Frontier should be empty initially
        next_url = state.get_next_url()
        assert next_url is None
    
    def test_frontier_duplicate_urls(self, sample_crawl_spec):
        """Test that frontier prevents duplicate URLs."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        # Add same URL with different scores
        url_scores = [(0.8, "https://test.com"), (0.6, "https://test.com")]
        state.add_urls_with_scores(url_scores)
        
        # Should only contain one instance of the URL
        crawled, processed, errors, frontier_size = state.get_status_counts()
        assert frontier_size == 1
        
        # Should get the URL when requested
        next_url = state.get_next_url()
        assert next_url == "https://test.com"
    
    def test_is_url_allowed_domain_blacklist(self, sample_crawl_spec):
        """Test URL filtering with domain blacklist."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        # Should allow URLs not in blacklist
        assert state.is_url_allowed("https://example.com/page")
        
        # Should block URLs in blacklist
        assert not state.is_url_allowed("https://spam.com/page")
    
    def test_is_url_allowed_no_blacklist(self, sample_analyzer_spec):
        """Test URL filtering with no domain blacklist."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        spec = CrawlSpec(
            name="test",
            seeds=["https://example.com"],
            analyzer_specs=[sample_analyzer_spec],
            domain_blacklist=None
        )
        storage = MemoryCrawlStateStorage()
        state = CrawlState(spec, storage)
        
        # Should allow all URLs when no blacklist
        assert state.is_url_allowed("https://any-domain.com/page")
    
    def test_counter_methods(self, sample_crawl_spec):
        """Test thread-safe counter increment methods."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        # Test increment methods
        state.increment_crawled_count()
        state.increment_processed_count()
        state.increment_error_count()
        
        crawled, processed, errors, frontier_size = state.get_status_counts()
        assert crawled == 1
        assert processed == 1
        assert errors == 1
        
        # Test multiple increments
        state.increment_crawled_count()
        state.increment_crawled_count()
        crawled, processed, errors, frontier_size = state.get_status_counts()
        assert crawled == 3
    
    def test_get_status_counts(self, sample_crawl_spec):
        """Test getting thread-safe status counts."""
        from prospector.core.storage.memory_crawl_state_storage import MemoryCrawlStateStorage
        storage = MemoryCrawlStateStorage()
        state = CrawlState(sample_crawl_spec, storage)
        
        # Add some URLs to frontier
        state.add_urls_with_scores([(0.8, "https://test1.com"), (0.6, "https://test2.com")])
        
        # Increment counters
        state.increment_crawled_count()
        state.increment_processed_count()
        state.increment_error_count()
        
        # Get status counts
        crawled, processed, errors, frontier_size = state.get_status_counts()
        
        assert crawled == 1
        assert processed == 1
        assert errors == 1
        assert frontier_size == 2


class TestProspector:
    """Tests for Prospector class."""
    
    def test_init(self):
        """Test Prospector initialization."""
        prospector = Prospector()
        
        assert len(prospector.crawls) == 0
        assert prospector.scraper is not None
        assert prospector.handler is not None
        assert prospector.executor is not None
    
    def test_create_crawl(self, prospector, sample_crawl_spec):
        """Test creating a new crawl."""
        crawl_id, run_state = prospector.create(sample_crawl_spec)
        
        assert crawl_id == sample_crawl_spec.id
        assert crawl_id in prospector.crawls
        assert run_state.state == RunStateEnum.CREATED
        
        crawl_state = prospector.crawls[crawl_id]
        assert crawl_state.crawl_spec == sample_crawl_spec
        assert len(crawl_state.analyzers) == 1
        assert crawl_state.current_state == RunStateEnum.CREATED
    
    def test_create_duplicate_crawl(self, prospector, sample_crawl_spec):
        """Test creating a crawl with duplicate ID raises error."""
        crawl_id, run_state = prospector.create(sample_crawl_spec)
        
        with pytest.raises(ValueError, match="already exists"):
            prospector.create(sample_crawl_spec)
    
    def test_create_crawl_with_llm_analyzer(self, prospector, sample_analyzer_spec):
        """Test creating a crawl with LLM analyzer."""
        llm_spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=0.5,
            scoring_input=TopicListInput(topics=["test", "example"])
        )
        
        crawl_spec = CrawlSpec(
            name="test_llm_crawl",
            seeds=["https://example.com"],
            analyzer_specs=[sample_analyzer_spec, llm_spec],
            worker_count=1
        )
        
        crawl_id, run_state = prospector.create(crawl_spec)
        
        assert crawl_id in prospector.crawls
        assert run_state.state == RunStateEnum.CREATED
        crawl_state = prospector.crawls[crawl_id]
        assert len(crawl_state.analyzers) == 2
        assert "LLMServiceScoreAnalyzer" in crawl_state.analyzer_weights
    
    def test_start_crawl(self, prospector, sample_crawl_spec, mock_scraper, mock_handler):
        """Test starting a crawl."""
        # Mock the scraper and handler
        prospector.scraper = mock_scraper
        prospector.handler = mock_handler
        
        crawl_id, create_state = prospector.create(sample_crawl_spec)
        start_crawl_id, start_state = prospector.start(crawl_id)
        
        assert start_crawl_id == crawl_id
        assert start_state.state == RunStateEnum.RUNNING
        crawl_state = prospector.crawls[crawl_id]
        assert crawl_state.current_state == RunStateEnum.RUNNING
    
    def test_start_nonexistent_crawl(self, prospector):
        """Test starting a non-existent crawl raises error."""
        with pytest.raises(ValueError, match="not found"):
            prospector.start("nonexistent_id")
    
    def test_start_already_running_crawl(self, prospector, sample_crawl_spec):
        """Test starting an already running crawl raises error."""
        crawl_id, create_state = prospector.create(sample_crawl_spec)
        
        # Manually set to running
        from prospector.core.models import RunState
        prospector.crawls[crawl_id].add_state(RunState(state=RunStateEnum.RUNNING))
        
        with pytest.raises(RuntimeError, match="already running"):
            prospector.start(crawl_id)
    
    def test_stop_crawl(self, prospector, sample_crawl_spec):
        """Test stopping a crawl."""
        crawl_id, create_state = prospector.create(sample_crawl_spec)
        from prospector.core.models import RunState
        prospector.crawls[crawl_id].add_state(RunState(state=RunStateEnum.RUNNING))  # Set to running
        
        stop_crawl_id, stop_state = prospector.stop(crawl_id)
        
        assert stop_crawl_id == crawl_id
        assert stop_state.state == RunStateEnum.STOPPED
        crawl_state = prospector.crawls[crawl_id]
        assert crawl_state.current_state == RunStateEnum.STOPPED
    
    def test_stop_crawl_not_running(self, prospector, sample_crawl_spec):
        """Test stopping a crawl that is not running raises error."""
        crawl_id, create_state = prospector.create(sample_crawl_spec)
        
        # Try to stop crawl that is in CREATED state
        with pytest.raises(RuntimeError, match="is not running"):
            prospector.stop(crawl_id)
        
        # Set to STOPPED and try again
        from prospector.core.models import RunState
        prospector.crawls[crawl_id].add_state(RunState(state=RunStateEnum.STOPPED))
        
        with pytest.raises(RuntimeError, match="is not running"):
            prospector.stop(crawl_id)
    
    def test_stop_nonexistent_crawl(self, prospector):
        """Test stopping a non-existent crawl raises error."""
        with pytest.raises(ValueError, match="not found"):
            prospector.stop("nonexistent_id")
    
    def test_delete_crawl(self, prospector, sample_crawl_spec):
        """Test deleting a crawl."""
        crawl_id, create_state = prospector.create(sample_crawl_spec)
        
        prospector.delete(crawl_id)
        
        assert crawl_id not in prospector.crawls
    
    def test_delete_nonexistent_crawl(self, prospector):
        """Test deleting a non-existent crawl raises error."""
        with pytest.raises(ValueError, match="not found"):
            prospector.delete("nonexistent_id")
    
    def test_delete_running_crawl(self, prospector, sample_crawl_spec):
        """Test deleting a running crawl raises error."""
        crawl_id, create_state = prospector.create(sample_crawl_spec)
        from prospector.core.models import RunState
        prospector.crawls[crawl_id].add_state(RunState(state=RunStateEnum.RUNNING))  # Set to running
        
        with pytest.raises(RuntimeError, match="Cannot delete running crawl"):
            prospector.delete(crawl_id)
    
    def test_get_crawl_status(self, prospector, sample_crawl_spec):
        """Test getting crawl status."""
        crawl_id, create_state = prospector.create(sample_crawl_spec)
        
        # Add some test data
        crawl_state = prospector.crawls[crawl_id]
        crawl_state.increment_crawled_count()
        crawl_state.increment_processed_count()
        crawl_state.add_urls_with_scores([(0.8, "https://test.com")])
        
        status_dict = prospector.get_crawl_status(crawl_id)
        
        assert status_dict["crawl_id"] == crawl_id
        assert status_dict["crawl_name"] == sample_crawl_spec.name
        assert status_dict["current_state"] == "CREATED"
        assert status_dict["crawled_count"] == 1
        assert status_dict["processed_count"] == 1
        assert status_dict["error_count"] == 0
        assert status_dict["frontier_size"] == 1
        # The state history may contain multiple CREATED states due to initialization
        assert len(status_dict["state_history"]) >= 1
        assert all(state["state"] == "CREATED" for state in status_dict["state_history"])
    
    def test_get_crawl_status_not_found(self, prospector):
        """Test getting status for non-existent crawl raises error."""
        with pytest.raises(ValueError, match="not found"):
            prospector.get_crawl_status("nonexistent_id")
    
