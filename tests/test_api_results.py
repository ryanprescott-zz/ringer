"""Tests for the results API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from ringer.api.v1.models import CrawlRecordsRequest, CrawlRecordsResponse
from ringer.core.models import CrawlRecord, CrawlResultsId


@pytest.fixture
def mock_ringer():
    """Create a mock Ringer instance."""
    mock = Mock()
    # Ensure get_crawl_records returns an empty list by default
    mock.get_crawl_records.return_value = []
    return mock


@pytest.fixture
def test_client():
    """Create a test client."""
    from ringer.api.v1.routers.results import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    return TestClient(app)


@pytest.fixture
def sample_crawl_records():
    """Create sample crawl records for testing."""
    return [
        CrawlRecord(
            url="https://example1.com",
            page_source="<html>Content 1</html>",
            extracted_content="Content 1",
            links=["https://link1.com"],
            scores={"KeywordScoreAnalyzer": 0.8, "OtherAnalyzer": 0.6},
            composite_score=0.7
        ),
        CrawlRecord(
            url="https://example2.com",
            page_source="<html>Content 2</html>",
            extracted_content="Content 2",
            links=["https://link2.com"],
            scores={"KeywordScoreAnalyzer": 0.9, "OtherAnalyzer": 0.5},
            composite_score=0.75
        ),
        CrawlRecord(
            url="https://example3.com",
            page_source="<html>Content 3</html>",
            extracted_content="Content 3",
            links=["https://link3.com"],
            scores={"KeywordScoreAnalyzer": 0.6, "OtherAnalyzer": 0.8},
            composite_score=0.7
        )
    ]


class TestGetCrawlRecordsEndpoint:
    """Tests for the GET /results/{crawl_id}/records endpoint."""
    
    def test_get_crawl_records_success(self, test_client, mock_ringer, sample_crawl_records):
        """Test successful retrieval of crawl records."""
        # Mock the ringer method to return sample records
        mock_ringer.get_crawl_records.return_value = sample_crawl_records
        
        # Make request with patch context
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                "/results/test_crawl_id/records",
                json={
                    "record_count": 3,
                    "score_type": "composite"
                }
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "records" in data
        assert len(data["records"]) == 3
        
        # Verify first record structure
        first_record = data["records"][0]
        assert first_record["url"] == "https://example1.com"
        assert first_record["extracted_content"] == "Content 1"
        assert first_record["composite_score"] == 0.7
        assert "scores" in first_record
        assert first_record["scores"]["KeywordScoreAnalyzer"] == 0.8
        
        # Verify ringer was called with correct parameters
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id="test_crawl_id",
            record_count=3,
            score_type="composite"
        )
    
    def test_get_crawl_records_with_analyzer_score_type(self, test_client, mock_ringer, sample_crawl_records):
        """Test retrieval with specific analyzer score type."""
        mock_ringer.get_crawl_records.return_value = sample_crawl_records
        
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                "/results/test_crawl_id/records",
                json={
                    "record_count": 2,
                    "score_type": "KeywordScoreAnalyzer"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 3  # Mock returns all sample records
        
        # Verify ringer was called with correct parameters
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id="test_crawl_id",
            record_count=2,
            score_type="KeywordScoreAnalyzer"
        )
    
    def test_get_crawl_records_empty_result(self, test_client, mock_ringer):
        """Test when no records are found."""
        mock_ringer.get_crawl_records.return_value = []
        
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                "/results/test_crawl_id/records",
                json={
                    "record_count": 10,
                    "score_type": "composite"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["records"] == []
    
    def test_get_crawl_records_crawl_not_found(self, test_client, mock_ringer):
        """Test when crawl ID is not found."""
        mock_ringer.get_crawl_records.side_effect = ValueError("Crawl nonexistent_id not found")
        
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                "/results/nonexistent_id/records",
                json={
                    "record_count": 10,
                    "score_type": "composite"
                }
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_crawl_records_invalid_score_type(self, test_client, mock_ringer):
        """Test with invalid score type."""
        mock_ringer.get_crawl_records.side_effect = ValueError(
            "Invalid score_type 'invalid_analyzer' for crawl test_crawl_id. Available types: composite, KeywordScoreAnalyzer"
        )
        
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                "/results/test_crawl_id/records",
                json={
                    "record_count": 10,
                    "score_type": "invalid_analyzer"
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid score_type" in data["detail"].lower()
    
    def test_get_crawl_records_invalid_record_count(self, test_client, mock_ringer):
        """Test with invalid record count (zero or negative)."""
        response = test_client.post(
            "/results/test_crawl_id/records",
            json={
                "record_count": 0,
                "score_type": "composite"
            }
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "greater_than" in data["detail"][0]["type"]
    
    def test_get_crawl_records_negative_record_count(self, test_client, mock_ringer):
        """Test with negative record count."""
        response = test_client.post(
            "/results/test_crawl_id/records",
            json={
                "record_count": -5,
                "score_type": "composite"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_crawl_records_missing_fields(self, test_client, mock_ringer):
        """Test with missing required fields."""
        # Missing record_count
        response = test_client.post(
            "/results/test_crawl_id/records",
            json={
                "score_type": "composite"
            }
        )
        assert response.status_code == 422
        
        # Missing score_type
        response = test_client.post(
            "/results/test_crawl_id/records",
            json={
                "record_count": 10
            }
        )
        assert response.status_code == 422
        
        # Missing both fields
        response = test_client.post(
            "/results/test_crawl_id/records",
            json={}
        )
        assert response.status_code == 422
    
    def test_get_crawl_records_internal_server_error(self, test_client, mock_ringer):
        """Test handling of internal server errors."""
        mock_ringer.get_crawl_records.side_effect = Exception("Database connection failed")
        
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                "/results/test_crawl_id/records",
                json={
                    "record_count": 10,
                    "score_type": "composite"
                }
            )
        
        assert response.status_code == 500
        data = response.json()
        assert "internal server error" in data["detail"].lower()
    
    def test_get_crawl_records_large_record_count(self, test_client, mock_ringer, sample_crawl_records):
        """Test with large record count."""
        mock_ringer.get_crawl_records.return_value = sample_crawl_records
        
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                "/results/test_crawl_id/records",
                json={
                    "record_count": 1000,
                    "score_type": "composite"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 3  # Mock returns sample records
        
        # Verify ringer was called with large count
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id="test_crawl_id",
            record_count=1000,
            score_type="composite"
        )
    
    def test_get_crawl_records_special_characters_in_crawl_id(self, test_client, mock_ringer, sample_crawl_records):
        """Test with special characters in crawl ID."""
        mock_ringer.get_crawl_records.return_value = sample_crawl_records
        
        crawl_id_with_special_chars = "crawl-123_test.id"
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            response = test_client.post(
                f"/results/{crawl_id_with_special_chars}/records",
                json={
                    "record_count": 5,
                    "score_type": "composite"
                }
            )
        
        assert response.status_code == 200
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id=crawl_id_with_special_chars,
            record_count=5,
            score_type="composite"
        )
    
    def test_get_crawl_records_response_model_validation(self, mock_ringer):
        """Test that response follows the expected model structure."""
        from ringer.api.v1.routers.results import router
        from fastapi import FastAPI
        
        # Create a record with all required fields
        test_record = CrawlRecord(
            url="https://test.com",
            page_source="<html>test</html>",
            extracted_content="test content",
            links=["https://link.com"],
            scores={"TestAnalyzer": 0.5},
            composite_score=0.5
        )
        
        mock_ringer.get_crawl_records.return_value = [test_record]
        
        app = FastAPI()
        app.include_router(router)
        
        # Use patch context manager directly in the test
        with patch('ringer.api.v1.routers.results.ringer', mock_ringer):
            test_client = TestClient(app)
            response = test_client.post(
                "/results/test_crawl_id/records",
                json={
                    "record_count": 1,
                    "score_type": "composite"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches CrawlRecordsResponse model
        assert "records" in data
        assert isinstance(data["records"], list)
        
        # Verify record structure matches CrawlRecord model
        record = data["records"][0]
        required_fields = ["url", "page_source", "extracted_content", "links", "scores", "composite_score", "timestamp"]
        for field in required_fields:
            assert field in record, f"Missing required field: {field}"
        
        # Check that id is available as a computed property (not serialized by default)
        # We'll verify the record has the expected structure without requiring id in JSON
        
        assert isinstance(record["links"], list)
        assert isinstance(record["scores"], dict)
        assert isinstance(record["composite_score"], (int, float))


class TestCrawlRecordsRequestModel:
    """Tests for the CrawlRecordsRequest model."""
    
    def test_valid_request_model(self):
        """Test creating valid request model."""
        request = CrawlRecordsRequest(
            record_count=10,
            score_type="composite"
        )
        
        assert request.record_count == 10
        assert request.score_type == "composite"
    
    def test_request_model_validation_positive_record_count(self):
        """Test that record_count must be positive."""
        with pytest.raises(ValueError):
            CrawlRecordsRequest(
                record_count=0,
                score_type="composite"
            )
        
        with pytest.raises(ValueError):
            CrawlRecordsRequest(
                record_count=-1,
                score_type="composite"
            )
    
    def test_request_model_valid_positive_record_count(self):
        """Test that positive record_count is accepted."""
        request = CrawlRecordsRequest(
            record_count=1,
            score_type="composite"
        )
        assert request.record_count == 1
        
        request = CrawlRecordsRequest(
            record_count=1000,
            score_type="composite"
        )
        assert request.record_count == 1000
    
    def test_request_model_score_type_validation(self):
        """Test score_type field validation."""
        # Valid score types
        valid_score_types = ["composite", "KeywordScoreAnalyzer", "DhLlmScoreAnalyzer", "custom_analyzer"]
        
        for score_type in valid_score_types:
            request = CrawlRecordsRequest(
                record_count=10,
                score_type=score_type
            )
            assert request.score_type == score_type


class TestCrawlRecordsResponseModel:
    """Tests for the CrawlRecordsResponse model."""
    
    def test_valid_response_model(self, sample_crawl_records):
        """Test creating valid response model."""
        response = CrawlRecordsResponse(records=sample_crawl_records)
        
        assert len(response.records) == 3
        assert all(isinstance(record, CrawlRecord) for record in response.records)
    
    def test_empty_response_model(self):
        """Test creating response model with empty records."""
        response = CrawlRecordsResponse(records=[])
        
        assert response.records == []
        assert len(response.records) == 0
    
    def test_response_model_serialization(self, sample_crawl_records):
        """Test that response model can be serialized to JSON."""
        response = CrawlRecordsResponse(records=sample_crawl_records)
        
        # Test model_dump (Pydantic v2 method)
        data = response.model_dump()
        
        assert "records" in data
        assert len(data["records"]) == 3
        
        # Verify first record structure
        first_record = data["records"][0]
        assert "url" in first_record
        assert "extracted_content" in first_record
        assert "composite_score" in first_record
        assert "scores" in first_record
