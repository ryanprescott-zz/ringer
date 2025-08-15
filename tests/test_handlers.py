"""Tests for crawl record handlers."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from prospector.core.storage_handlers import (
    FsStoreHandler,
    DhStoreHandler,
)
from prospector.core import CrawlRecord


class TestDhStoreHandler:
    """Tests for DhStoreHandler class."""
    
    def test_init(self):
        """Test service handler initialization."""
        handler = DhStoreHandler()
        assert handler.settings is not None
        assert handler.session is not None
        assert handler.session.headers['Content-Type'] == 'application/json'
    
    @patch('prospector.core.storage_handlers.dh_store_handler.requests.Session.post')
    def test_store_record_success(self, mock_post, sample_crawl_record):
        """Test successful record handling via service."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_post.return_value = mock_response
        
        handler = DhStoreHandler()
        
        # Should not raise any exception
        handler.store_record(sample_crawl_record, "test_crawl_id")
        
        # Verify request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify URL and timeout
        assert call_args[0][0] == handler.settings.service_url
        assert call_args[1]['timeout'] == handler.settings.service_timeout_sec
        
        # Verify request payload structure
        request_data = call_args[1]['json']
        assert 'record' in request_data
        assert 'crawl_id' in request_data
        assert request_data['crawl_id'] == "test_crawl_id"
    
    @patch('prospector.core.storage_handlers.dh_store_handler.requests.Session.post')
    def test_store_record_http_error_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with HTTP error after all retries."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        handler = DhStoreHandler()
        
        # Should not raise exception, just log and discard
        handler.store_record(sample_crawl_record, "test_crawl_id")
        
        # Should have made multiple attempts (3 retries + 1 initial = 4 total)
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.storage_handlers.dh_store_handler.requests.Session.post')
    def test_store_record_timeout_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with timeout after all retries."""
        import requests
        
        # Mock timeout exception
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        handler = DhStoreHandler()
        
        # Should not raise exception, just log and discard
        handler.store_record(sample_crawl_record, "test_crawl_id")
        
        # Should have made multiple attempts
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.storage_handlers.dh_store_handler.requests.Session.post')
    def test_store_record_connection_error_after_retries(self, mock_post, sample_crawl_record):
        """Test handling with connection error after all retries."""
        import requests
        
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        handler = DhStoreHandler()
        
        # Should not raise exception, just log and discard
        handler.store_record(sample_crawl_record, "test_crawl_id")
        
        # Should have made multiple attempts
        assert mock_post.call_count >= 3
    
    @patch('prospector.core.storage_handlers.dh_store_handler.requests.Session.post')
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
        
        handler = DhStoreHandler()
        
        # Should succeed after retry
        handler.store_record(sample_crawl_record, "test_crawl_id")
        
        # Should have made 2 calls
        assert mock_post.call_count == 2
    


class TestFsStoreHandler:
    """Tests for FsStoreHandler class."""
    
    def test_init(self):
        """Test handler initialization."""
        handler = FsStoreHandler()
        assert handler.settings is not None
    
    def test_store_record_success(self, sample_crawl_record, sample_crawl_spec):
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
                handler.create_crawl(sample_crawl_spec)
                handler.store_record(sample_crawl_record, sample_crawl_spec.id)
                
                # Check that directory was created
                expected_dir = Path(temp_dir) / sample_crawl_spec.id / "records"
                assert expected_dir.exists()
                
                # Check that file was created
                files = list(expected_dir.glob("*.json"))
                assert len(files) == 1
                
                # Check file content
                with open(files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert data['url'] == sample_crawl_record.url
                    assert data['extracted_content'] == sample_crawl_record.extracted_content
    
    def test_store_record_directory_creation(self, sample_crawl_record, sample_crawl_spec):
        """Test that directories are created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(FsStoreHandler, '__init__', lambda x: None):
                handler = FsStoreHandler()
                handler.settings = type('Settings', (), {
                    'output_directory': temp_dir,
                    'record_directory': 'records'
                })()
                
                # Create crawl and handle multiple records for same crawl
                handler.create_crawl(sample_crawl_spec)
                handler.store_record(sample_crawl_record, sample_crawl_spec.id)
                
                record2 = CrawlRecord(
                    url="https://example2.com",
                    page_source="<html></html>",
                    extracted_content="Different content",
                    links=[],
                    scores={},
                    composite_score=0.0
                )
                handler.store_record(record2, sample_crawl_spec.id)
                
                # Should create same directory structure
                expected_dir = Path(temp_dir) / sample_crawl_spec.id / "records"
                files = list(expected_dir.glob("*.json"))
                assert len(files) == 2
    
    
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
                handler.store_record(sample_crawl_record, "test_crawl_id")
