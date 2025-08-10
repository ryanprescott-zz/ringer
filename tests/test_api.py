"""Tests for the FastAPI web service and crawl router endpoints."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from prospector.main import app
from prospector.core.prospector import Prospector, CrawlState
from prospector.core.models import CrawlSpec, AnalyzerSpec, WeightedKeyword
from prospector.api.v1.models import (
    SubmitCrawlRequest, CrawlStartRequest, CrawlStopRequest, CrawlDeleteRequest
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_prospector():
    """Create a mock Prospector instance."""
    prospector = Mock(spec=Prospector)
    prospector.crawls = {}
    return prospector


@pytest.fixture
def sample_crawl_spec_dict():
    """Sample crawl specification as dictionary for API requests."""
    return {
        "name": "test_crawl",
        "seed_urls": ["https://example.com"],
        "analyzer_specs": [
            {
                "name": "KeywordScoreAnalyzer",
                "composite_weight": 1.0,
                "params": [
                    {"keyword": "test", "weight": 1.0}
                ]
            }
        ],
        "worker_count": 2,
        "domain_blacklist": []
    }


@pytest.fixture
def sample_crawl_state():
    """Create a sample CrawlState for testing."""
    crawl_spec = CrawlSpec(
        name="test_crawl",
        seed_urls=["https://example.com"],
        analyzer_specs=[
            AnalyzerSpec(
                name="KeywordScoreAnalyzer",
                composite_weight=1.0,
                params=[WeightedKeyword(keyword="test", weight=1.0)]
            )
        ]
    )
    crawl_state = CrawlState(crawl_spec)
    crawl_state.crawl_submitted_time = "2023-12-01T10:30:00Z"
    crawl_state.crawl_started_time = "2023-12-01T10:31:00Z"
    crawl_state.crawl_stopped_time = "2023-12-01T10:32:00Z"
    return crawl_state


class TestMainEndpoints:
    """Tests for main application endpoints."""
    
    def test_read_root(self, client):
        """Test the root endpoint returns basic API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Prospector Web Crawler API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCrawlSubmitEndpoint:
    """Tests for the crawl submit endpoint."""
    
    def test_submit_crawl_success(self, client, mock_prospector, sample_crawl_spec_dict, sample_crawl_state):
        """Test successful crawl submission."""
        # Setup mock
        test_crawl_id = "test_crawl_123"
        mock_prospector.submit.return_value = test_crawl_id
        mock_prospector.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/submit",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["crawl_submitted_time"] == sample_crawl_state.crawl_submitted_time
        mock_prospector.submit.assert_called_once()
    
    def test_submit_crawl_duplicate_id(self, client, mock_prospector, sample_crawl_spec_dict):
        """Test submitting a crawl with duplicate ID returns 400."""
        mock_prospector.submit.side_effect = ValueError("Crawl with ID test_crawl already exists")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/submit",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 400
        assert "Crawl with ID test_crawl already exists" in response.json()["detail"]
    
    def test_submit_crawl_invalid_spec(self, client, mock_prospector):
        """Test submitting invalid crawl spec returns 422."""
        invalid_spec = {
            "name": "test_crawl",
            # Missing required fields
        }
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/submit",
            json={"crawl_spec": invalid_spec}
        )
        
        assert response.status_code == 422
    
    def test_submit_crawl_internal_error(self, client, mock_prospector, sample_crawl_spec_dict):
        """Test internal server error during crawl submission."""
        mock_prospector.submit.side_effect = Exception("Database connection failed")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/submit",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestCrawlStartEndpoint:
    """Tests for the crawl start endpoint."""
    
    def test_start_crawl_success(self, client, mock_prospector, sample_crawl_state):
        """Test successful crawl start."""
        test_crawl_id = "test_crawl_123"
        mock_prospector.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/start",
            json={"crawl_id": test_crawl_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["crawl_started_time"] == sample_crawl_state.crawl_started_time
        mock_prospector.start.assert_called_once_with(test_crawl_id)
    
    def test_start_crawl_not_found(self, client, mock_prospector):
        """Test starting non-existent crawl returns 404."""
        mock_prospector.start.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/start",
            json={"crawl_id": "nonexistent_id"}
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_start_crawl_already_running(self, client, mock_prospector):
        """Test starting already running crawl returns 400."""
        mock_prospector.start.side_effect = RuntimeError("Crawl test_crawl is already running")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/start",
            json={"crawl_id": "test_crawl"}
        )
        
        assert response.status_code == 400
        assert "Crawl test_crawl is already running" in response.json()["detail"]
    
    def test_start_crawl_internal_error(self, client, mock_prospector):
        """Test internal server error during crawl start."""
        mock_prospector.start.side_effect = Exception("Thread pool exhausted")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/start",
            json={"crawl_id": "test_crawl"}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestCrawlStopEndpoint:
    """Tests for the crawl stop endpoint."""
    
    def test_stop_crawl_success(self, client, mock_prospector, sample_crawl_state):
        """Test successful crawl stop."""
        test_crawl_id = "test_crawl_123"
        mock_prospector.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/stop",
            json={"crawl_id": test_crawl_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["crawl_stopped_time"] == sample_crawl_state.crawl_stopped_time
        mock_prospector.stop.assert_called_once_with(test_crawl_id)
    
    def test_stop_crawl_not_found(self, client, mock_prospector):
        """Test stopping non-existent crawl returns 404."""
        mock_prospector.stop.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/stop",
            json={"crawl_id": "nonexistent_id"}
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_stop_crawl_internal_error(self, client, mock_prospector):
        """Test internal server error during crawl stop."""
        mock_prospector.stop.side_effect = Exception("Failed to stop workers")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/stop",
            json={"crawl_id": "test_crawl"}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestCrawlDeleteEndpoint:
    """Tests for the crawl delete endpoint."""
    
    @patch('prospector.api.v1.routers.crawl.datetime')
    def test_delete_crawl_success(self, mock_datetime, client, mock_prospector):
        """Test successful crawl deletion."""
        test_crawl_id = "test_crawl_123"
        test_deletion_time = "2023-12-01T10:33:00Z"
        mock_datetime.utcnow.return_value.strftime.return_value = test_deletion_time
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/delete",
            json={"crawl_id": test_crawl_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["crawl_deleted_time"] == test_deletion_time
        mock_prospector.delete.assert_called_once_with(test_crawl_id)
    
    def test_delete_crawl_not_found(self, client, mock_prospector):
        """Test deleting non-existent crawl returns 404."""
        mock_prospector.delete.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/delete",
            json={"crawl_id": "nonexistent_id"}
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_delete_crawl_still_running(self, client, mock_prospector):
        """Test deleting running crawl returns 400."""
        mock_prospector.delete.side_effect = RuntimeError("Cannot delete running crawl test_crawl")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/delete",
            json={"crawl_id": "test_crawl"}
        )
        
        assert response.status_code == 400
        assert "Cannot delete running crawl test_crawl" in response.json()["detail"]
    
    def test_delete_crawl_internal_error(self, client, mock_prospector):
        """Test internal server error during crawl deletion."""
        mock_prospector.delete.side_effect = Exception("Failed to cleanup resources")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/delete",
            json={"crawl_id": "test_crawl"}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestAPIModels:
    """Tests for API request/response models."""
    
    def test_submit_crawl_request_validation(self, sample_crawl_spec_dict):
        """Test SubmitCrawlRequest model validation."""
        # Valid request
        request = SubmitCrawlRequest(crawl_spec=sample_crawl_spec_dict)
        assert request.crawl_spec.name == "test_crawl"
        
        # Invalid request - missing crawl_spec
        with pytest.raises(ValueError):
            SubmitCrawlRequest()
    
    def test_crawl_start_request_validation(self):
        """Test CrawlStartRequest model validation."""
        # Valid request
        request = CrawlStartRequest(crawl_id="test_crawl_123")
        assert request.crawl_id == "test_crawl_123"
        
        # Invalid request - missing crawl_id
        with pytest.raises(ValueError):
            CrawlStartRequest()
    
    def test_crawl_stop_request_validation(self):
        """Test CrawlStopRequest model validation."""
        # Valid request
        request = CrawlStopRequest(crawl_id="test_crawl_123")
        assert request.crawl_id == "test_crawl_123"
        
        # Invalid request - missing crawl_id
        with pytest.raises(ValueError):
            CrawlStopRequest()
    
    def test_crawl_delete_request_validation(self):
        """Test CrawlDeleteRequest model validation."""
        # Valid request
        request = CrawlDeleteRequest(crawl_id="test_crawl_123")
        assert request.crawl_id == "test_crawl_123"
        
        # Invalid request - missing crawl_id
        with pytest.raises(ValueError):
            CrawlDeleteRequest()


class TestApplicationLifespan:
    """Tests for FastAPI application lifespan management."""
    
    @patch('prospector.main.Prospector')
    def test_lifespan_startup_shutdown(self, mock_prospector_class):
        """Test that Prospector is created on startup and shutdown on exit."""
        mock_prospector_instance = Mock()
        mock_prospector_class.return_value = mock_prospector_instance
        
        # Test startup and shutdown
        with TestClient(app) as client:
            # Verify Prospector was created and stored in app state
            mock_prospector_class.assert_called_once()
            assert hasattr(client.app.state, 'prospector')
        
        # Verify shutdown was called
        mock_prospector_instance.shutdown.assert_called_once()


class TestEndToEndWorkflow:
    """End-to-end tests for complete crawl workflow."""
    
    def test_complete_crawl_workflow(self, client, mock_prospector, sample_crawl_spec_dict, sample_crawl_state):
        """Test complete workflow: submit -> start -> stop -> delete."""
        test_crawl_id = "workflow_test_123"
        
        # Setup mock responses
        mock_prospector.submit.return_value = test_crawl_id
        mock_prospector.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        # 1. Submit crawl
        submit_response = client.post(
            "/api/v1/crawl/submit",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        assert submit_response.status_code == 200
        assert submit_response.json()["crawl_id"] == test_crawl_id
        
        # 2. Start crawl
        start_response = client.post(
            "/api/v1/crawl/start",
            json={"crawl_id": test_crawl_id}
        )
        assert start_response.status_code == 200
        assert start_response.json()["crawl_id"] == test_crawl_id
        
        # 3. Stop crawl
        stop_response = client.post(
            "/api/v1/crawl/stop",
            json={"crawl_id": test_crawl_id}
        )
        assert stop_response.status_code == 200
        assert stop_response.json()["crawl_id"] == test_crawl_id
        
        # 4. Delete crawl
        with patch('prospector.api.v1.routers.crawl.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.strftime.return_value = "2023-12-01T10:35:00Z"
            delete_response = client.post(
                "/api/v1/crawl/delete",
                json={"crawl_id": test_crawl_id}
            )
            assert delete_response.status_code == 200
            assert delete_response.json()["crawl_id"] == test_crawl_id
        
        # Verify all methods were called
        mock_prospector.submit.assert_called_once()
        mock_prospector.start.assert_called_once_with(test_crawl_id)
        mock_prospector.stop.assert_called_once_with(test_crawl_id)
        mock_prospector.delete.assert_called_once_with(test_crawl_id)
    
    def test_invalid_workflow_order(self, client, mock_prospector):
        """Test that invalid workflow order returns appropriate errors."""
        nonexistent_crawl_id = "nonexistent_123"
        
        # Setup mock to raise ValueError for nonexistent crawl
        mock_prospector.start.side_effect = ValueError(f"Crawl {nonexistent_crawl_id} not found")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        # Try to start non-existent crawl
        response = client.post(
            "/api/v1/crawl/start",
            json={"crawl_id": nonexistent_crawl_id}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestErrorHandling:
    """Tests for comprehensive error handling scenarios."""
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON requests."""
        response = client.post(
            "/api/v1/crawl/submit",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_request_body(self, client):
        """Test handling of missing request body."""
        response = client.post("/api/v1/crawl/submit")
        assert response.status_code == 422
    
    def test_invalid_content_type(self, client, sample_crawl_spec_dict):
        """Test handling of invalid content type."""
        response = client.post(
            "/api/v1/crawl/submit",
            content=str(sample_crawl_spec_dict),
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422
    
    def test_prospector_not_initialized(self, client, sample_crawl_spec_dict):
        """Test handling when Prospector is not properly initialized."""
        # Remove prospector from app state
        if hasattr(app.state, 'prospector'):
            delattr(app.state, 'prospector')
        
        response = client.post(
            "/api/v1/crawl/submit",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        assert response.status_code == 500
