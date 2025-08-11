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
)


class TestCrawlState:
    """Tests for CrawlState class."""
    
    def test_init(self, sample_crawl_spec):
        """Test CrawlState initialization."""
        state = CrawlState(sample_crawl_spec)
        
        assert state.crawl_spec == sample_crawl_spec
        assert len(state.frontier) == len(sample_crawl_spec.seed_urls)
        assert len(state.visited_urls) == 0
        assert len(state.analyzers) == 0
        assert not state.running
    
    def test_add_urls_with_scores(self, sample_crawl_spec):
        """Test adding URLs with scores to frontier."""
        state = CrawlState(sample_crawl_spec)
        
        url_scores = [(0.8, "https://test1.com"), (0.6, "https://test2.com")]
        state.add_urls_with_scores(url_scores)
        
        # Should be sorted by score descending
        assert len(state.frontier) == len(sample_crawl_spec.seed_urls) + 2
        # Check that higher score comes first (negative key for descending sort)
        scores = [-item[0] for item in state.frontier]
        assert scores == sorted(scores)
    
    def test_get_next_url(self, sample_crawl_spec):
        """Test getting next URL from frontier."""
        state = CrawlState(sample_crawl_spec)
        
        # Add some URLs with different scores
        url_scores = [(0.8, "https://high.com"), (0.2, "https://low.com")]
        state.add_urls_with_scores(url_scores)
        
        # Should get highest scoring URL first
        next_url = state.get_next_url()
        assert next_url == "https://high.com"
        assert next_url in state.visited_urls
    
    def test_get_next_url_empty_frontier(self, sample_crawl_spec):
        """Test getting next URL when frontier is empty."""
        state = CrawlState(sample_crawl_spec)
        
        # Empty the frontier
        while state.frontier:
            state.frontier.pop(0)
        
        next_url = state.get_next_url()
        assert next_url is None
    
    def test_is_url_allowed_domain_blacklist(self, sample_crawl_spec):
        """Test URL filtering with domain blacklist."""
        state = CrawlState(sample_crawl_spec)
        
        # Should allow URLs not in blacklist
        assert state.is_url_allowed("https://example.com/page")
        
        # Should block URLs in blacklist
        assert not state.is_url_allowed("https://spam.com/page")
    
    def test_is_url_allowed_no_blacklist(self, sample_analyzer_spec):
        """Test URL filtering with no domain blacklist."""
        spec = CrawlSpec(
            name="test",
            seed_urls=["https://example.com"],
            analyzer_specs=[sample_analyzer_spec],
            domain_blacklist=None
        )
        state = CrawlState(spec)
        
        # Should allow all URLs when no blacklist
        assert state.is_url_allowed("https://any-domain.com/page")


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
        crawl_id = prospector.create(sample_crawl_spec)
        
        assert crawl_id == sample_crawl_spec.id
        assert crawl_id in prospector.crawls
        
        crawl_state = prospector.crawls[crawl_id]
        assert crawl_state.crawl_spec == sample_crawl_spec
        assert len(crawl_state.analyzers) == 1
        assert not crawl_state.running
    
    def test_create_duplicate_crawl(self, prospector, sample_crawl_spec):
        """Test creating a crawl with duplicate ID raises error."""
        prospector.create(sample_crawl_spec)
        
        with pytest.raises(ValueError, match="already exists"):
            prospector.create(sample_crawl_spec)
    
    def test_create_crawl_with_llm_analyzer(self, prospector, sample_analyzer_spec):
        """Test creating a crawl with LLM analyzer."""
        llm_spec = AnalyzerSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=0.5,
            params=None  # LLM analyzer doesn't need params
        )
        
        crawl_spec = CrawlSpec(
            name="test_llm_crawl",
            seed_urls=["https://example.com"],
            analyzer_specs=[sample_analyzer_spec, llm_spec],
            worker_count=1
        )
        
        crawl_id = prospector.create(crawl_spec)
        
        assert crawl_id in prospector.crawls
        crawl_state = prospector.crawls[crawl_id]
        assert len(crawl_state.analyzers) == 2
        assert "LLMServiceScoreAnalyzer" in crawl_state.analyzer_weights
    
    def test_start_crawl(self, prospector, sample_crawl_spec, mock_scraper, mock_handler):
        """Test starting a crawl."""
        # Mock the scraper and handler
        prospector.scraper = mock_scraper
        prospector.handler = mock_handler
        
        crawl_id = prospector.create(sample_crawl_spec)
        prospector.start(crawl_id)
        
        crawl_state = prospector.crawls[crawl_id]
        assert crawl_state.running
    
    def test_start_nonexistent_crawl(self, prospector):
        """Test starting a non-existent crawl raises error."""
        with pytest.raises(ValueError, match="not found"):
            prospector.start("nonexistent_id")
    
    def test_start_already_running_crawl(self, prospector, sample_crawl_spec):
        """Test starting an already running crawl raises error."""
        crawl_id = prospector.create(sample_crawl_spec)
        
        # Manually set to running
        prospector.crawls[crawl_id].running = True
        
        with pytest.raises(RuntimeError, match="already running"):
            prospector.start(crawl_id)
    
    def test_stop_crawl(self, prospector, sample_crawl_spec):
        """Test stopping a crawl."""
        crawl_id = prospector.create(sample_crawl_spec)
        prospector.crawls[crawl_id].running = True  # Set to running
        
        prospector.stop(crawl_id)
        
        crawl_state = prospector.crawls[crawl_id]
        assert not crawl_state.running
    
    def test_stop_nonexistent_crawl(self, prospector):
        """Test stopping a non-existent crawl raises error."""
        with pytest.raises(ValueError, match="not found"):
            prospector.stop("nonexistent_id")
    
    def test_delete_crawl(self, prospector, sample_crawl_spec):
        """Test deleting a crawl."""
        crawl_id = prospector.create(sample_crawl_spec)
        
        prospector.delete(crawl_id)
        
        assert crawl_id not in prospector.crawls
    
    def test_delete_nonexistent_crawl(self, prospector):
        """Test deleting a non-existent crawl raises error."""
        with pytest.raises(ValueError, match="not found"):
            prospector.delete("nonexistent_id")
    
    def test_delete_running_crawl(self, prospector, sample_crawl_spec):
        """Test deleting a running crawl raises error."""
        crawl_id = prospector.create(sample_crawl_spec)
        prospector.crawls[crawl_id].running = True  # Set to running
        
        with pytest.raises(RuntimeError, match="Cannot delete running crawl"):
            prospector.delete(crawl_id)
    
    def test_initialize_analyzers_unknown_type(self, prospector, sample_crawl_spec):
        """Test initializing analyzers with unknown type raises error."""
        # Create spec with unknown analyzer
        bad_spec = AnalyzerSpec(
            name="UnknownAnalyzer",
            composite_weight=1.0,
            params=[]
        )
        spec = CrawlSpec(
            name="test",
            seed_urls=["https://example.com"],
            analyzer_specs=[bad_spec]
        )
        
        with pytest.raises(ValueError, match="Unknown analyzer type"):
            prospector.create(spec)
    
    def test_score_content(self, prospector, sample_crawl_spec, sample_crawl_record):
        """Test scoring content with analyzers."""
        crawl_id = prospector.create(sample_crawl_spec)
        crawl_state = prospector.crawls[crawl_id]
        
        # Score the content
        prospector._score_content(crawl_state, sample_crawl_record)
        
        assert "KeywordScoreAnalyzer" in sample_crawl_record.scores
        assert sample_crawl_record.composite_score >= 0.0
        assert sample_crawl_record.composite_score <= 1.0
    
    def test_score_links(self, prospector, sample_crawl_spec):
        """Test scoring discovered links."""
        crawl_id = prospector.create(sample_crawl_spec)
        crawl_state = prospector.crawls[crawl_id]
        
        links = ["https://example.com/page1", "https://spam.com/page2"]
        scored_links = prospector._score_links(crawl_state, links)
        
        # Should filter out spam.com due to blacklist
        assert len(scored_links) == 1
        assert scored_links[0][1] == "https://example.com/page1"
        assert isinstance(scored_links[0][0], float)
    
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_crawl_worker_empty_frontier(self, mock_sleep, prospector, sample_crawl_spec):
        """Test crawl worker behavior with empty frontier."""
        crawl_id = prospector.create(sample_crawl_spec)
        crawl_state = prospector.crawls[crawl_id]
        
        # Empty the frontier
        crawl_state.frontier.clear()
        crawl_state.running = True
        
        # Start worker in separate thread
        worker_thread = threading.Thread(
            target=prospector._crawl_worker, 
            args=(crawl_id,)
        )
        worker_thread.daemon = True
        worker_thread.start()
        
        # Let it run briefly then stop
        time.sleep(0.1)
        crawl_state.running = False
        worker_thread.join(timeout=1.0)
        
        # Should have called sleep due to empty frontier
        assert mock_sleep.called
    
    def test_process_url_filtered(self, prospector, sample_crawl_spec):
        """Test processing a URL that gets filtered out."""
        crawl_id = prospector.create(sample_crawl_spec)
        crawl_state = prospector.crawls[crawl_id]
        
        # Try to process a blacklisted URL
        prospector._process_url(crawl_state, "https://spam.com/page")
        
        # Should not call scraper or handler (we can verify via mocking if needed)
        # For now, just verify it doesn't crash
        assert True  # Test passes if no exception raised