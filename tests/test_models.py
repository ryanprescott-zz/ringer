"""Tests for Pydantic models."""

import pytest
import threading
import time
from datetime import datetime
from unittest.mock import patch

from ringer.core.models import (
    KeywordScoringSpec,
    DhLlmScoringSpec,
    PromptInput,
    WeightedKeyword,
    WeightedRegex,
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


class TestWeightedRegex:
    """Tests for WeightedRegex model."""
    
    def test_valid_regex(self):
        """Test creating a valid weighted regex."""
        regex = WeightedRegex(regex=r"\d+", weight=2.0)
        
        assert regex.regex == r"\d+"
        assert regex.weight == 2.0
        assert regex.flags == 0  # default value
    
    def test_regex_with_flags(self):
        """Test creating a weighted regex with flags."""
        import re
        regex = WeightedRegex(regex=r"test", weight=1.0, flags=re.IGNORECASE)
        
        assert regex.regex == r"test"
        assert regex.weight == 1.0
        assert regex.flags == re.IGNORECASE
    
    def test_regex_validation(self):
        """Test regex field validation."""
        # Should require regex field
        with pytest.raises(ValueError):
            WeightedRegex(weight=1.0)


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
        assert spec.regexes == []  # default empty list
    
    def test_valid_keyword_scoring_spec_with_regexes(self):
        """Test creating valid keyword scoring spec with regexes."""
        from ringer.core.models import WeightedRegex
        import re
        
        regexes = [
            WeightedRegex(regex=r"\d+", weight=1.0),
            WeightedRegex(regex=r"test", weight=2.0, flags=re.IGNORECASE)
        ]
        
        spec = KeywordScoringSpec(
            name="KeywordScoreAnalyzer",
            composite_weight=0.8,
            regexes=regexes
        )
        
        assert spec.name == "KeywordScoreAnalyzer"
        assert spec.composite_weight == 0.8
        assert spec.keywords == []  # default empty list
        assert spec.regexes == regexes
    
    def test_valid_keyword_scoring_spec_mixed(self, sample_weighted_keywords):
        """Test creating valid keyword scoring spec with both keywords and regexes."""
        from ringer.core.models import WeightedRegex
        
        regexes = [WeightedRegex(regex=r"\d+", weight=1.5)]
        
        spec = KeywordScoringSpec(
            name="KeywordScoreAnalyzer",
            composite_weight=0.8,
            keywords=sample_weighted_keywords,
            regexes=regexes
        )
        
        assert spec.name == "KeywordScoreAnalyzer"
        assert spec.composite_weight == 0.8
        assert spec.keywords == sample_weighted_keywords
        assert spec.regexes == regexes
    
    def test_empty_keywords_and_regexes_validation(self):
        """Test empty keywords and regexes validation."""
        with pytest.raises(ValueError, match="At least one keyword or regex must be provided"):
            KeywordScoringSpec(
                name="KeywordScoreAnalyzer",
                composite_weight=1.0,
                keywords=[],
                regexes=[]
            )


class TestDhLlmScoringSpec:
    """Tests for DhLlmScoringSpec model."""
    
    def test_valid_llm_scoring_spec_with_prompt(self):
        """Test creating valid LLM scoring spec with prompt."""
        spec = DhLlmScoringSpec(
            name="DhLlmScoreAnalyzer",
            composite_weight=0.7,
            prompt_input=PromptInput(prompt="Score this content:")
        )
        
        assert spec.name == "DhLlmScoreAnalyzer"
        assert spec.composite_weight == 0.7
        assert isinstance(spec.prompt_input, PromptInput)


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
    
