"""Tests for Pydantic models."""

import pytest
import threading
import time
from datetime import datetime
from unittest.mock import patch
from prospector.core import (
    WeightedKeyword,
    AnalyzerSpec,
    CrawlSpec,
    CrawlRecord,
    LLMScoreServiceInput,
    LLMScoreRequest,
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


class TestLLMScoreServiceInput:
    """Tests for LLMScoreServiceInput model."""
    
    def test_valid_input_with_prompt(self):
        """Test creating valid input with prompt."""
        input_obj = LLMScoreServiceInput(
            text="Test content to score",
            prompt="Score this content:"
        )
        
        assert input_obj.text == "Test content to score"
        assert input_obj.prompt == "Score this content:"
    
    def test_valid_input_without_prompt(self):
        """Test creating valid input without prompt."""
        input_obj = LLMScoreServiceInput(text="Test content to score")
        
        assert input_obj.text == "Test content to score"
        assert input_obj.prompt is None
    
    def test_input_validation(self):
        """Test input field validation."""
        # Should require text field
        with pytest.raises(ValueError):
            LLMScoreServiceInput(prompt="Test prompt")


class TestLLMScoreRequest:
    """Tests for LLMScoreRequest model."""
    
    def test_valid_request(self):
        """Test creating a valid LLM score request."""
        request = LLMScoreRequest(
            prompt="Score this text: test content",
            model_output_format={"score": "string"}
        )
        
        assert "test content" in request.prompt
        assert request.model_output_format == {"score": "string"}
    
    def test_request_validation(self):
        """Test request field validation."""
        # Should require both fields
        with pytest.raises(ValueError):
            LLMScoreRequest(prompt="Test prompt")
        
        with pytest.raises(ValueError):
            LLMScoreRequest(model_output_format={"score": "string"})


class TestAnalyzerSpec:
    """Tests for AnalyzerSpec model."""
    
    def test_valid_analyzer_spec(self, sample_weighted_keywords):
        """Test creating a valid analyzer spec."""
        spec = AnalyzerSpec(
            name="TestAnalyzer",
            composite_weight=0.8,
            params=sample_weighted_keywords
        )
        
        assert spec.name == "TestAnalyzer"
        assert spec.composite_weight == 0.8
        assert spec.params == sample_weighted_keywords


class TestCrawlSpec:
    """Tests for CrawlSpec model."""
    
    def test_valid_crawl_spec(self, sample_analyzer_spec):
        """Test creating a valid crawl spec."""
        spec = CrawlSpec(
            name="test_crawl",
            seed_urls=["https://example.com", "https://test.com"],
            analyzer_specs=[sample_analyzer_spec],
            worker_count=2,
            domain_blacklist=["spam.com"]
        )
        
        assert spec.name == "test_crawl"
        assert len(spec.seed_urls) == 2
        assert len(spec.analyzer_specs) == 1
        assert spec.worker_count == 2
        assert "spam.com" in spec.domain_blacklist
    
    def test_crawl_id_generation(self, sample_analyzer_spec):
        """Test crawl ID generation from name hash."""
        spec = CrawlSpec(
            name="test_crawl",
            seed_urls=["https://example.com"],
            analyzer_specs=[sample_analyzer_spec]
        )
        
        crawl_id = spec.id
        assert isinstance(crawl_id, str)
        assert len(crawl_id) == 32  # MD5 hex digest length
        
        # Same name should generate same ID
        spec2 = CrawlSpec(
            name="test_crawl",
            seed_urls=["https://different.com"],
            analyzer_specs=[sample_analyzer_spec]
        )
        assert spec2.id == crawl_id
    
    
    def test_default_values(self, sample_analyzer_spec):
        """Test default values for optional fields."""
        spec = CrawlSpec(
            name="test_crawl",
            seed_urls=["https://example.com"],
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
    
