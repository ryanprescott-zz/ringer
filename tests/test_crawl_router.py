"""Tests for the crawl router endpoints."""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from ringer.api.v1.routers.crawl import router
from fastapi import FastAPI


@pytest.fixture
def app():
    """Create a FastAPI app with the crawl router for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_ringer():
    """Create a mock ringer instance."""
    return Mock()


@pytest.fixture
def sample_crawl_info():
    """Sample crawl info data for testing."""
    return {
        "crawl_spec": {
            "name": "test_crawl",
            "description": "A test crawl",
            "seeds": ["https://example.com"],
            "max_pages": 100,
            "analyzer_specs": []
        },
        "crawl_status": {
            "crawl_id": "test_crawl_123",
            "current_state": "created",
            "queued_count": 1,
            "crawled_count": 0,
            "processed_count": 0,
            "error_count": 0,
            "state_history": []
        }
    }


class TestDownloadCrawlSpec:
    """Tests for the download crawl spec endpoint."""

    def test_download_crawl_spec_success(self, client, mock_ringer, sample_crawl_info):
        """Test successful crawl spec download."""
        # Setup
        crawl_id = "test_crawl_123"
        mock_ringer.get_crawl_info.return_value = sample_crawl_info
        
        with patch.object(client.app, 'state') as mock_state:
            mock_state.ringer = mock_ringer
            
            # Execute
            response = client.get(f"/api/v1/crawls/{crawl_id}/spec/download")
            
            # Verify
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert response.headers["content-disposition"] == f"attachment; filename=crawl_spec_{crawl_id}.json"
            
            # Verify the response content matches the crawl spec
            response_json = response.json()
            assert response_json == sample_crawl_info["crawl_spec"]
            
            # Verify ringer was called correctly
            mock_ringer.get_crawl_info.assert_called_once_with(crawl_id)

    def test_download_crawl_spec_not_found(self, client, mock_ringer):
        """Test crawl spec download when crawl doesn't exist."""
        # Setup
        crawl_id = "nonexistent_crawl"
        mock_ringer.get_crawl_info.side_effect = ValueError("Crawl not found")
        
        with patch.object(client.app, 'state') as mock_state:
            mock_state.ringer = mock_ringer
            
            # Execute
            response = client.get(f"/api/v1/crawls/{crawl_id}/spec/download")
            
            # Verify
            assert response.status_code == 404
            assert response.json()["detail"] == "The requested crawl does not exist"
            
            # Verify ringer was called correctly
            mock_ringer.get_crawl_info.assert_called_once_with(crawl_id)

    def test_download_crawl_spec_internal_error(self, client, mock_ringer):
        """Test crawl spec download when internal error occurs."""
        # Setup
        crawl_id = "test_crawl_123"
        mock_ringer.get_crawl_info.side_effect = Exception("Database connection failed")
        
        with patch.object(client.app, 'state') as mock_state:
            mock_state.ringer = mock_ringer
            
            # Execute
            response = client.get(f"/api/v1/crawls/{crawl_id}/spec/download")
            
            # Verify
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
            
            # Verify ringer was called correctly
            mock_ringer.get_crawl_info.assert_called_once_with(crawl_id)

    def test_download_crawl_spec_filename_format(self, client, mock_ringer, sample_crawl_info):
        """Test that the filename format is correct for different crawl IDs."""
        # Setup
        crawl_id = "my-special-crawl_456"
        mock_ringer.get_crawl_info.return_value = sample_crawl_info
        
        with patch.object(client.app, 'state') as mock_state:
            mock_state.ringer = mock_ringer
            
            # Execute
            response = client.get(f"/api/v1/crawls/{crawl_id}/spec/download")
            
            # Verify
            assert response.status_code == 200
            expected_filename = f"crawl_spec_{crawl_id}.json"
            assert response.headers["content-disposition"] == f"attachment; filename={expected_filename}"

    def test_download_crawl_spec_only_returns_spec(self, client, mock_ringer, sample_crawl_info):
        """Test that only the crawl spec is returned, not the full crawl info."""
        # Setup
        crawl_id = "test_crawl_123"
        mock_ringer.get_crawl_info.return_value = sample_crawl_info
        
        with patch.object(client.app, 'state') as mock_state:
            mock_state.ringer = mock_ringer
            
            # Execute
            response = client.get(f"/api/v1/crawls/{crawl_id}/spec/download")
            
            # Verify
            response_json = response.json()
            
            # Should only contain spec fields, not status fields
            assert "name" in response_json
            assert "description" in response_json
            assert "seeds" in response_json
            assert "max_pages" in response_json
            assert "analyzer_specs" in response_json
            
            # Should not contain status fields
            assert "crawl_id" not in response_json
            assert "current_state" not in response_json
            assert "queued_count" not in response_json
