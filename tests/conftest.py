"""Pytest configuration and fixtures."""

import pytest
import threading
import time
import atexit
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from prospector.main import app
from prospector.core import (
    CrawlSpec,
    CrawlState,
    SearchEngineSeed,
    SearchEngineEnum,
    AnalyzerSpec,
    WeightedKeyword,
    CrawlRecord,
    Prospector,
    KeywordScoreAnalyzer,
    RunStateEnum,
)
from prospector.core.models import KeywordScoringSpec


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
    from prospector.core.models import KeywordScoringSpec
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
    from prospector.core.models import KeywordScoringSpec
    spec = KeywordScoringSpec(
        name="KeywordScoreAnalyzer",
        composite_weight=1.0,
        keywords=sample_weighted_keywords
    )
    analyzer = KeywordScoreAnalyzer(spec)
    return analyzer


@pytest.fixture
def prospector():
    """Prospector instance for testing with temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Patch the FsCrawlResultsManager settings to use temp directory
        with patch('prospector.core.results_management.fs_crawl_results_manager.FsCrawlResultsManagerSettings') as mock_settings:
            mock_settings.return_value.crawl_data_dir = temp_dir
            prospector_instance = Prospector()
            yield prospector_instance
            # Cleanup prospector after test
            try:
                prospector_instance.shutdown()
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
def mock_handler():
    """Mock crawl record handler for testing."""
    handler = Mock()
    return handler

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
def sample_crawl_state(sample_crawl_spec):
    """Create a sample CrawlState for testing."""
    from prospector.core.models import RunState, RunStateEnum
    from prospector.core.state_managers.memory_crawl_state_manager import MemoryCrawlStateManager
    manager = MemoryCrawlStateManager()
    crawl_state = CrawlState(sample_crawl_spec, manager)
    return crawl_state
