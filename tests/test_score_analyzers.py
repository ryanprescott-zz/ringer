"""Tests for score analyzers."""
import pytest
import math
from unittest.mock import Mock, patch

from prospector.core import (
    KeywordScoreAnalyzer,
    WeightedKeyword,
    LLMServiceScoreAnalyzer,
)
from prospector.core.models import (
    KeywordScoringSpec,
    LLMScoringSpec,
    PromptInput,
    TopicListInput,
)


class TestKeywordScoreAnalyzer:
    """Tests for KeywordScoreAnalyzer class."""
    
    def test_init_with_keywords(self, sample_weighted_keywords):
        """Test initialization with valid keywords."""
        spec = KeywordScoringSpec(
            name="KeywordScoreAnalyzer",
            composite_weight=1.0,
            keywords=sample_weighted_keywords
        )
        analyzer = KeywordScoreAnalyzer(spec)
        assert hasattr(analyzer, 'keywords') or hasattr(analyzer, 'spec')
        # Check that keywords are accessible somehow
        if hasattr(analyzer, 'spec'):
            assert analyzer.spec.keywords == sample_weighted_keywords
        elif hasattr(analyzer, 'keywords'):
            assert analyzer.keywords == sample_weighted_keywords
    
    def test_init_empty_keywords(self):
        """Test initialization with empty keywords list raises error."""
        with pytest.raises(ValueError, match="Keywords list cannot be empty"):
            spec = KeywordScoringSpec(
                name="KeywordScoreAnalyzer",
                composite_weight=1.0,
                keywords=[]
            )
    
    def test_score_with_string_content(self, keyword_analyzer):
        """Test scoring with valid string content."""
        content = "This is a python programming tutorial with code examples"
        score = keyword_analyzer.score(content)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0  # Should have positive score due to keyword matches
    
    def test_score_with_non_string_content(self, keyword_analyzer):
        """Test scoring with non-string content raises error."""
        with pytest.raises(TypeError, match="Content must be a string"):
            keyword_analyzer.score(123)
    
    def test_score_empty_content(self, keyword_analyzer):
        """Test scoring with empty content returns zero."""
        score = keyword_analyzer.score("")
        assert score == 0.0
    
    def test_score_case_insensitive(self, keyword_analyzer):
        """Test that scoring is case insensitive."""
        content_lower = "python programming code"
        content_upper = "PYTHON PROGRAMMING CODE"
        content_mixed = "Python Programming Code"
        
        score_lower = keyword_analyzer.score(content_lower)
        score_upper = keyword_analyzer.score(content_upper)
        score_mixed = keyword_analyzer.score(content_mixed)
        
        assert score_lower == score_upper == score_mixed
    
    def test_score_multiple_occurrences(self, keyword_analyzer):
        """Test that multiple occurrences increase score."""
        content_single = "python"
        content_multiple = "python python python"
        
        score_single = keyword_analyzer.score(content_single)
        score_multiple = keyword_analyzer.score(content_multiple)
        
        assert score_multiple > score_single
    
    def test_score_weighted_keywords(self):
        """Test that keyword weights affect scoring."""
        high_weight = WeightedKeyword(keyword="important", weight=10.0)
        low_weight = WeightedKeyword(keyword="unimportant", weight=0.1)
        
        spec = KeywordScoringSpec(
            name="KeywordScoreAnalyzer",
            composite_weight=1.0,
            keywords=[high_weight, low_weight]
        )
        analyzer = KeywordScoreAnalyzer(spec)
        
        # Use multiple occurrences to amplify the weight difference
        content_high = "This is important important important"
        content_low = "This is unimportant"
        
        score_high = analyzer.score(content_high)
        score_low = analyzer.score(content_low)
        
        assert score_high > score_low
    
    def test_score_no_matches(self, keyword_analyzer):
        """Test scoring with no keyword matches."""
        content = "This content has no relevant terms"
        score = keyword_analyzer.score(content)
        
        # Should still be > 0 due to sigmoid normalization but very low
        assert 0.0 <= score < 0.6  # Sigmoid of 0 is ~0.5, so should be less
    
    def test_score_sigmoid_normalization(self, keyword_analyzer):
        """Test that scores are properly normalized using sigmoid."""
        # Very high keyword density should still be <= 1.0
        content = " ".join(["python programming code"] * 100)
        score = keyword_analyzer.score(content)
        
        assert 0.0 <= score <= 1.0


class TestLLMServiceScoreAnalyzer:
    """Tests for LLMServiceScoreAnalyzer class."""
    
    def test_init(self):
        """Test initialization of LLM service analyzer."""
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["test", "example"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        assert hasattr(analyzer, 'spec') or hasattr(analyzer, 'settings')
        assert analyzer.session is not None
        assert analyzer.session.headers['Content-Type'] == 'application/json'
        assert analyzer.session.headers['Accept'] == 'application/json'
    
    @patch('prospector.core.score_analyzers.llm_service_score_analyzer.requests.Session.post')
    def test_score_with_valid_response(self, mock_post):
        """Test scoring with valid LLM service response."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"score": "0.85"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["python", "programming"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        content = "Test content about python programming"
        
        score = analyzer.score(content)
        
        assert score == 0.85
        mock_post.assert_called_once()
        
        # Verify request data
        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == analyzer.settings.llm_request_timeout
        request_data = call_args[1]['json']
        assert 'generation_input' in request_data
        assert 'text_inputs' in request_data
        assert "Test content about python programming" in request_data['text_inputs']
    
    @patch('prospector.core.score_analyzers.llm_service_score_analyzer.requests.Session.post')
    def test_score_with_custom_prompt(self, mock_post):
        """Test scoring with custom prompt."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"score": "0.75"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=PromptInput(prompt="Custom scoring prompt:")
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        content = "Test content"
        
        score = analyzer.score(content)
        
        assert score == 0.75
        
        # Verify custom prompt was used
        call_args = mock_post.call_args
        request_data = call_args[1]['json']
        assert "Custom scoring prompt:" in request_data['generation_input']['prompt']
    
    @patch('prospector.core.score_analyzers.llm_service_score_analyzer.requests.Session.post')
    def test_score_with_default_prompt(self, mock_post):
        """Test scoring with default prompt when using topics."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"score": "0.65"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["test", "content"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        content = "Test content"
        
        score = analyzer.score(content)
        
        assert score == 0.65
        
        # Verify default prompt was built from topics
        call_args = mock_post.call_args
        request_data = call_args[1]['json']
        prompt = request_data['generation_input']['prompt']
        assert "test" in prompt and "content" in prompt
    
    def test_score_with_invalid_content_type(self):
        """Test scoring with invalid content type raises error."""
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["test"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        
        with pytest.raises(TypeError, match="Content must be a string"):
            analyzer.score(123)
    
    @patch('prospector.core.score_analyzers.llm_service_score_analyzer.requests.Session.post')
    def test_score_with_http_error(self, mock_post):
        """Test scoring with HTTP error returns 0.0."""
        import requests
        
        # Mock HTTP error
        mock_post.side_effect = requests.exceptions.HTTPError("HTTP 500 Error")
        
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["test"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        content = "Test content"
        
        score = analyzer.score(content)
        
        assert score == 0.0
    
    @patch('prospector.core.score_analyzers.llm_service_score_analyzer.requests.Session.post')
    def test_score_with_timeout(self, mock_post):
        """Test scoring with timeout returns 0.0."""
        import requests
        
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["test"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        content = "Test content"
        
        score = analyzer.score(content)
        
        assert score == 0.0
    
    @patch('prospector.core.score_analyzers.llm_service_score_analyzer.requests.Session.post')
    def test_score_with_invalid_json_response(self, mock_post):
        """Test scoring with invalid JSON response returns 0.0."""
        import json
        
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["test"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        content = "Test content"
        
        score = analyzer.score(content)
        
        assert score == 0.0
    
    @patch('prospector.core.score_analyzers.llm_service_score_analyzer.requests.Session.post')
    def test_score_with_missing_score_field(self, mock_post):
        """Test scoring with missing score field in response returns 0.0."""
        # Mock response missing score field
        mock_response = Mock()
        mock_response.json.return_value = {"result": "success"}  # No score field
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        spec = LLMScoringSpec(
            name="LLMServiceScoreAnalyzer",
            composite_weight=1.0,
            scoring_input=TopicListInput(topics=["test"])
        )
        analyzer = LLMServiceScoreAnalyzer(spec)
        content = "Test content"
        
        score = analyzer.score(content)
        
        assert score == 0.0
