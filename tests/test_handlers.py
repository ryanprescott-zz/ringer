"""Tests for crawl record handlers."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from prospector.core.handlers import (
    FsStoreHandler,
    ServiceCallHandler,
)
from prospector.core.models import CrawlRecord


class TestServiceCallHandler:
    """Tests for ServiceCallHandler class."""
    
    def test_init(self):
        """Test service handler initialization."""
        handler = ServiceCallHandler()
        assert handler.settings is not None
        assert handler.session is not None
        assert handler.session.headers['Content-Type'] == 'application/json'
    
    @patch('prospector.core.handlers.service_call_handler.requests.Session.post')
    def test_store_record_success(self, mock_post, sample_crawl_record):
        """Test successful record handling via service."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_post.return_value = mock_response
        
        handler = ServiceCallHandler()
        
        # Should not raise any exception
        handler.store_record(sample_crawl_record, "test_crawl")
        
    #     # Verify request was made
    #     mock_post.assert_called_once()
    #     call_args = mock_post.call_args
        
        # Verify URL and timeout
        assert call_args[0][0] == handler.settings.service_url
        assert call_args[1]['timeout'] == handler.settings.service_timeout_sec
        
        # Verify request payload structure
        request_data = call_args[1]['json']
        assert 'record' in request_data
        assert 'crawl_name' in request_data
        assert request_data['crawl_name'] == "test_crawl"
    
    @patch('prospector.core.handlers.service_call_handler.requests.Session.post')
    def test_store_record_http_error_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with HTTP error after all retries."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        handler = ServiceCallHandler()
        
        # Should not raise exception, just log and discard
        handler.store_record(sample_crawl_record, "test_crawl")
        
        # Should have made multiple attempts (3 retries + 1 initial = 4 total)
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.handlers.service_call_handler.requests.Session.post')
    def test_store_record_timeout_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with timeout after all retries."""
        import requests
        
        # Mock timeout exception
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        handler = ServiceCallHandler()
        
        # Should not raise exception, just log and discard
        handler.store_record(sample_crawl_record, "test_crawl")
        
        # Should have made multiple attempts
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.handlers.service_call_handler.requests.Session.post')
    def test_store_record_connection_error_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with connection error after all retries."""
        import requests
        
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        handler = ServiceCallHandler()
        
        # Should not raise exception, just log and discard
        handler.store_record(sample_crawl_record, "test_crawl")
        
        # Should have made multiple attempts
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.handlers.service_call_handler.requests.Session.post')
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
        
        handler = ServiceCallHandler()
        
        # Should succeed after retry
        handler.store_record(sample_crawl_record, "test_crawl")
        
        # Should have made 2 calls
        assert mock_post.call_count == 2
    


class TestFsStoreHandler:
    """Tests for FsStoreHandler class."""
    
    def test_init(self):
        """Test handler initialization."""
        handler = FsStoreHandler()
        assert handler.settings is not None
    
    def test_store_record_success(self, sample_crawl_record):
        """Test successful record handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch the settings to use temp directory
            with patch.object(FsStoreHandler, '__init__', lambda x: None):
                handler = FsStoreHandler()
                handler.settings = type('Settings', (), {
                    'output_directory': temp_dir,
                    'record_directory': 'records'
                })()
                
                # First create the crawl
                handler.create_crawl("test_crawl")
                handler.store_record(sample_crawl_record, "test_crawl")
                
                # Check that directory was created
                expected_dir = Path(temp_dir) / "test_crawl" / "records"
                assert expected_dir.exists()
                
                # Check that file was created
                files = list(expected_dir.glob("*.json"))
                assert len(files) == 1
                
                # Check file content
                with open(files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert data['url'] == sample_crawl_record.url
                    assert data['extracted_content'] == sample_crawl_record.extracted_content
    
    def test_store_record_directory_creation(self, sample_crawl_record):
        """Test that directories are created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(FsStoreHandler, '__init__', lambda x: None):
                handler = FsStoreHandler()
                handler.settings = type('Settings', (), {
                    'output_directory': temp_dir,
                    'record_directory': 'records'
                })()
                
                # Create crawl and handle multiple records for same crawl
                handler.create_crawl("test_crawl")
                handler.store_record(sample_crawl_record, "test_crawl")
                
                record2 = CrawlRecord(
                    url="https://example2.com",
                    page_source="<html></html>",
                    extracted_content="Different content",
                    links=[],
                    scores={},
                    composite_score=0.0
                )
                handler.store_record(record2, "test_crawl")
                
                # Should create same directory structure
                expected_dir = Path(temp_dir) / "test_crawl" / "records"
                files = list(expected_dir.glob("*.json"))
                assert len(files) == 2
    
    def test_store_record_filename_generation(self, sample_crawl_record):
        """Test that filenames are generated from URL hash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(FsStoreHandler, '__init__', lambda x: None):
                handler = FsStoreHandler()
                handler.settings = type('Settings', (), {
                    'output_directory': temp_dir,
                    'record_directory': 'records'
                })()
                
                handler.create_crawl("test_crawl")
                handler.store_record(sample_crawl_record, "test_crawl")
                
                # Check filename is MD5 hash
                expected_dir = Path(temp_dir) / "test_crawl" / "records"
                files = list(expected_dir.glob("*.json"))
                
                import hashlib
                expected_hash = hashlib.md5(sample_crawl_record.url.encode()).hexdigest()
                expected_filename = f"{expected_hash}.json"
                
                assert files[0].name == expected_filename
    
    def test_store_record_file_write_error(self, sample_crawl_record):
        """Test handling of file write errors."""
        # Use a non-existent directory that can't be created
        with patch.object(FsStoreHandler, '__init__', lambda x: None):
            handler = FsStoreHandler()
            handler.settings = type('Settings', (), {
                'output_directory': '/invalid/path',
                'record_directory': 'records'
            })()
            
            with pytest.raises(OSError, match="Failed to store crawl record"):
                handler.store_record(sample_crawl_record, "test_crawl")
