"""Tests for Pydantic models."""

import pytest
import threading
import time
from datetime import datetime
from unittest.mock import patch

from prospector.core.models import (
    KeywordScoringSpec,
    DhLlmScoringSpec,
    PromptInput,
    TopicListInput,
    WeightedKeyword,
    AnalyzerSpec,
    CrawlSpec,
    CrawlRecord,
)


class TestWeightedKeyword:
    """Tests for WeightedKeyword model."""
    
    def test_valid_keyword(self):
        """Test creating a valid weighted keyword."""
        keyword = WeightedKeyword(keyword="test", weight=1.5)
        
        assert keyword.keyword == "test"
        assert keyword.weight == 1.5
    
    def test_keyword_validation(self):
        """Test keyword field validation."""
        # Should require keyword field
        with pytest.raises(ValueError):
            WeightedKeyword(weight=1.0)


class TestPromptInput:
    """Tests for PromptInput model."""
    
    def test_valid_prompt_input(self):
        """Test creating valid prompt input."""
        input_obj = PromptInput(prompt="Score this content:")
        assert input_obj.prompt == "Score this content:"
    
    def test_empty_prompt_validation(self):
        """Test empty prompt validation."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            PromptInput(prompt="")
        
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            PromptInput(prompt="   ")


class TestTopicListInput:
    """Tests for TopicListInput model."""
    
    def test_valid_topic_list_input(self):
        """Test creating valid topic list input."""
        input_obj = TopicListInput(topics=["python", "programming", "code"])
        assert input_obj.topics == ["python", "programming", "code"]
    
    def test_empty_topics_validation(self):
        """Test empty topics list validation."""
        with pytest.raises(ValueError, match="Topics list cannot be empty"):
            TopicListInput(topics=[])


class TestKeywordScoringSpec:
    """Tests for KeywordScoringSpec model."""
    
    def test_valid_keyword_scoring_spec(self, sample_weighted_keywords):
        """Test creating valid keyword scoring spec."""
        spec = KeywordScoringSpec(
            name="KeywordScoreAnalyzer",
            composite_weight=0.8,
            keywords=sample_weighted_keywords
        )
        
        assert spec.name == "KeywordScoreAnalyzer"
        assert spec.composite_weight == 0.8
        assert spec.keywords == sample_weighted_keywords
    
    def test_empty_keywords_validation(self):
        """Test empty keywords validation."""
        with pytest.raises(ValueError, match="Keywords list cannot be empty"):
            KeywordScoringSpec(
                name="KeywordScoreAnalyzer",
                composite_weight=1.0,
                keywords=[]
            )


class TestDhLlmScoringSpec:
    """Tests for DhLlmScoringSpec model."""
    
    def test_valid_llm_scoring_spec_with_prompt(self):
        """Test creating valid LLM scoring spec with prompt."""
        spec = DhLlmScoringSpec(
            name="DhLlmScoreAnalyzer",
            composite_weight=0.7,
            scoring_input=PromptInput(prompt="Score this content:")
        )
        
        assert spec.name == "DhLlmScoreAnalyzer"
        assert spec.composite_weight == 0.7
        assert isinstance(spec.scoring_input, PromptInput)
    
    def test_valid_llm_scoring_spec_with_topics(self):
        """Test creating valid LLM scoring spec with topics."""
        spec = DhLlmScoringSpec(
            name="DhLlmScoreAnalyzer",
            composite_weight=0.9,
            scoring_input=TopicListInput(topics=["python", "programming"])
        )
        
        assert spec.name == "DhLlmScoreAnalyzer"
        assert spec.composite_weight == 0.9
        assert isinstance(spec.scoring_input, TopicListInput)


class TestAnalyzerSpec:
    """Tests for AnalyzerSpec model."""
    
    def test_valid_analyzer_spec(self):
        """Test creating a valid analyzer spec."""
        spec = AnalyzerSpec(
            name="TestAnalyzer",
            composite_weight=0.8
        )
        
        assert spec.name == "TestAnalyzer"
        assert spec.composite_weight == 0.8


class TestCrawlSpec:
    """Tests for CrawlSpec model."""
    
    def test_valid_crawl_spec(self, sample_crawl_spec):
        """Test creating a valid crawl spec."""
        
        assert sample_crawl_spec.name == "test_crawl"
        assert len(sample_crawl_spec.seeds) == 1
        assert sample_crawl_spec.seeds[0] == "https://example.com"
        assert len(sample_crawl_spec.analyzer_specs) == 1
        assert sample_crawl_spec.worker_count == 1
        assert "spam.com" in sample_crawl_spec.domain_blacklist
    
    def test_empty_seeds_validation(self, sample_analyzer_spec):
        """Test that empty seeds list raises validation error."""
        with pytest.raises(ValueError, match="Seeds list cannot be empty"):
            CrawlSpec(
                name="test_crawl",
                seeds=[],
                analyzer_specs=[sample_analyzer_spec]
            )
    
    def test_default_values(self, sample_analyzer_spec):
        """Test default values for optional fields."""
        spec = CrawlSpec(
            name="test_crawl",
            seeds=["https://example.com"],
            analyzer_specs=[sample_analyzer_spec]
        )
        
        assert spec.worker_count == 1
        assert spec.domain_blacklist is None


class TestCrawlRecord:
    """Tests for CrawlRecord model."""
    
    def test_valid_crawl_record(self):
        """Test creating a valid crawl record."""
        record = CrawlRecord(
            url="https://example.com",
            page_source="<html><body>Test</body></html>",
            extracted_content="Test content",
            links=["https://example.com/page1"],
            scores={"TestAnalyzer": 0.8},
            composite_score=0.8
        )
        
        assert record.url == "https://example.com"
        assert record.extracted_content == "Test content"
        assert len(record.links) == 1
        assert record.scores["TestAnalyzer"] == 0.8
        assert record.composite_score == 0.8
        assert isinstance(record.timestamp, datetime)
    
    def test_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        record = CrawlRecord(
            url="https://example.com",
            page_source="<html></html>",
            extracted_content="Test",
            links=[],
            scores={},
            composite_score=0.0
        )
        
        assert record.timestamp is not None
        assert isinstance(record.timestamp, datetime)
        
        # Should be recent
        time_diff = datetime.now() - record.timestamp
        assert time_diff.total_seconds() < 1.0
    
