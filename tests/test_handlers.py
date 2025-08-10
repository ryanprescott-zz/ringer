"""Tests for crawl record handlers."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from prospector.core import (
    FsStoreCrawlRecordHandler,
    ServiceCrawlRecordHandler,
    CrawlRecord,
)


class TestServiceCrawlRecordHandler:
    """Tests for ServiceCrawlRecordHandler class."""
    
    def test_init(self):
        """Test service handler initialization."""
        handler = ServiceCrawlRecordHandler()
        assert handler.settings is not None
        assert handler.session is not None
        assert handler.session.headers['Content-Type'] == 'application/json'
    
    # @patch('prospector.core.handlers.service_crawl_record_handler.requests.Session.post')
    # def test_handle_success(self, mock_post, sample_crawl_record):
    #     """Test successful record handling via service."""
    #     # Mock successful response
    #     mock_response = Mock()
    #     mock_response.status_code = 200
    #     mock_response.text = "Success"
    #     mock_post.return_value = mock_response
        
    #     handler = ServiceCrawlRecordHandler()
        
    #     # Should not raise any exception
    #     handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
        
    #     # Verify request was made
    #     mock_post.assert_called_once()
    #     call_args = mock_post.call_args
        
    #     # Verify URL and timeout
    #     assert call_args[0][0] == handler.settings.service_url
    #     assert call_args[1]['timeout'] == handler.settings.service_timeout
        
    #     # Verify request payload structure
    #     request_data = call_args[1]['json']
    #     assert 'record' in request_data
    #     assert 'crawl_name' in request_data
    #     assert 'crawl_datetime' in request_data
    #     assert request_data['crawl_name'] == "test_crawl"
    #     assert request_data['crawl_datetime'] == "20240101_120000"
    
    # @patch('prospector.core.handlers.service_crawl_record_handler.requests.Session.post')
    # def test_handle_http_error_after_retries(self, mock_post, sample_crawl_record):
    #     """Test handling with HTTP error after all retries."""
    #     # Mock HTTP error response
    #     mock_response = Mock()
    #     mock_response.status_code = 500
    #     mock_response.text = "Internal Server Error"
    #     mock_post.return_value = mock_response
        
    #     handler = ServiceCrawlRecordHandler()
        
    #     # Should not raise exception, just log and discard
    #     handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
        
    #     # Should have made multiple attempts (3 retries + 1 initial = 4 total)
    #     assert mock_post.call_count >= 3
    
    # @patch('prospector.core.handlers.service_crawl_record_handler.requests.Session.post')
    # def test_handle_timeout_after_retries(self, mock_post, sample_crawl_record):
    #     """Test handling with timeout after all retries."""
    #     import requests
        
    #     # Mock timeout exception
    #     mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
    #     handler = ServiceCrawlRecordHandler()
        
    #     # Should not raise exception, just log and discard
    #     handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
        
    #     # Should have made multiple attempts
    #     assert mock_post.call_count >= 3
    
    # @patch('prospector.core.handlers.service_crawl_record_handler.requests.Session.post')
    # def test_handle_connection_error_after_retries(self, mock_post, sample_crawl_record):
    #     """Test handling with connection error after all retries."""
    #     import requests
        
    #     # Mock connection error
    #     mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
    #     handler = ServiceCrawlRecordHandler()
        
    #     # Should not raise exception, just log and discard
    #     handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
        
    #     # Should have made multiple attempts
    #     assert mock_post.call_count >= 3
    
    # @patch('prospector.core.handlers.service_crawl_record_handler.requests.Session.post')
    # def test_handle_success_after_retry(self, mock_post, sample_crawl_record):
    #     """Test successful handling after initial failures."""
    #     # Mock first call fails, second succeeds
    #     mock_response_fail = Mock()
    #     mock_response_fail.status_code = 503
    #     mock_response_fail.text = "Service Unavailable"
        
    #     mock_response_success = Mock()
    #     mock_response_success.status_code = 200
    #     mock_response_success.text = "Success"
        
    #     mock_post.side_effect = [mock_response_fail, mock_response_success]
        
    #     handler = ServiceCrawlRecordHandler()
        
    #     # Should succeed after retry
    #     handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
        
    #     # Should have made 2 calls
    #     assert mock_post.call_count == 2
    


class TestFsStoreCrawlRecordHandler:
    """Tests for FsStoreCrawlRecordHandler class."""
    
    def test_init(self):
        """Test handler initialization."""
        handler = FsStoreCrawlRecordHandler()
        assert handler.settings is not None
    
    def test_handle_success(self, sample_crawl_record):
        """Test successful record handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch the settings to use temp directory
            with patch.object(FsStoreCrawlRecordHandler, '__init__', lambda x: None):
                handler = FsStoreCrawlRecordHandler()
                handler.settings = type('Settings', (), {'output_directory': temp_dir})()
                
                handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
                
                # Check that directory was created
                expected_dir = Path(temp_dir) / "test_crawl_20240101_120000" / "records"
                assert expected_dir.exists()
                
                # Check that file was created
                files = list(expected_dir.glob("*.json"))
                assert len(files) == 1
                
                # Check file content
                with open(files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert data['url'] == sample_crawl_record.url
                    assert data['extracted_content'] == sample_crawl_record.extracted_content
    
    def test_handle_directory_creation(self, sample_crawl_record):
        """Test that directories are created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(FsStoreCrawlRecordHandler, '__init__', lambda x: None):
                handler = FsStoreCrawlRecordHandler()
                handler.settings = type('Settings', (), {'output_directory': temp_dir})()
                
                # Handle multiple records for same crawl
                handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
                
                record2 = CrawlRecord(
                    url="https://example2.com",
                    page_source="<html></html>",
                    extracted_content="Different content",
                    links=[],
                    scores={},
                    composite_score=0.0
                )
                handler.handle(record2, "test_crawl", "20240101_120000")
                
                # Should create same directory structure
                expected_dir = Path(temp_dir) / "test_crawl_20240101_120000" / "records"
                files = list(expected_dir.glob("*.json"))
                assert len(files) == 2
    
    def test_handle_filename_generation(self, sample_crawl_record):
        """Test that filenames are generated from URL hash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(FsStoreCrawlRecordHandler, '__init__', lambda x: None):
                handler = FsStoreCrawlRecordHandler()
                handler.settings = type('Settings', (), {'output_directory': temp_dir})()
                
                handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")
                
                # Check filename is MD5 hash
                expected_dir = Path(temp_dir) / "test_crawl_20240101_120000" / "records"
                files = list(expected_dir.glob("*.json"))
                
                import hashlib
                expected_hash = hashlib.md5(sample_crawl_record.url.encode()).hexdigest()
                expected_filename = f"{expected_hash}.json"
                
                assert files[0].name == expected_filename
    
    def test_handle_file_write_error(self, sample_crawl_record):
        """Test handling of file write errors."""
        # Use a non-existent directory that can't be created
        with patch.object(FsStoreCrawlRecordHandler, '__init__', lambda x: None):
            handler = FsStoreCrawlRecordHandler()
            handler.settings = type('Settings', (), {'output_directory': '/invalid/path'})()
            
            with pytest.raises(OSError, match="Failed to store crawl record"):
                handler.handle(sample_crawl_record, "test_crawl", "20240101_120000")