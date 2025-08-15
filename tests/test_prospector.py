"""Tests for main Prospector class."""

import pytest
from unittest.mock import Mock, patch
import threading
import time

from prospector.core import (
    Prospector,
    CrawlState,
    CrawlSpec,
    CrawlSeeds,
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
        state = CrawlState(sample_crawl_spec)
        
        assert state.crawl_spec == sample_crawl_spec
        assert len(state.frontier) == 0  # Frontier is now populated when crawl starts
        assert len(state.visited_urls) == 0
        assert len(state.analyzers) == 0
        assert state.current_state == RunStateEnum.CREATED
        assert len(state.resolved_seed_urls) == 0
    
    def test_add_urls_with_scores(self, sample_crawl_spec):
        """Test adding URLs with scores to frontier."""
        state = CrawlState(sample_crawl_spec)
        
        url_scores = [(0.8, "https://test1.com"), (0.6, "https://test2.com")]
        state.add_urls_with_scores(url_scores)
        
        # Should be sorted by score descending
        assert len(state.frontier) == 2
        # Check that higher score comes first
        frontier_list = list(state.frontier)
        scores = [item.score for item in frontier_list]
        assert scores == sorted(scores, reverse=True)
    
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
    
    def test_frontier_duplicate_urls(self, sample_crawl_spec):
        """Test that frontier prevents duplicate URLs."""
        state = CrawlState(sample_crawl_spec)
        
        # Add same URL with different scores
        url_scores = [(0.8, "https://test.com"), (0.6, "https://test.com")]
        state.add_urls_with_scores(url_scores)
        
        # Should only contain one instance of the URL
        urls_in_frontier = [item.url for item in state.frontier]
        assert urls_in_frontier.count("https://test.com") == 1
        
        # Should keep the first one added (0.8 score)
        test_url_tuple = next(item for item in state.frontier if item.url == "https://test.com")
        assert test_url_tuple.score == 0.8
    
    def test_is_url_allowed_domain_blacklist(self, sample_crawl_spec):
        """Test URL filtering with domain blacklist."""
        state = CrawlState(sample_crawl_spec)
        
        # Should allow URLs not in blacklist
        assert state.is_url_allowed("https://example.com/page")
        
        # Should block URLs in blacklist
        assert not state.is_url_allowed("https://spam.com/page")
    
    def test_is_url_allowed_no_blacklist(self, sample_analyzer_spec):
        """Test URL filtering with no domain blacklist."""
        seeds = CrawlSeeds(url_seeds=["https://example.com"])
        spec = CrawlSpec(
            name="test",
            seeds=seeds,
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
        
        seeds = CrawlSeeds(url_seeds=["https://example.com"])
        crawl_spec = CrawlSpec(
            name="test_llm_crawl",
            seeds=seeds,
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
    
