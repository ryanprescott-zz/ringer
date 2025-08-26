"""Pytest configuration and fixtures."""

import pytest
import threading
import time
import atexit
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from ringer.main import app
from ringer.core import (
    CrawlSpec,
    CrawlState,
    SearchEngineSeed,
    SearchEngineEnum,
    AnalyzerSpec,
    WeightedKeyword,
    CrawlRecord,
    Ringer,
    KeywordScoreAnalyzer,
    RunStateEnum,
)
from ringer.core.models import KeywordScoringSpec


# Global cleanup registry
_cleanup_functions = []


def register_cleanup(func):
    """Register a cleanup function to be called at exit."""
    _cleanup_functions.append(func)


def cleanup_all():
    """Run all registered cleanup functions."""
    for func in _cleanup_functions:
        try:
            func()
        except Exception:
            pass  # Ignore cleanup errors


# Register cleanup to run at exit
atexit.register(cleanup_all)


# Add pytest configuration for better cleanup
def pytest_configure(config):
    """Configure pytest for proper cleanup."""
    pass


def pytest_unconfigure(config):
    """Cleanup after pytest run."""
    # Run all cleanup functions
    cleanup_all()
    
    # Give threads time to cleanup
    time.sleep(0.1)
    
    # Force cleanup of any remaining threads
    main_thread = threading.main_thread()
    for thread in threading.enumerate():
        if thread != main_thread and thread.is_alive():
            if hasattr(thread, '_target') and thread._target:
                thread.daemon = True


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically cleanup after each test."""
    yield
    # Small delay to allow async cleanup
    time.sleep(0.01)


@pytest.fixture
def sample_weighted_keywords():
    """Sample weighted keywords for testing."""
    return [
        WeightedKeyword(keyword="python", weight=1.0),
        WeightedKeyword(keyword="programming", weight=0.8),
        WeightedKeyword(keyword="code", weight=0.6)
    ]


@pytest.fixture
def sample_analyzer_spec(sample_weighted_keywords) -> KeywordScoringSpec:
    """Sample analyzer specification for testing."""
    from ringer.core.models import KeywordScoringSpec
    return KeywordScoringSpec(
        name="KeywordScoreAnalyzer",
        composite_weight=1.0,
        keywords=sample_weighted_keywords
    )


@pytest.fixture
def sample_crawl_spec(sample_analyzer_spec):
    """Sample crawl specification for testing."""
    return CrawlSpec(
        name="test_crawl",
        seeds=["https://example.com"],
        analyzer_specs=[sample_analyzer_spec],
        worker_count=1,
        domain_blacklist=["spam.com"]
    )

@pytest.fixture
def sample_crawl_spec_dict(sample_crawl_spec):
    return {
        "name": "test_crawl",
        "seeds": ["https://example.com"],
        "analyzer_specs": [
        {
            "name": "KeywordScoreAnalyzer",
            "composite_weight": 1.0,
            "keywords": [
            {"keyword": "python", "weight": 1.0},
            {"keyword": "programming", "weight": 0.8},
            {"keyword": "code", "weight": 0.6}
            ]
        }
        ],
        "worker_count": 1,
        "domain_blacklist": ["spam.com"]
    }

@pytest.fixture
def sample_crawl_record():
    """Sample crawl record for testing."""
    return CrawlRecord(
        url="https://example.com",
        page_source="<html><body>Test content</body></html>",
        extracted_content="Test content about python programming",
        links=["https://example.com/page1", "https://example.com/page2"],
        scores={"KeywordScoreAnalyzer": 0.8},
        composite_score=0.8
    )


@pytest.fixture
def keyword_analyzer(sample_weighted_keywords):
    """Sample keyword analyzer for testing."""
    from ringer.core.models import KeywordScoringSpec
    spec = KeywordScoringSpec(
        name="KeywordScoreAnalyzer",
        composite_weight=1.0,
        keywords=sample_weighted_keywords
    )
    analyzer = KeywordScoreAnalyzer(spec)
    return analyzer


@pytest.fixture
def ringer():
    """Ringer instance for testing with temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Patch the FsCrawlResultsManager settings to use temp directory
        with patch('ringer.core.results_managers.fs_crawl_results_manager.FsCrawlResultsManagerSettings') as mock_settings:
            mock_settings.return_value.crawl_data_dir = temp_dir
            # Also patch the results manager to return a consistent storage ID
            with patch('ringer.core.results_managers.fs_crawl_results_manager.uuid.uuid4') as mock_uuid:
                mock_uuid.return_value = Mock()
                mock_uuid.return_value.__str__ = Mock(return_value="test-storage-id-123")
                ringer_instance = Ringer()
                yield ringer_instance
                # Cleanup ringer after test
                try:
                    ringer_instance.shutdown()
                except Exception:
                    pass  # Ignore shutdown errors in tests


@pytest.fixture
def mock_scraper():
    """Mock scraper for testing."""
    scraper = Mock()
    scraper.scrape.return_value = CrawlRecord(
        url="https://example.com",
        page_source="<html><body>Mock content</body></html>",
        extracted_content="Mock content with python programming",
        links=["https://example.com/link1"],
        scores={},
        composite_score=0.0
    )
    return scraper


@pytest.fixture
def mock_results_manager():
    """Mock crawl results_manager for testing."""
    results_manager = Mock()
    results_manager.create_crawl.return_value = "test-storage-id-123"
    return results_manager

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_ringer():
    """Create a mock Ringer instance."""
    ringer = Mock(spec=Ringer)
    ringer.crawls = {}
    return ringer


@pytest.fixture
def sample_crawl_state(sample_crawl_spec):
    """Create a sample CrawlState for testing."""
    from ringer.core.models import RunState, RunStateEnum, CrawlResultsId
    from ringer.core.state_managers.memory_crawl_state_manager import MemoryCrawlStateManager
    manager = MemoryCrawlStateManager()
    results_id = CrawlResultsId(collection_id="test_collection", data_id="test_data")
    crawl_state = CrawlState(sample_crawl_spec, results_id, manager, "test_crawl_id")
    return crawl_state
