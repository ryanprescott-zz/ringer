"""Tests for crawl results managers."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from prospector.core.results_managers import (
    FsCrawlResultsManager,
    DhCrawlResultsManager,
)
from prospector.core import CrawlRecord


class TestDhCrawlResultsManager:
    """Tests for DhCrawlResultsManager class."""
    
    def test_init(self):
        """Test service manager initialization."""
        manager = DhCrawlResultsManager()
        assert manager.settings is not None
        assert manager.session is not None
        assert manager.session.headers['Content-Type'] == 'application/json'
    
    @patch('prospector.core.results_managers.dh_crawl_results_manager.requests.Session.post')
    def test_store_record_success(self, mock_post, sample_crawl_record):
        """Test successful record handling via service."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_post.return_value = mock_response
        
        manager = DhCrawlResultsManager()
        
        # Should not raise any exception
        manager.store_record(sample_crawl_record, "test_crawl_id")
        
        # Verify request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify URL and timeout
        assert call_args[0][0] == manager.settings.service_url
        assert call_args[1]['timeout'] == manager.settings.service_timeout_sec
        
        # Verify request payload structure
        request_data = call_args[1]['json']
        assert 'record' in request_data
        assert 'crawl_id' in request_data
        assert request_data['crawl_id'] == "test_crawl_id"
    
    @patch('prospector.core.results_managers.dh_crawl_results_manager.requests.Session.post')
    def test_store_record_http_error_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with HTTP error after all retries."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        manager = DhCrawlResultsManager()
        
        # Should not raise exception, just log and discard
        manager.store_record(sample_crawl_record, "test_storage_id")
        
        # Should have made multiple attempts (3 retries + 1 initial = 4 total)
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.results_managers.dh_crawl_results_manager.requests.Session.post')
    def test_store_record_timeout_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with timeout after all retries."""
        import requests
        
        # Mock timeout exception
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        manager = DhCrawlResultsManager()
        
        # Should not raise exception, just log and discard
        manager.store_record(sample_crawl_record, "test_storage_id")
        
        # Should have made multiple attempts
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.results_managers.dh_crawl_results_manager.requests.Session.post')
    def test_store_record_connection_error_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with connection error after all retries."""
        import requests
        
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        manager = DhCrawlResultsManager()
        
        # Should not raise exception, just log and discard
        manager.store_record(sample_crawl_record, "test_storage_id")
        
        # Should have made multiple attempts
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.results_managers.dh_crawl_results_manager.requests.Session.post')
    def test_store_record_success_after_retry(self, mock_post, sample_crawl_record):
        """Test successful handling after initial failures."""
        # Mock first call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Service Unavailable"
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.text = "Success"
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        manager = DhCrawlResultsManager()
        
        # Should succeed after retry
        manager.store_record(sample_crawl_record, "test_storage_id")
        
        # Should have made 2 calls
        assert mock_post.call_count == 2
    


class TestFsCrawlResultsManager:
    """Tests for FsCrawlResultsManager class."""
    
    def test_init(self):
        """Test manager initialization."""
        manager = FsCrawlResultsManager()
        assert manager.settings is not None
    
    def test_store_record_success(self, sample_crawl_record, sample_crawl_spec):
        """Test successful record handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch the settings to use temp directory
            with patch.object(FsCrawlResultsManager, '__init__', lambda x: None):
                manager = FsCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'crawl_data_dir': temp_dir
                })()
                manager.base_dir = Path(temp_dir)
                
                # First create the crawl and get storage ID
                storage_id = manager.create_crawl(sample_crawl_spec)
                manager.store_record(sample_crawl_record, storage_id)
                
                # Check that directory was created with storage ID
                expected_dir = Path(temp_dir) / storage_id
                assert expected_dir.exists()
                
                # Check that file was created
                files = list(expected_dir.glob("*.json"))
                assert len(files) >= 1  # crawl_spec.json + record file
                
                # Find the record file (not crawl_spec.json)
                record_files = [f for f in files if f.name != "crawl_spec.json"]
                assert len(record_files) == 1
                
                # Check file content
                with open(record_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert data['url'] == sample_crawl_record.url
                    assert data['extracted_content'] == sample_crawl_record.extracted_content
    
    def test_store_record_directory_creation(self, sample_crawl_record, sample_crawl_spec):
        """Test that directories are created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(FsCrawlResultsManager, '__init__', lambda x: None):
                manager = FsCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'crawl_data_dir': temp_dir
                })()
                manager.base_dir = Path(temp_dir)
                
                # Create crawl and handle multiple records for same crawl
                storage_id = manager.create_crawl(sample_crawl_spec)
                manager.store_record(sample_crawl_record, storage_id)
                
                record2 = CrawlRecord(
                    url="https://example2.com",
                    page_source="<html></html>",
                    extracted_content="Different content",
                    links=[],
                    scores={},
                    composite_score=0.0
                )
                manager.store_record(record2, storage_id)
                
                # Should create same directory structure
                expected_dir = Path(temp_dir) / storage_id
                files = list(expected_dir.glob("*.json"))
                # Should have crawl_spec.json + 2 record files
                assert len(files) == 3
    
    
    def test_store_record_file_write_error(self, sample_crawl_record):
        """Test handling of file write errors."""
        # Use a non-existent directory that can't be created
        with patch.object(FsCrawlResultsManager, '__init__', lambda x: None):
            manager = FsCrawlResultsManager()
            manager.settings = type('Settings', (), {
                'crawl_data_dir': '/invalid/path'
            })()
            manager.base_dir = Path('/invalid/path')
            
            with pytest.raises(Exception):
                manager.store_record(sample_crawl_record, "test_storage_id")
