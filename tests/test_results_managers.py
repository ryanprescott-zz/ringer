"""Tests for crawl results managers."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from ringer.core.results_managers import (
    FsCrawlResultsManager,
    DhCrawlResultsManager,
    SQLiteCrawlResultsManager,
)
from ringer.core import CrawlRecord


class TestDhCrawlResultsManager:
    """Tests for DhCrawlResultsManager class."""
    
    def test_init(self):
        """Test service manager initialization."""
        manager = DhCrawlResultsManager()
        assert manager.settings is not None
        assert manager.session is not None
        assert manager.session.headers['Content-Type'] == 'application/json'
    
    @patch('ringer.core.results_managers.dh_crawl_results_manager.requests.Session.patch')
    def test_store_record_success(self, mock_patch, sample_crawl_record):
        """Test successful record handling via service."""
        from ringer.core.models import CrawlResultsId
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_patch.return_value = mock_response
        
        manager = DhCrawlResultsManager()
        results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
        
        # Should not raise any exception
        manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
        
        # Verify request was made
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        
        # Verify URL and timeout
        expected_url = f"{manager.settings.service_url}workbook/{results_id.collection_id}/bin/{results_id.data_id}"
        assert call_args[0][0] == expected_url
        assert call_args[1]['timeout'] == manager.settings.service_timeout_sec
        
        # Verify request payload structure
        request_data = call_args[1]['json']
        assert 'operation' in request_data
        assert 'operation_info' in request_data
        assert request_data['operation'] == "add_from_docs"
        assert 'documents' in request_data['operation_info']
        assert 'source' in request_data['operation_info']
        assert request_data['operation_info']['source'] == "test_crawl_id"
        assert len(request_data['operation_info']['documents']) == 1
    
    @patch('ringer.core.results_managers.dh_crawl_results_manager.requests.Session.patch')
    def test_store_record_http_error_after_retries(self, mock_patch, sample_crawl_record):
        """Test handling with HTTP error after all retries."""
        from ringer.core.models import CrawlResultsId
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_patch.return_value = mock_response
        
        manager = DhCrawlResultsManager()
        results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
        
        # Should not raise exception, just log and discard
        manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
        
        # Should have made multiple attempts (3 retries + 1 initial = 4 total)
        assert mock_patch.call_count >= 3
    
    @patch('ringer.core.results_managers.dh_crawl_results_manager.requests.Session.patch')
    def test_store_record_timeout_after_retries(self, mock_patch, sample_crawl_record):
        """Test handling with timeout after all retries."""
        from ringer.core.models import CrawlResultsId
        import requests
        
        # Mock timeout exception
        mock_patch.side_effect = requests.exceptions.Timeout("Request timeout")
        
        manager = DhCrawlResultsManager()
        results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
        
        # Should not raise exception, just log and discard
        manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
        
        # Should have made multiple attempts
        assert mock_patch.call_count >= 3
    
    @patch('ringer.core.results_managers.dh_crawl_results_manager.requests.Session.patch')
    def test_store_record_connection_error_after_retries(self, mock_patch, sample_crawl_record):
        """Test handling with connection error after all retries."""
        from ringer.core.models import CrawlResultsId
        import requests
        
        # Mock connection error
        mock_patch.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        manager = DhCrawlResultsManager()
        results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
        
        # Should not raise exception, just log and discard
        manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
        
        # Should have made multiple attempts
        assert mock_patch.call_count >= 3
    
    @patch('ringer.core.results_managers.dh_crawl_results_manager.requests.Session.patch')
    def test_store_record_success_after_retry(self, mock_patch, sample_crawl_record):
        """Test successful handling after initial failures."""
        from ringer.core.models import CrawlResultsId
        # Mock first call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Service Unavailable"
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.text = "Success"
        
        mock_patch.side_effect = [mock_response_fail, mock_response_success]
        
        manager = DhCrawlResultsManager()
        results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
        
        # Should succeed after retry
        manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
        
        # Should have made 2 calls
        assert mock_patch.call_count == 2
    


class TestFsCrawlResultsManager:
    """Tests for FsCrawlResultsManager class."""
    
    def test_init(self):
        """Test manager initialization."""
        manager = FsCrawlResultsManager()
        assert manager.settings is not None
    
    def test_store_record_success(self, sample_crawl_record, sample_crawl_spec):
        """Test successful record handling."""
        from ringer.core.models import CrawlResultsId
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch the settings to use temp directory
            with patch.object(FsCrawlResultsManager, '__init__', lambda x: None):
                manager = FsCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'crawl_data_dir': temp_dir
                })()
                manager.base_dir = Path(temp_dir)
                
                # First create the crawl and get results ID
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
                
                # Check that directory structure was created correctly
                crawl_dir = Path(temp_dir) / results_id.collection_id / results_id.data_id
                assert crawl_dir.exists()
                
                # Check that crawl spec and results ID files were created
                spec_file = crawl_dir / "crawl_spec.json"
                results_id_file = crawl_dir / "results_id.json"
                assert spec_file.exists()
                assert results_id_file.exists()
                
                # Check that records directory was created
                records_dir = crawl_dir / "records"
                assert records_dir.exists()

                # Find the record file
                record_files = list(records_dir.glob("*.json"))
                assert len(record_files) == 1
                
                # Check file content
                with open(record_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert data['url'] == sample_crawl_record.url
                    assert data['extracted_content'] == sample_crawl_record.extracted_content
    
    def test_store_record_directory_creation(self, sample_crawl_record, sample_crawl_spec):
        """Test that directories are created properly."""
        from ringer.core.models import CrawlResultsId
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(FsCrawlResultsManager, '__init__', lambda x: None):
                manager = FsCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'crawl_data_dir': temp_dir
                })()
                manager.base_dir = Path(temp_dir)
                
                # Create crawl and handle multiple records for same crawl
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
                
                record2 = CrawlRecord(
                    url="https://example2.com",
                    page_source="<html></html>",
                    extracted_content="Different content",
                    links=[],
                    scores={},
                    composite_score=0.0
                )
                manager.store_record(record2, results_id, "test_crawl_id")
                
                # Check that directory structure was created correctly
                crawl_dir = Path(temp_dir) / results_id.collection_id / results_id.data_id
                assert crawl_dir.exists()
                
                # Check that crawl spec and results ID files exist
                spec_file = crawl_dir / "crawl_spec.json"
                results_id_file = crawl_dir / "results_id.json"
                assert spec_file.exists()
                assert results_id_file.exists()
                
                # Check records directory and files
                records_dir = crawl_dir / "records"
                assert records_dir.exists(), f"Records directory not found in {crawl_dir}"
                record_files = list(records_dir.glob("*.json"))
                # Should have 2 record files
                assert len(record_files) == 2

    
    def test_store_record_file_write_error(self, sample_crawl_record):
        """Test handling of file write errors."""
        from ringer.core.models import CrawlResultsId
        # Use a non-existent directory that can't be created
        with patch.object(FsCrawlResultsManager, '__init__', lambda x: None):
            manager = FsCrawlResultsManager()
            manager.settings = type('Settings', (), {
                'crawl_data_dir': '/invalid/path'
            })()
            manager.base_dir = Path('/invalid/path')
            
            results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
            with pytest.raises(Exception):
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")


class TestSQLiteCrawlResultsManager:
    """Tests for SQLiteCrawlResultsManager class."""
    
    def test_init(self):
        """Test SQLite manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                assert manager.settings is not None
                assert manager.engine is not None
                assert manager.SessionLocal is not None
                assert db_path.exists()
    
    def test_create_crawl_success(self, sample_crawl_spec):
        """Test successful crawl creation."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base, CrawlSpecTable
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                
                # Verify crawl was created in database
                session = manager.SessionLocal()
                try:
                    crawl_record = session.query(CrawlSpecTable).filter_by(id=sample_crawl_spec.id).first()
                    assert crawl_record is not None
                    assert crawl_record.name == sample_crawl_spec.name
                    assert crawl_record.collection_id == results_id.collection_id
                    assert crawl_record.data_id == results_id.data_id
                    assert crawl_record.seeds == sample_crawl_spec.seeds
                    assert crawl_record.worker_count == sample_crawl_spec.worker_count
                finally:
                    session.close()
    
    def test_create_crawl_duplicate(self, sample_crawl_spec):
        """Test creating duplicate crawl doesn't raise error but logs warning."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base, CrawlSpecTable
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl twice
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.create_crawl(sample_crawl_spec, results_id)  # Should not raise error
                
                # Verify only one record exists
                session = manager.SessionLocal()
                try:
                    count = session.query(CrawlSpecTable).filter_by(id=sample_crawl_spec.id).count()
                    assert count == 1
                finally:
                    session.close()
    
    def test_store_record_success(self, sample_crawl_record, sample_crawl_spec):
        """Test successful record storage."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base, CrawlRecordTable
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl and store record
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
                
                # Verify record was stored
                session = manager.SessionLocal()
                try:
                    record = session.query(CrawlRecordTable).filter_by(id=sample_crawl_record.id).first()
                    assert record is not None
                    assert record.url == sample_crawl_record.url
                    assert record.extracted_content == sample_crawl_record.extracted_content
                    assert record.crawl_id == "test_crawl_id"
                    assert record.composite_score == sample_crawl_record.composite_score
                finally:
                    session.close()
    
    def test_store_record_update_existing(self, sample_crawl_record, sample_crawl_spec):
        """Test updating existing record."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base, CrawlRecordTable
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl and store record
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
                
                # Update the record with new content
                updated_record = CrawlRecord(
                    url=sample_crawl_record.url,  # Same URL to get same ID
                    page_source="<html><body>Updated content</body></html>",
                    extracted_content="Updated content",
                    links=["https://updated.com"],
                    scores={"KeywordScoreAnalyzer": 0.9},
                    composite_score=0.9
                )
                manager.store_record(updated_record, results_id, "test_crawl_id")
                
                # Verify record was updated, not duplicated
                session = manager.SessionLocal()
                try:
                    records = session.query(CrawlRecordTable).filter_by(id=sample_crawl_record.id).all()
                    assert len(records) == 1
                    record = records[0]
                    assert record.extracted_content == "Updated content"
                    assert record.composite_score == 0.9
                finally:
                    session.close()
    
    def test_store_record_crawl_not_found(self, sample_crawl_record):
        """Test storing record when crawl doesn't exist."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Try to store record without creating crawl first
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                
                with pytest.raises(ValueError, match="Crawl spec not found"):
                    manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
    
    def test_delete_crawl_success(self, sample_crawl_record, sample_crawl_spec):
        """Test successful crawl deletion."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base, CrawlSpecTable, CrawlRecordTable
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl and store record
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
                
                # Verify data exists
                session = manager.SessionLocal()
                try:
                    spec_count = session.query(CrawlSpecTable).filter_by(
                        collection_id=results_id.collection_id,
                        data_id=results_id.data_id
                    ).count()
                    record_count = session.query(CrawlRecordTable).count()
                    assert spec_count == 1
                    assert record_count == 1
                finally:
                    session.close()
                
                # Delete crawl
                manager.delete_crawl(results_id)
                
                # Verify data was deleted (cascade should delete records too)
                session = manager.SessionLocal()
                try:
                    spec_count = session.query(CrawlSpecTable).filter_by(
                        collection_id=results_id.collection_id,
                        data_id=results_id.data_id
                    ).count()
                    record_count = session.query(CrawlRecordTable).count()
                    assert spec_count == 0
                    assert record_count == 0
                finally:
                    session.close()
    
    def test_delete_crawl_not_found(self):
        """Test deleting non-existent crawl."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Try to delete non-existent crawl (should not raise error)
                results_id = CrawlResultsId(collection_id="nonexistent", data_id="crawl")
                manager.delete_crawl(results_id)  # Should complete without error
    
    def test_get_crawl_records_success(self, sample_crawl_record, sample_crawl_spec):
        """Test retrieving crawl records."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl and store records
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")
                
                # Create a second record
                record2 = CrawlRecord(
                    url="https://example2.com",
                    page_source="<html></html>",
                    extracted_content="Different content",
                    links=[],
                    scores={"KeywordScoreAnalyzer": 0.5},
                    composite_score=0.5
                )
                manager.store_record(record2, results_id, "test_crawl_id")
                
                # Retrieve records
                records = manager.get_crawl_records(results_id)
                assert len(records) == 2
                
                # Check record content
                urls = [record.url for record in records]
                assert sample_crawl_record.url in urls
                assert record2.url in urls
    
    def test_get_crawl_records_with_limit(self, sample_crawl_record, sample_crawl_spec):
        """Test retrieving crawl records with limit."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl and store multiple records
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                
                # Store 3 records
                for i in range(3):
                    record = CrawlRecord(
                        url=f"https://example{i}.com",
                        page_source="<html></html>",
                        extracted_content=f"Content {i}",
                        links=[],
                        scores={"KeywordScoreAnalyzer": 0.5},
                        composite_score=0.5
                    )
                    manager.store_record(record, results_id, "test_crawl_id")
                
                # Retrieve with limit
                records = manager.get_crawl_records(results_id, limit=2)
                assert len(records) == 2
    
    def test_get_crawl_records_not_found(self):
        """Test retrieving records for non-existent crawl."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Try to get records for non-existent crawl
                results_id = CrawlResultsId(collection_id="nonexistent", data_id="crawl")
                records = manager.get_crawl_records(results_id)
                assert records == []
    
    def test_get_crawl_stats_success(self, sample_crawl_record, sample_crawl_spec):
        """Test getting crawl statistics."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl and store records with different scores
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                manager.store_record(sample_crawl_record, results_id, "test_crawl_id")  # score 0.8
                
                # Create records with different scores
                record2 = CrawlRecord(
                    url="https://example2.com",
                    page_source="<html></html>",
                    extracted_content="Different content",
                    links=[],
                    scores={"KeywordScoreAnalyzer": 0.5},
                    composite_score=0.5
                )
                manager.store_record(record2, results_id, "test_crawl_id")
                
                record3 = CrawlRecord(
                    url="https://example3.com",
                    page_source="<html></html>",
                    extracted_content="More content",
                    links=[],
                    scores={"KeywordScoreAnalyzer": 1.0},
                    composite_score=1.0
                )
                manager.store_record(record3, results_id, "test_crawl_id")
                
                # Get statistics
                stats = manager.get_crawl_stats(results_id)
                assert stats["total_records"] == 3
                assert abs(stats["avg_score"] - 0.7666666666666667) < 0.001  # (0.8 + 0.5 + 1.0) / 3
                assert stats["max_score"] == 1.0
                assert stats["min_score"] == 0.5
    
    def test_get_crawl_stats_empty(self, sample_crawl_spec):
        """Test getting statistics for crawl with no records."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Create crawl but don't store any records
                results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
                manager.create_crawl(sample_crawl_spec, results_id)
                
                # Get statistics
                stats = manager.get_crawl_stats(results_id)
                assert stats["total_records"] == 0
                assert stats["avg_score"] == 0.0
                assert stats["max_score"] == 0.0
                assert stats["min_score"] == 0.0
    
    def test_get_crawl_stats_not_found(self):
        """Test getting statistics for non-existent crawl."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager = SQLiteCrawlResultsManager()
                manager.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager.engine)
                manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                
                # Try to get stats for non-existent crawl
                results_id = CrawlResultsId(collection_id="nonexistent", data_id="crawl")
                stats = manager.get_crawl_stats(results_id)
                assert stats["total_records"] == 0
                assert stats["avg_score"] == 0.0
                assert stats["max_score"] == 0.0
                assert stats["min_score"] == 0.0
    
    def test_database_persistence(self, sample_crawl_record, sample_crawl_spec):
        """Test that data persists across manager instances."""
        from ringer.core.models import CrawlResultsId
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
            
            # Create first manager instance and store data
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager1 = SQLiteCrawlResultsManager()
                manager1.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager1.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager1.engine)
                manager1.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager1.engine)
                
                # Store data
                manager1.create_crawl(sample_crawl_spec, results_id)
                manager1.store_record(sample_crawl_record, results_id, "test_crawl_id")
                
                # Cleanup first manager
                manager1.engine.dispose()
            
            # Create second manager instance and verify data persists
            with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                manager2 = SQLiteCrawlResultsManager()
                manager2.settings = type('Settings', (), {
                    'database_path': str(db_path),
                    'echo_sql': False,
                    'pool_size': 5,
                    'max_overflow': 10
                })()
                
                # Initialize the actual components
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                
                database_url = f"sqlite:///{db_path}"
                manager2.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                Base.metadata.create_all(manager2.engine)
                manager2.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager2.engine)
                
                # Verify data persists
                records = manager2.get_crawl_records(results_id)
                assert len(records) == 1
                assert records[0].url == sample_crawl_record.url
                assert records[0].extracted_content == sample_crawl_record.extracted_content
                
                stats = manager2.get_crawl_stats(results_id)
                assert stats["total_records"] == 1
                assert stats["avg_score"] == sample_crawl_record.composite_score
                
                # Cleanup second manager
                manager2.engine.dispose()
    
    def test_concurrent_access(self, sample_crawl_record, sample_crawl_spec):
        """Test concurrent access to the database."""
        from ringer.core.models import CrawlResultsId
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
            
            def create_manager():
                with patch.object(SQLiteCrawlResultsManager, '__init__', lambda x: None):
                    manager = SQLiteCrawlResultsManager()
                    manager.settings = type('Settings', (), {
                        'database_path': str(db_path),
                        'echo_sql': False,
                        'pool_size': 5,
                        'max_overflow': 10
                    })()
                    
                    # Initialize the actual components
                    from sqlalchemy import create_engine
                    from sqlalchemy.orm import sessionmaker
                    from ringer.core.results_managers.sqlite_crawl_results_manager import Base
                    
                    database_url = f"sqlite:///{db_path}"
                    manager.engine = create_engine(database_url, connect_args={"check_same_thread": False})
                    Base.metadata.create_all(manager.engine)
                    manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager.engine)
                    
                    return manager
            
            # Create initial manager and crawl
            manager = create_manager()
            manager.create_crawl(sample_crawl_spec, results_id)
            
            # Function to store records concurrently
            def store_records(thread_id):
                thread_manager = create_manager()
                for i in range(3):
                    record = CrawlRecord(
                        url=f"https://thread{thread_id}-example{i}.com",
                        page_source="<html></html>",
                        extracted_content=f"Thread {thread_id} Content {i}",
                        links=[],
                        scores={"KeywordScoreAnalyzer": 0.5},
                        composite_score=0.5
                    )
                    thread_manager.store_record(record, results_id, f"crawl_thread_{thread_id}")
                    time.sleep(0.01)  # Small delay to encourage interleaving
                thread_manager.engine.dispose()
            
            # Start multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=store_records, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all records were stored
            records = manager.get_crawl_records(results_id)
            assert len(records) == 9  # 3 threads * 3 records each
            
            # Verify unique URLs
            urls = [record.url for record in records]
            assert len(set(urls)) == 9  # All URLs should be unique
            
            manager.engine.dispose()
