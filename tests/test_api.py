"""Tests for the FastAPI web service and crawl router endpoints."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from prospector.main import app
from prospector.core.prospector import Prospector
from prospector.core import (
    CrawlSpec,
    WeightedKeyword,
)
from prospector.core.models import KeywordScoringSpec
from prospector.api.v1.models import (
    CreateCrawlRequest, StartCrawlRequest, StopCrawlRequest, DeleteCrawlRequest
)


#@pytest.fixture
# def sample_crawl_spec_dict():
#     """Sample crawl specification as dictionary for API requests."""
#     return {
#         "name": "test_crawl",
#         "seeds": [
#             {
#                 "url_seeds": ["https://example.com"],
#                 "search_engine_seeds": [
#                     {"search_engine": "google", "query": "breeds of dogs", "result_count": 10}
#                 ]
#             }
#         ],
#         "url_seeds": ["https://example.com"],
#         "analyzer_specs": [
#             {
#                 "name": "KeywordScoreAnalyzer",
#                 "composite_weight": 1.0,
#                 "keywords": [
#                     {"keyword": "test", "weight": 1.0}
#                 ]
#             }
#         ],
#         "worker_count": 2,
#         "domain_blacklist": []
#     }


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


class TestCreateCrawlEndpoint:
    """Tests for the crawl create endpoint."""
    
    def test_create_crawl_success(self, client, mock_prospector, sample_crawl_spec_dict, sample_crawl_state):
        """Test successful crawl submission."""
        from prospector.core.models import RunState, RunStateEnum
        
        # Setup mock
        test_crawl_id = "test_crawl_123"
        test_run_state = RunState(state=RunStateEnum.CREATED)
        mock_prospector.create.return_value = (test_crawl_id, test_run_state)
        mock_prospector.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/create",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["run_state"]["state"] == "CREATED"
        assert "timestamp" in data["run_state"]
        mock_prospector.create.assert_called_once()
    
    def test_create_crawl_duplicate_id(self, client, mock_prospector, sample_crawl_spec_dict):
        """Test creating a crawl with duplicate ID returns 400."""
        mock_prospector.create.side_effect = ValueError("Crawl with ID test_crawl already exists")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/create",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 400
        assert "Crawl with ID test_crawl already exists" in response.json()["detail"]
    
    def test_create_crawl_invalid_spec(self, client, mock_prospector):
        """Test creating invalid crawl spec returns 422."""
        invalid_spec = {
            "name": "test_crawl",
            # Missing required fields
        }
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/create",
            json={"crawl_spec": invalid_spec}
        )
        
        assert response.status_code == 422
    
    def test_create_crawl_internal_error(self, client, mock_prospector, sample_crawl_spec_dict):
        """Test internal server error during crawl submission."""
        mock_prospector.create.side_effect = Exception("Database connection failed")
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        response = client.post(
            "/api/v1/crawl/create",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestStartCrawlEndpoint:
    """Tests for the crawl start endpoint."""
    
    def test_start_crawl_success(self, client, mock_prospector, sample_crawl_state):
        """Test successful crawl start."""
        from prospector.core.models import RunState, RunStateEnum
        
        test_crawl_id = "test_crawl_123"
        test_run_state = RunState(state=RunStateEnum.RUNNING)
        mock_prospector.start.return_value = (test_crawl_id, test_run_state)
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
        assert data["run_state"]["state"] == "RUNNING"
        assert "timestamp" in data["run_state"]
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


class TestStopCrawlEndpoint:
    """Tests for the crawl stop endpoint."""
    
    def test_stop_crawl_success(self, client, mock_prospector, sample_crawl_state):
        """Test successful crawl stop."""
        from prospector.core.models import RunState, RunStateEnum
        
        test_crawl_id = "test_crawl_123"
        test_run_state = RunState(state=RunStateEnum.STOPPED)
        mock_prospector.stop.return_value = (test_crawl_id, test_run_state)
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
        assert data["run_state"]["state"] == "STOPPED"
        assert "timestamp" in data["run_state"]
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


class TestDeleteCrawlEndpoint:
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
    
    def test_create_crawl_request_validation(self, sample_crawl_spec):
        """Test CreateCrawlRequest model validation."""
        # Valid request
        request = CreateCrawlRequest(crawl_spec=sample_crawl_spec)
        assert request.crawl_spec.name == "test_crawl"
        
        # Invalid request - missing crawl_spec
        with pytest.raises(ValueError):
            CreateCrawlRequest()
    
    def test_crawl_start_request_validation(self):
        """Test StartCrawlRequest model validation."""
        # Valid request
        request = StartCrawlRequest(crawl_id="test_crawl_123")
        assert request.crawl_id == "test_crawl_123"
        
        # Invalid request - missing crawl_id
        with pytest.raises(ValueError):
            StartCrawlRequest()
    
    def test_crawl_stop_request_validation(self):
        """Test StopCrawlRequest model validation."""
        # Valid request
        request = StopCrawlRequest(crawl_id="test_crawl_123")
        assert request.crawl_id == "test_crawl_123"
        
        # Invalid request - missing crawl_id
        with pytest.raises(ValueError):
            StopCrawlRequest()
    
    def test_crawl_delete_request_validation(self):
        """Test DeleteCrawlRequest model validation."""
        # Valid request
        request = DeleteCrawlRequest(crawl_id="test_crawl_123")
        assert request.crawl_id == "test_crawl_123"
        
        # Invalid request - missing crawl_id
        with pytest.raises(ValueError):
            DeleteCrawlRequest()


class TestApplicationLifespan:
    """Tests for FastAPI application lifespan management."""
    
    @patch('prospector.main.Prospector')
    def test_lifespan_startup_shutdown(self, mock_prospector_class):
        """Test that Prospector is created on startup and shutdown on exit."""
        from contextlib import asynccontextmanager
        from fastapi import FastAPI
        from prospector.main import lifespan
        
        mock_prospector_instance = Mock()
        mock_prospector_class.return_value = mock_prospector_instance
        
        # Create a test app to test the lifespan
        test_app = FastAPI()
        
        # Manually run the lifespan context manager
        async def run_lifespan():
            async with lifespan(test_app):
                # Verify Prospector was created and stored in app state
                mock_prospector_class.assert_called_once()
                assert hasattr(test_app.state, 'prospector')
                assert test_app.state.prospector == mock_prospector_instance
        
        # Run the async lifespan
        import asyncio
        asyncio.run(run_lifespan())
        
        # Verify shutdown was called
        mock_prospector_instance.shutdown.assert_called_once()


class TestEndToEndWorkflow:
    """End-to-end tests for complete crawl workflow."""
    
    def test_complete_crawl_workflow(self, client, mock_prospector, sample_crawl_spec_dict, sample_crawl_state):
        """Test complete workflow: create -> start -> stop -> delete."""
        from prospector.core.models import RunState, RunStateEnum
        
        test_crawl_id = "workflow_test_123"
        
        # Setup mock responses
        create_state = RunState(state=RunStateEnum.CREATED)
        start_state = RunState(state=RunStateEnum.RUNNING)
        stop_state = RunState(state=RunStateEnum.STOPPED)
        
        mock_prospector.create.return_value = (test_crawl_id, create_state)
        mock_prospector.start.return_value = (test_crawl_id, start_state)
        mock_prospector.stop.return_value = (test_crawl_id, stop_state)
        mock_prospector.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the prospector in app state
        app.state.prospector = mock_prospector
        
        # 1. create crawl
        create_response = client.post(
            "/api/v1/crawl/create",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        assert create_response.status_code == 200
        assert create_response.json()["crawl_id"] == test_crawl_id
        assert create_response.json()["run_state"]["state"] == "CREATED"
        
        # 2. Start crawl
        start_response = client.post(
            "/api/v1/crawl/start",
            json={"crawl_id": test_crawl_id}
        )
        assert start_response.status_code == 200
        assert start_response.json()["crawl_id"] == test_crawl_id
        assert start_response.json()["run_state"]["state"] == "RUNNING"
        
        # 3. Stop crawl
        stop_response = client.post(
            "/api/v1/crawl/stop",
            json={"crawl_id": test_crawl_id}
        )
        assert stop_response.status_code == 200
        assert stop_response.json()["crawl_id"] == test_crawl_id
        assert stop_response.json()["run_state"]["state"] == "STOPPED"
        
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
        mock_prospector.create.assert_called_once()
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
            "/api/v1/crawl/create",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_request_body(self, client):
        """Test handling of missing request body."""
        response = client.post("/api/v1/crawl/create")
        assert response.status_code == 422
    
    def test_invalid_content_type(self, client, sample_crawl_spec_dict):
        """Test handling of invalid content type."""
        response = client.post(
            "/api/v1/crawl/create",
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
            "/api/v1/crawl/create",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        assert response.status_code == 500
