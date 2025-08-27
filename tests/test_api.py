"""Tests for the FastAPI web service and crawl router endpoints."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from ringer.main import app
from ringer.core.ringer import Ringer
from ringer.core import (
    CrawlSpec,
    WeightedKeyword,
)
from ringer.core.models import KeywordScoringSpec
from ringer.api.v1.models import (
    CreateCrawlRequest,
    SeedUrlScrapeRequest, SeedUrlScrapeResponse
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
        assert data["message"] == "Ringer Web Crawler API"
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
    
    def test_create_crawl_success(self, client, mock_ringer, sample_crawl_spec_dict, sample_crawl_state):
        """Test successful crawl submission."""
        from ringer.core.models import RunState, RunStateEnum
        
        # Setup mock
        test_crawl_id = "test_crawl_123"
        test_run_state = RunState(state=RunStateEnum.CREATED)
        mock_ringer.create.return_value = (test_crawl_id, test_run_state)
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["run_state"]["state"] == "CREATED"
        assert "timestamp" in data["run_state"]
        # Verify create was called with crawl_spec and results_id
        mock_ringer.create.assert_called_once()
        call_args = mock_ringer.create.call_args
        assert len(call_args[0]) == 2  # crawl_spec and results_id
    
    def test_create_crawl_duplicate_id(self, client, mock_ringer, sample_crawl_spec_dict):
        """Test creating a crawl with duplicate ID returns 400."""
        mock_ringer.create.side_effect = ValueError("Crawl with ID test_crawl already exists")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 400
        assert "Crawl with ID test_crawl already exists" in response.json()["detail"]
    
    def test_create_crawl_invalid_spec(self, client, mock_ringer):
        """Test creating invalid crawl spec returns 422."""
        invalid_spec = {
            "name": "test_crawl",
            # Missing required fields
        }
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls",
            json={"crawl_spec": invalid_spec}
        )
        
        assert response.status_code == 422
    
    def test_create_crawl_internal_error(self, client, mock_ringer, sample_crawl_spec_dict):
        """Test internal server error during crawl submission."""
        mock_ringer.create.side_effect = Exception("Database connection failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestStartCrawlEndpoint:
    """Tests for the crawl start endpoint."""
    
    def test_start_crawl_success(self, client, mock_ringer, sample_crawl_state):
        """Test successful crawl start."""
        from ringer.core.models import RunState, RunStateEnum
        
        test_crawl_id = "test_crawl_123"
        test_run_state = RunState(state=RunStateEnum.RUNNING)
        mock_ringer.start.return_value = (test_crawl_id, test_run_state)
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            f"/api/v1/crawls/{test_crawl_id}/start"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["run_state"]["state"] == "RUNNING"
        assert "timestamp" in data["run_state"]
        mock_ringer.start.assert_called_once_with(test_crawl_id)
    
    def test_start_crawl_not_found(self, client, mock_ringer):
        """Test starting non-existent crawl returns 404."""
        mock_ringer.start.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls/nonexistent_id/start"
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_start_crawl_already_running(self, client, mock_ringer):
        """Test starting already running crawl returns 400."""
        mock_ringer.start.side_effect = RuntimeError("Crawl test_crawl is already running")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls/test_crawl/start"
        )
        
        assert response.status_code == 400
        assert "Crawl test_crawl is already running" in response.json()["detail"]
    
    def test_start_crawl_internal_error(self, client, mock_ringer):
        """Test internal server error during crawl start."""
        mock_ringer.start.side_effect = Exception("Thread pool exhausted")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls/test_crawl/start"
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestStopCrawlEndpoint:
    """Tests for the crawl stop endpoint."""
    
    def test_stop_crawl_success(self, client, mock_ringer, sample_crawl_state):
        """Test successful crawl stop."""
        from ringer.core.models import RunState, RunStateEnum
        
        test_crawl_id = "test_crawl_123"
        test_run_state = RunState(state=RunStateEnum.STOPPED)
        mock_ringer.stop.return_value = (test_crawl_id, test_run_state)
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            f"/api/v1/crawls/{test_crawl_id}/stop"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["run_state"]["state"] == "STOPPED"
        assert "timestamp" in data["run_state"]
        mock_ringer.stop.assert_called_once_with(test_crawl_id)
    
    def test_stop_crawl_not_found(self, client, mock_ringer):
        """Test stopping non-existent crawl returns 404."""
        mock_ringer.stop.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls/nonexistent_id/stop"
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_stop_crawl_already_stopped(self, client, mock_ringer):
        """Test stopping already stopped crawl returns 400."""
        mock_ringer.stop.side_effect = RuntimeError("Crawl test_crawl is not running")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls/test_crawl/stop"
        )
        
        assert response.status_code == 400
        assert "Crawl test_crawl is not running" in response.json()["detail"]
    
    def test_stop_crawl_internal_error(self, client, mock_ringer):
        """Test internal server error during crawl stop."""
        mock_ringer.stop.side_effect = Exception("Failed to stop workers")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.post(
            "/api/v1/crawls/test_crawl/stop"
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestDeleteCrawlEndpoint:
    """Tests for the crawl delete endpoint."""
    
    @patch('ringer.api.v1.routers.crawl.datetime')
    def test_delete_crawl_success(self, mock_datetime, client, mock_ringer):
        """Test successful crawl deletion."""
        test_crawl_id = "test_crawl_123"
        test_deletion_time = "2023-12-01T10:33:00Z"
        mock_datetime.utcnow.return_value.strftime.return_value = test_deletion_time
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.delete(
            f"/api/v1/crawls/{test_crawl_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["crawl_id"] == test_crawl_id
        assert data["crawl_deleted_time"] == test_deletion_time
        mock_ringer.delete.assert_called_once_with(test_crawl_id)
    
    def test_delete_crawl_not_found(self, client, mock_ringer):
        """Test deleting non-existent crawl returns 404."""
        mock_ringer.delete.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.delete(
            "/api/v1/crawls/nonexistent_id"
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_delete_crawl_still_running(self, client, mock_ringer):
        """Test deleting running crawl returns 400."""
        mock_ringer.delete.side_effect = RuntimeError("Cannot delete running crawl test_crawl")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.delete(
            "/api/v1/crawls/test_crawl"
        )
        
        assert response.status_code == 400
        assert "Cannot delete running crawl test_crawl" in response.json()["detail"]
    
    def test_delete_crawl_internal_error(self, client, mock_ringer):
        """Test internal server error during crawl deletion."""
        mock_ringer.delete.side_effect = Exception("Failed to cleanup resources")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.delete(
            "/api/v1/crawls/test_crawl"
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestCrawlStatusEndpoint:
    """Tests for the crawl status endpoint."""
    
    def test_get_all_crawl_statuses_success(self, client, mock_ringer):
        """Test successful retrieval of all crawl statuses."""
        from datetime import datetime
        
        # Mock the get_all_crawl_statuses method
        test_status_dicts = [
            {
                "crawl_id": "crawl_1",
                "crawl_name": "test_crawl_1",
                "current_state": "RUNNING",
                "state_history": [
                    {
                        "state": "CREATED",
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "state": "RUNNING", 
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "crawled_count": 10,
                "processed_count": 8,
                "error_count": 2,
                "frontier_size": 5
            },
            {
                "crawl_id": "crawl_2",
                "crawl_name": "test_crawl_2",
                "current_state": "STOPPED",
                "state_history": [
                    {
                        "state": "CREATED",
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "state": "STOPPED", 
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "crawled_count": 5,
                "processed_count": 5,
                "error_count": 0,
                "frontier_size": 0
            }
        ]
        
        mock_ringer.get_all_crawl_statuses.return_value = test_status_dicts
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "crawls" in data
        crawls = data["crawls"]
        assert len(crawls) == 2
        
        # Check first crawl
        assert crawls[0]["crawl_id"] == "crawl_1"
        assert crawls[0]["crawl_name"] == "test_crawl_1"
        assert crawls[0]["current_state"] == "RUNNING"
        
        # Check second crawl
        assert crawls[1]["crawl_id"] == "crawl_2"
        assert crawls[1]["crawl_name"] == "test_crawl_2"
        assert crawls[1]["current_state"] == "STOPPED"
        
        mock_ringer.get_all_crawl_statuses.assert_called_once()
    
    def test_get_all_crawl_statuses_empty(self, client, mock_ringer):
        """Test retrieval of all crawl statuses when no crawls exist."""
        mock_ringer.get_all_crawl_statuses.return_value = []
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "crawls" in data
        assert data["crawls"] == []
        
        mock_ringer.get_all_crawl_statuses.assert_called_once()
    
    def test_get_all_crawl_statuses_internal_error(self, client, mock_ringer):
        """Test internal server error during all crawl statuses retrieval."""
        mock_ringer.get_all_crawl_statuses.side_effect = Exception("Database connection failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls/status")
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_get_all_crawl_info_success(self, client, mock_ringer):
        """Test successful retrieval of all crawl info."""
        from datetime import datetime
        
        # Mock the get_all_crawl_info method
        test_info_dicts = [
            {
                "crawl_spec": {
                    "name": "test_crawl_1",
                    "seeds": ["https://example1.com"],
                    "analyzer_specs": [
                        {
                            "name": "KeywordScoreAnalyzer",
                            "composite_weight": 1.0,
                            "keywords": [
                                {"keyword": "test", "weight": 1.0}
                            ]
                        }
                    ],
                    "worker_count": 1,
                    "domain_blacklist": None
                },
                "crawl_status": {
                    "crawl_id": "crawl_1",
                    "crawl_name": "test_crawl_1",
                    "current_state": "RUNNING",
                    "state_history": [
                        {
                            "state": "CREATED",
                            "timestamp": datetime.now().isoformat()
                        },
                        {
                            "state": "RUNNING", 
                            "timestamp": datetime.now().isoformat()
                        }
                    ],
                    "crawled_count": 10,
                    "processed_count": 8,
                    "error_count": 2,
                    "frontier_size": 5
                }
            },
            {
                "crawl_spec": {
                    "name": "test_crawl_2",
                    "seeds": ["https://example2.com"],
                    "analyzer_specs": [
                        {
                            "name": "KeywordScoreAnalyzer",
                            "composite_weight": 1.0,
                            "keywords": [
                                {"keyword": "test", "weight": 1.0}
                            ]
                        }
                    ],
                    "worker_count": 1,
                    "domain_blacklist": None
                },
                "crawl_status": {
                    "crawl_id": "crawl_2",
                    "crawl_name": "test_crawl_2",
                    "current_state": "STOPPED",
                    "state_history": [
                        {
                            "state": "CREATED",
                            "timestamp": datetime.now().isoformat()
                        },
                        {
                            "state": "STOPPED", 
                            "timestamp": datetime.now().isoformat()
                        }
                    ],
                    "crawled_count": 5,
                    "processed_count": 5,
                    "error_count": 0,
                    "frontier_size": 0
                }
            }
        ]
        
        mock_ringer.get_all_crawl_info.return_value = test_info_dicts
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "crawls" in data
        crawls = data["crawls"]
        assert len(crawls) == 2
        
        # Check first crawl
        assert "crawl_spec" in crawls[0]
        assert "crawl_status" in crawls[0]
        assert crawls[0]["crawl_spec"]["name"] == "test_crawl_1"
        assert crawls[0]["crawl_status"]["crawl_id"] == "crawl_1"
        assert crawls[0]["crawl_status"]["current_state"] == "RUNNING"
        
        # Check second crawl
        assert crawls[1]["crawl_spec"]["name"] == "test_crawl_2"
        assert crawls[1]["crawl_status"]["crawl_id"] == "crawl_2"
        assert crawls[1]["crawl_status"]["current_state"] == "STOPPED"
        
        mock_ringer.get_all_crawl_info.assert_called_once()
    
    def test_get_all_crawl_info_empty(self, client, mock_ringer):
        """Test retrieval of all crawl info when no crawls exist."""
        mock_ringer.get_all_crawl_info.return_value = []
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "crawls" in data
        assert data["crawls"] == []
        
        mock_ringer.get_all_crawl_info.assert_called_once()
    
    def test_get_all_crawl_info_internal_error(self, client, mock_ringer):
        """Test internal server error during all crawl info retrieval."""
        mock_ringer.get_all_crawl_info.side_effect = Exception("Database connection failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls")
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_get_crawl_info_success(self, client, mock_ringer, sample_crawl_state):
        """Test successful crawl info retrieval."""
        from ringer.core.models import RunState, RunStateEnum
        from datetime import datetime
        
        test_crawl_id = "test_crawl_123"
        
        # Mock the get_crawl_info method to return a dictionary (as the actual implementation does)
        test_info_dict = {
            "crawl_spec": {
                "name": "test_crawl",
                "seeds": ["https://example.com"],
                "analyzer_specs": [
                    {
                        "name": "KeywordScoreAnalyzer",
                        "composite_weight": 1.0,
                        "keywords": [
                            {"keyword": "test", "weight": 1.0}
                        ]
                    }
                ],
                "worker_count": 1,
                "domain_blacklist": None
            },
            "crawl_status": {
                "crawl_id": test_crawl_id,
                "crawl_name": "test_crawl",
                "current_state": "RUNNING",
                "state_history": [
                    {
                        "state": "CREATED",
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "state": "RUNNING", 
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "crawled_count": 10,
                "processed_count": 8,
                "error_count": 2,
                "frontier_size": 5
            }
        }
        
        mock_ringer.get_crawl_info.return_value = test_info_dict
        # Also add the crawl to the mock's crawls dictionary to avoid any internal checks
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get(f"/api/v1/crawls/{test_crawl_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "info" in data
        info = data["info"]
        assert "crawl_spec" in info
        assert "crawl_status" in info
        
        # Check crawl spec
        assert info["crawl_spec"]["name"] == "test_crawl"
        assert info["crawl_spec"]["seeds"] == ["https://example.com"]
        
        # Check crawl status
        assert info["crawl_status"]["crawl_id"] == test_crawl_id
        assert info["crawl_status"]["crawl_name"] == "test_crawl"
        assert info["crawl_status"]["current_state"] == "RUNNING"
        assert info["crawl_status"]["crawled_count"] == 10
        assert info["crawl_status"]["processed_count"] == 8
        assert info["crawl_status"]["error_count"] == 2
        assert info["crawl_status"]["frontier_size"] == 5
        assert len(info["crawl_status"]["state_history"]) == 2
        
        mock_ringer.get_crawl_info.assert_called_once_with(test_crawl_id)
    
    def test_get_crawl_info_not_found(self, client, mock_ringer):
        """Test getting info for non-existent crawl returns 404."""
        mock_ringer.get_crawl_info.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls/nonexistent_id")
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_get_crawl_info_internal_error(self, client, mock_ringer):
        """Test internal server error during info retrieval."""
        mock_ringer.get_crawl_info.side_effect = Exception("Database connection failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls/test_crawl")
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_get_crawl_status_success(self, client, mock_ringer, sample_crawl_state):
        """Test successful crawl status retrieval."""
        from ringer.core.models import RunState, RunStateEnum
        from datetime import datetime
        
        test_crawl_id = "test_crawl_123"
        
        # Mock the get_crawl_status method to return a dictionary (as the actual implementation does)
        test_status_dict = {
            "crawl_id": test_crawl_id,
            "crawl_name": "test_crawl",
            "current_state": "RUNNING",
            "state_history": [
                {
                    "state": "CREATED",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "state": "RUNNING", 
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "crawled_count": 10,
            "processed_count": 8,
            "error_count": 2,
            "frontier_size": 5
        }
        
        mock_ringer.get_crawl_status.return_value = test_status_dict
        # Also add the crawl to the mock's crawls dictionary to avoid any internal checks
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get(f"/api/v1/crawls/{test_crawl_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        status = data["status"]
        assert status["crawl_id"] == test_crawl_id
        assert status["crawl_name"] == "test_crawl"
        assert status["current_state"] == "RUNNING"
        assert status["crawled_count"] == 10
        assert status["processed_count"] == 8
        assert status["error_count"] == 2
        assert status["frontier_size"] == 5
        assert len(status["state_history"]) == 2
        
        mock_ringer.get_crawl_status.assert_called_once_with(test_crawl_id)
    
    def test_get_crawl_status_not_found(self, client, mock_ringer):
        """Test getting status for non-existent crawl returns 404."""
        mock_ringer.get_crawl_status.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls/nonexistent_id/status")
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_get_crawl_status_internal_error(self, client, mock_ringer):
        """Test internal server error during status retrieval."""
        mock_ringer.get_crawl_status.side_effect = Exception("Database connection failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        response = client.get("/api/v1/crawls/test_crawl/status")
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestAnalyzersEndpoint:
    """Tests for the analyzers information endpoint."""
    
    def test_get_analyzer_info_success(self, client):
        """Test successful retrieval of analyzer information."""
        response = client.get("/api/v1/analyzers/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have analyzers list
        assert "analyzers" in data
        analyzers = data["analyzers"]
        
        # Should have at least KeywordScoreAnalyzer and DhLlmScoreAnalyzer
        analyzer_names = [analyzer["name"] for analyzer in analyzers]
        assert "KeywordScoreAnalyzer" in analyzer_names
        assert "DhLlmScoreAnalyzer" in analyzer_names
        
        # Check structure of analyzer info
        for analyzer in analyzers:
            assert "name" in analyzer
            assert "description" in analyzer
            assert "spec_fields" in analyzer
            
            # Check field structure
            for field in analyzer["spec_fields"]:
                assert "name" in field
                assert "type" in field
                assert "description" in field
                assert "required" in field
                # default is optional
    
    def test_get_analyzer_info_keyword_analyzer_fields(self, client):
        """Test that KeywordScoreAnalyzer has expected fields."""
        response = client.get("/api/v1/analyzers/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find KeywordScoreAnalyzer
        keyword_analyzer = None
        for analyzer in data["analyzers"]:
            if analyzer["name"] == "KeywordScoreAnalyzer":
                keyword_analyzer = analyzer
                break
        
        assert keyword_analyzer is not None
        
        # Check expected fields
        field_names = [field["name"] for field in keyword_analyzer["spec_fields"]]
        assert "name" in field_names
        assert "composite_weight" in field_names
        assert "keywords" in field_names
        
        # Check keywords field type
        keywords_field = next(field for field in keyword_analyzer["spec_fields"] if field["name"] == "keywords")
        assert "List[WeightedKeyword]" in keywords_field["type"]
    
    def test_get_analyzer_info_llm_analyzer_fields(self, client):
        """Test that DhLlmScoreAnalyzer has expected fields."""
        response = client.get("/api/v1/analyzers/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find DhLlmScoreAnalyzer
        llm_analyzer = None
        for analyzer in data["analyzers"]:
            if analyzer["name"] == "DhLlmScoreAnalyzer":
                llm_analyzer = analyzer
                break
        
        assert llm_analyzer is not None
        
        # Check expected fields
        field_names = [field["name"] for field in llm_analyzer["spec_fields"]]
        assert "name" in field_names
        assert "composite_weight" in field_names
        assert "scoring_input" in field_names
        
        # Check scoring_input field shows union type
        scoring_input_field = next(field for field in llm_analyzer["spec_fields"] if field["name"] == "scoring_input")
        assert "PromptInput" in scoring_input_field["type"]
        assert "TopicListInput" in scoring_input_field["type"]


class TestSeedsEndpoint:
    """Tests for the seeds collection endpoint."""
    
    def test_collect_seed_urls_success(self, client, mock_ringer):
        """Test successful seed URL collection."""
        from ringer.core.models import SearchEngineSeed, SearchEngineEnum
        
        # Setup mock
        test_seed_urls = ["https://example1.com", "https://example2.com"]
        mock_ringer.collect_seed_urls_from_search_engines.return_value = test_seed_urls
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        search_engine_seeds = [
            {
                "search_engine": "Google",
                "query": "test query",
                "result_count": 10
            }
        ]
        
        response = client.post(
            "/api/v1/seeds/collect",
            json={"search_engine_seeds": search_engine_seeds}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["seed_urls"] == test_seed_urls
        mock_ringer.collect_seed_urls_from_search_engines.assert_called_once()
    
    def test_collect_seed_urls_internal_error(self, client, mock_ringer):
        """Test internal server error during seed URL collection."""
        mock_ringer.collect_seed_urls_from_search_engines.side_effect = Exception("Search engine failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        search_engine_seeds = [
            {
                "search_engine": "Google", 
                "query": "test query",
                "result_count": 10
            }
        ]
        
        response = client.post(
            "/api/v1/seeds/collect",
            json={"search_engine_seeds": search_engine_seeds}
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestResultsEndpoint:
    """Tests for the results endpoints."""
    
    def test_get_crawl_record_summaries_success(self, client, mock_ringer, sample_crawl_state):
        """Test successful retrieval of crawl record summaries."""
        from ringer.core.models import CrawlRecordSummary
        
        test_crawl_id = "test_crawl_123"
        
        # Mock record summaries
        test_record_summaries = [
            CrawlRecordSummary(
                id="record_1",
                url="https://example1.com",
                score=0.95
            ),
            CrawlRecordSummary(
                id="record_2", 
                url="https://example2.com",
                score=0.87
            )
        ]
        
        mock_ringer.get_crawl_record_summaries.return_value = test_record_summaries
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_count": 10,
            "score_type": "composite"
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/record_summaries",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "records" in data
        records = data["records"]
        assert len(records) == 2
        
        # Check first record
        assert records[0]["id"] == "record_1"
        assert records[0]["url"] == "https://example1.com"
        assert records[0]["score"] == 0.95
        
        # Check second record
        assert records[1]["id"] == "record_2"
        assert records[1]["url"] == "https://example2.com"
        assert records[1]["score"] == 0.87
        
        mock_ringer.get_crawl_record_summaries.assert_called_once_with(
            crawl_id=test_crawl_id,
            record_count=10,
            score_type="composite"
        )
    
    def test_get_crawl_record_summaries_not_found(self, client, mock_ringer):
        """Test getting record summaries for non-existent crawl returns 404."""
        mock_ringer.get_crawl_record_summaries.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_count": 10,
            "score_type": "composite"
        }
        
        response = client.post(
            "/api/v1/results/nonexistent_id/record_summaries",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_get_crawl_record_summaries_invalid_score_type(self, client, mock_ringer):
        """Test getting record summaries with invalid score type returns 400."""
        mock_ringer.get_crawl_record_summaries.side_effect = ValueError("Invalid score_type: invalid_type")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_count": 10,
            "score_type": "invalid_type"
        }
        
        response = client.post(
            "/api/v1/results/test_crawl/record_summaries",
            json=request_data
        )
        
        assert response.status_code == 400
        assert "Invalid score_type" in response.json()["detail"]
    
    def test_get_crawl_record_summaries_invalid_request(self, client, mock_ringer):
        """Test getting record summaries with invalid request data returns 422."""
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        # Missing required fields
        request_data = {
            "record_count": 10
            # Missing score_type
        }
        
        response = client.post(
            "/api/v1/results/test_crawl/record_summaries",
            json=request_data
        )
        
        assert response.status_code == 422
    
    def test_get_crawl_record_summaries_internal_error(self, client, mock_ringer):
        """Test internal server error during record summaries retrieval."""
        mock_ringer.get_crawl_record_summaries.side_effect = Exception("Database connection failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_count": 10,
            "score_type": "composite"
        }
        
        response = client.post(
            "/api/v1/results/test_crawl/record_summaries",
            json=request_data
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_get_crawl_record_summaries_different_score_types(self, client, mock_ringer, sample_crawl_state):
        """Test getting record summaries with different score types."""
        from ringer.core.models import CrawlRecordSummary
        
        test_crawl_id = "test_crawl_123"
        
        # Mock record summaries for keyword analyzer
        test_record_summaries = [
            CrawlRecordSummary(
                id="record_1",
                url="https://example1.com",
                score=0.75
            )
        ]
        
        mock_ringer.get_crawl_record_summaries.return_value = test_record_summaries
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_count": 5,
            "score_type": "KeywordScoreAnalyzer"
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/record_summaries",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "records" in data
        records = data["records"]
        assert len(records) == 1
        assert records[0]["score"] == 0.75
        
        mock_ringer.get_crawl_record_summaries.assert_called_once_with(
            crawl_id=test_crawl_id,
            record_count=5,
            score_type="KeywordScoreAnalyzer"
        )
    
    def test_get_crawl_records_success(self, client, mock_ringer, sample_crawl_state):
        """Test successful retrieval of crawl records."""
        from ringer.core.models import CrawlRecord
        
        test_crawl_id = "test_crawl_123"
        
        # Mock full crawl records
        test_records = [
            CrawlRecord(
                url="https://example1.com",
                page_source="<html><body>Content 1</body></html>",
                extracted_content="Content 1 about python programming",
                links=["https://example1.com/link1"],
                scores={"KeywordScoreAnalyzer": 0.95},
                composite_score=0.95
            ),
            CrawlRecord(
                url="https://example2.com", 
                page_source="<html><body>Content 2</body></html>",
                extracted_content="Content 2 about web development",
                links=["https://example2.com/link1", "https://example2.com/link2"],
                scores={"KeywordScoreAnalyzer": 0.87},
                composite_score=0.87
            )
        ]
        
        mock_ringer.get_crawl_records.return_value = test_records
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_ids": ["record_1", "record_2"]
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/records",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "records" in data
        records = data["records"]
        assert len(records) == 2
        
        # Check first record
        assert records[0]["url"] == "https://example1.com"
        assert records[0]["page_source"] == "<html><body>Content 1</body></html>"
        assert records[0]["extracted_content"] == "Content 1 about python programming"
        assert records[0]["links"] == ["https://example1.com/link1"]
        assert records[0]["scores"]["KeywordScoreAnalyzer"] == 0.95
        assert records[0]["composite_score"] == 0.95
        
        # Check second record
        assert records[1]["url"] == "https://example2.com"
        assert records[1]["page_source"] == "<html><body>Content 2</body></html>"
        assert records[1]["extracted_content"] == "Content 2 about web development"
        assert records[1]["links"] == ["https://example2.com/link1", "https://example2.com/link2"]
        assert records[1]["scores"]["KeywordScoreAnalyzer"] == 0.87
        assert records[1]["composite_score"] == 0.87
        
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id=test_crawl_id,
            record_ids=["record_1", "record_2"]
        )
    
    def test_get_crawl_records_not_found(self, client, mock_ringer):
        """Test getting records for non-existent crawl returns 404."""
        mock_ringer.get_crawl_records.side_effect = ValueError("Crawl nonexistent_id not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_ids": ["record_1", "record_2"]
        }
        
        response = client.post(
            "/api/v1/results/nonexistent_id/records",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "Crawl nonexistent_id not found" in response.json()["detail"]
    
    def test_get_crawl_records_no_records_found(self, client, mock_ringer, sample_crawl_state):
        """Test getting records when no records exist for given IDs returns 404."""
        test_crawl_id = "test_crawl_123"
        
        # Mock empty result
        mock_ringer.get_crawl_records.return_value = []
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_ids": ["nonexistent_record_1", "nonexistent_record_2"]
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/records",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "No records found for the provided record IDs" in response.json()["detail"]
        assert test_crawl_id in response.json()["detail"]
    
    def test_get_crawl_records_partial_results(self, client, mock_ringer, sample_crawl_state):
        """Test getting records when only some records exist for given IDs."""
        from ringer.core.models import CrawlRecord
        
        test_crawl_id = "test_crawl_123"
        
        # Mock partial result - only one record found out of three requested
        test_records = [
            CrawlRecord(
                url="https://example1.com",
                page_source="<html><body>Content 1</body></html>",
                extracted_content="Content 1 about python programming",
                links=["https://example1.com/link1"],
                scores={"KeywordScoreAnalyzer": 0.95},
                composite_score=0.95
            )
        ]
        
        mock_ringer.get_crawl_records.return_value = test_records
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_ids": ["record_1", "nonexistent_record_1", "nonexistent_record_2"]
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/records",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "records" in data
        records = data["records"]
        assert len(records) == 1  # Only one record found
        assert records[0]["url"] == "https://example1.com"
        
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id=test_crawl_id,
            record_ids=["record_1", "nonexistent_record_1", "nonexistent_record_2"]
        )
    
    def test_get_crawl_records_invalid_request(self, client, mock_ringer):
        """Test getting records with invalid request data returns 422."""
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        # Missing required fields
        request_data = {
            # Missing record_ids
        }
        
        response = client.post(
            "/api/v1/results/test_crawl/records",
            json=request_data
        )
        
        assert response.status_code == 422
    
    def test_get_crawl_records_empty_record_ids(self, client, mock_ringer, sample_crawl_state):
        """Test getting records with empty record_ids list returns 404."""
        test_crawl_id = "test_crawl_123"
        
        # Mock empty result for empty input
        mock_ringer.get_crawl_records.return_value = []
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_ids": []
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/records",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "No records found for the provided record IDs" in response.json()["detail"]
    
    def test_get_crawl_records_internal_error(self, client, mock_ringer):
        """Test internal server error during records retrieval."""
        mock_ringer.get_crawl_records.side_effect = Exception("Database connection failed")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_ids": ["record_1", "record_2"]
        }
        
        response = client.post(
            "/api/v1/results/test_crawl/records",
            json=request_data
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_get_crawl_records_single_record(self, client, mock_ringer, sample_crawl_state):
        """Test getting a single record by ID."""
        from ringer.core.models import CrawlRecord
        
        test_crawl_id = "test_crawl_123"
        
        # Mock single record result
        test_records = [
            CrawlRecord(
                url="https://example.com",
                page_source="<html><body>Single record content</body></html>",
                extracted_content="Single record about machine learning",
                links=["https://example.com/ml", "https://example.com/ai"],
                scores={"KeywordScoreAnalyzer": 0.92, "DhLlmScoreAnalyzer": 0.88},
                composite_score=0.90
            )
        ]
        
        mock_ringer.get_crawl_records.return_value = test_records
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        request_data = {
            "record_ids": ["single_record_id"]
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/records",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "records" in data
        records = data["records"]
        assert len(records) == 1
        
        record = records[0]
        assert record["url"] == "https://example.com"
        assert record["extracted_content"] == "Single record about machine learning"
        assert len(record["links"]) == 2
        assert record["scores"]["KeywordScoreAnalyzer"] == 0.92
        assert record["scores"]["DhLlmScoreAnalyzer"] == 0.88
        assert record["composite_score"] == 0.90
        
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id=test_crawl_id,
            record_ids=["single_record_id"]
        )
    
    def test_get_crawl_records_large_batch(self, client, mock_ringer, sample_crawl_state):
        """Test getting a large batch of records."""
        from ringer.core.models import CrawlRecord
        
        test_crawl_id = "test_crawl_123"
        
        # Mock large batch of records
        test_records = []
        for i in range(50):
            record = CrawlRecord(
                url=f"https://example{i}.com",
                page_source=f"<html><body>Content {i}</body></html>",
                extracted_content=f"Content {i} about topic {i}",
                links=[f"https://example{i}.com/link1", f"https://example{i}.com/link2"],
                scores={"KeywordScoreAnalyzer": 0.5 + (i * 0.01)},
                composite_score=0.5 + (i * 0.01)
            )
            test_records.append(record)
        
        mock_ringer.get_crawl_records.return_value = test_records
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        # Request 50 record IDs
        record_ids = [f"record_{i}" for i in range(50)]
        request_data = {
            "record_ids": record_ids
        }
        
        response = client.post(
            f"/api/v1/results/{test_crawl_id}/records",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "records" in data
        records = data["records"]
        assert len(records) == 50
        
        # Check first and last records
        assert records[0]["url"] == "https://example0.com"
        assert records[49]["url"] == "https://example49.com"
        assert records[49]["composite_score"] == 0.99  # 0.5 + (49 * 0.01)
        
        mock_ringer.get_crawl_records.assert_called_once_with(
            crawl_id=test_crawl_id,
            record_ids=record_ids
        )


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
    
    def test_seed_url_scrape_request_validation(self):
        """Test SeedUrlScrapeRequest model validation."""
        from ringer.core.models import SearchEngineSeed, SearchEngineEnum
        
        # Valid request
        search_engine_seeds = [
            SearchEngineSeed(
                search_engine=SearchEngineEnum.GOOGLE,
                query="test query",
                result_count=10
            )
        ]
        request = SeedUrlScrapeRequest(search_engine_seeds=search_engine_seeds)
        assert len(request.search_engine_seeds) == 1
        
        # Invalid request - missing search_engine_seeds
        with pytest.raises(ValueError):
            SeedUrlScrapeRequest()
    
    def test_crawl_record_request_validation(self):
        """Test CrawlRecordRequest model validation."""
        from ringer.api.v1.models import CrawlRecordRequest
        
        # Valid request
        request = CrawlRecordRequest(record_ids=["record_1", "record_2", "record_3"])
        assert len(request.record_ids) == 3
        assert request.record_ids == ["record_1", "record_2", "record_3"]
        
        # Valid request with single record
        single_request = CrawlRecordRequest(record_ids=["single_record"])
        assert len(single_request.record_ids) == 1
        
        # Valid request with empty list
        empty_request = CrawlRecordRequest(record_ids=[])
        assert len(empty_request.record_ids) == 0
        
        # Invalid request - missing record_ids
        with pytest.raises(ValueError):
            CrawlRecordRequest()
    
    def test_crawl_record_response_validation(self):
        """Test CrawlRecordResponse model validation."""
        from ringer.api.v1.models import CrawlRecordResponse
        from ringer.core.models import CrawlRecord
        
        # Create test records
        test_records = [
            CrawlRecord(
                url="https://example1.com",
                page_source="<html><body>Content 1</body></html>",
                extracted_content="Content 1 about python",
                links=["https://example1.com/link1"],
                scores={"KeywordScoreAnalyzer": 0.8},
                composite_score=0.8
            ),
            CrawlRecord(
                url="https://example2.com",
                page_source="<html><body>Content 2</body></html>",
                extracted_content="Content 2 about programming",
                links=["https://example2.com/link1", "https://example2.com/link2"],
                scores={"KeywordScoreAnalyzer": 0.9},
                composite_score=0.9
            )
        ]
        
        # Valid response
        response = CrawlRecordResponse(records=test_records)
        assert len(response.records) == 2
        assert response.records[0].url == "https://example1.com"
        assert response.records[1].url == "https://example2.com"
        
        # Valid response with empty records
        empty_response = CrawlRecordResponse(records=[])
        assert len(empty_response.records) == 0
        
        # Invalid response - missing records
        with pytest.raises(ValueError):
            CrawlRecordResponse()
    


class TestApplicationLifespan:
    """Tests for FastAPI application lifespan management."""
    
    @patch('ringer.main.Ringer')
    def test_lifespan_startup_shutdown(self, mock_ringer_class):
        """Test that ringer is created on startup and shutdown on exit."""
        from contextlib import asynccontextmanager
        from fastapi import FastAPI
        from ringer.main import lifespan
        
        mock_ringer_instance = Mock()
        mock_ringer_class.return_value = mock_ringer_instance
        
        # Create a test app to test the lifespan
        test_app = FastAPI()
        
        # Manually run the lifespan context manager
        async def run_lifespan():
            async with lifespan(test_app):
                # Verify ringer was created and stored in app state
                mock_ringer_class.assert_called_once()
                assert hasattr(test_app.state, 'ringer')
                assert test_app.state.ringer == mock_ringer_instance
        
        # Run the async lifespan
        import asyncio
        asyncio.run(run_lifespan())
        
        # Verify shutdown was called
        mock_ringer_instance.shutdown.assert_called_once()


class TestEndToEndWorkflow:
    """End-to-end tests for complete crawl workflow."""
    
    def test_complete_crawl_workflow(self, client, mock_ringer, sample_crawl_spec_dict, sample_crawl_state):
        """Test complete workflow: create -> start -> stop -> delete."""
        from ringer.core.models import RunState, RunStateEnum
        
        test_crawl_id = "workflow_test_123"
        
        # Setup mock responses
        create_state = RunState(state=RunStateEnum.CREATED)
        start_state = RunState(state=RunStateEnum.RUNNING)
        stop_state = RunState(state=RunStateEnum.STOPPED)
        
        mock_ringer.create.return_value = (test_crawl_id, create_state)
        mock_ringer.start.return_value = (test_crawl_id, start_state)
        mock_ringer.stop.return_value = (test_crawl_id, stop_state)
        mock_ringer.crawls = {test_crawl_id: sample_crawl_state}
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        # 1. create crawl
        create_response = client.post(
            "/api/v1/crawls",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        assert create_response.status_code == 200
        assert create_response.json()["crawl_id"] == test_crawl_id
        assert create_response.json()["run_state"]["state"] == "CREATED"
        
        # 2. Start crawl
        start_response = client.post(
            f"/api/v1/crawls/{test_crawl_id}/start"
        )
        assert start_response.status_code == 200
        assert start_response.json()["crawl_id"] == test_crawl_id
        assert start_response.json()["run_state"]["state"] == "RUNNING"
        
        # 3. Stop crawl
        stop_response = client.post(
            f"/api/v1/crawls/{test_crawl_id}/stop"
        )
        assert stop_response.status_code == 200
        assert stop_response.json()["crawl_id"] == test_crawl_id
        assert stop_response.json()["run_state"]["state"] == "STOPPED"
        
        # 4. Delete crawl
        with patch('ringer.api.v1.routers.crawl.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.strftime.return_value = "2023-12-01T10:35:00Z"
            delete_response = client.delete(
                f"/api/v1/crawls/{test_crawl_id}"
            )
            assert delete_response.status_code == 200
            assert delete_response.json()["crawl_id"] == test_crawl_id
        
        # Verify all methods were called - create now takes 2 args (crawl_spec, results_id)
        mock_ringer.create.assert_called_once()
        call_args = mock_ringer.create.call_args
        assert len(call_args[0]) == 2  # crawl_spec and results_id
        mock_ringer.start.assert_called_once_with(test_crawl_id)
        mock_ringer.stop.assert_called_once_with(test_crawl_id)
        mock_ringer.delete.assert_called_once_with(test_crawl_id)
    
    def test_invalid_workflow_order(self, client, mock_ringer):
        """Test that invalid workflow order returns appropriate errors."""
        nonexistent_crawl_id = "nonexistent_123"
        
        # Setup mock to raise ValueError for nonexistent crawl
        mock_ringer.start.side_effect = ValueError(f"Crawl {nonexistent_crawl_id} not found")
        
        # Set the ringer in app state
        app.state.ringer = mock_ringer
        
        # Try to start non-existent crawl
        response = client.post(
            f"/api/v1/crawls/{nonexistent_crawl_id}/start"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestErrorHandling:
    """Tests for comprehensive error handling scenarios."""
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON requests."""
        response = client.post(
            "/api/v1/crawls",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_request_body(self, client):
        """Test handling of missing request body."""
        response = client.post("/api/v1/crawls")
        assert response.status_code == 422
    
    def test_invalid_content_type(self, client, sample_crawl_spec_dict):
        """Test handling of invalid content type."""
        response = client.post(
            "/api/v1/crawls",
            content=str(sample_crawl_spec_dict),
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422
    
    def test_ringer_not_initialized(self, client, sample_crawl_spec_dict):
        """Test handling when ringer is not properly initialized."""
        # Remove ringer from app state
        if hasattr(app.state, 'ringer'):
            delattr(app.state, 'ringer')
        
        response = client.post(
            "/api/v1/crawls",
            json={"crawl_spec": sample_crawl_spec_dict}
        )
        assert response.status_code == 500
