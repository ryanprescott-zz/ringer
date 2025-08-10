"""Tests for web scrapers."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from prospector.core import (
    PlaywrightScraper,
    CrawlRecord,
)


class TestPlaywrightScraper:
    """Tests for PlaywrightScraper class."""
    
    def test_init(self):
        """Test scraper initialization."""
        scraper = PlaywrightScraper()
        assert scraper.settings is not None
    
    @patch('prospector.core.scrapers.playwright_scraper.sync_playwright')
    def test_scrape_success(self, mock_playwright):
        """Test successful page scraping."""
        # Mock Playwright components
        mock_page = Mock()
        mock_page.content.return_value = "<html><body>Test content</body></html>"
        mock_page.evaluate.return_value = "Test content"
        
        mock_context = Mock()
        mock_context.new_page.return_value = mock_page
        
        mock_browser = Mock()
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        
        scraper = PlaywrightScraper()
        
        # Mock the _extract_links method
        with patch.object(scraper, '_extract_links', return_value=["https://example.com/link"]):
            result = scraper.scrape("https://example.com")
        
        assert isinstance(result, CrawlRecord)
        assert result.url == "https://example.com"
        assert result.page_source == "<html><body>Test content</body></html>"
        assert result.extracted_content == "Test content"
        assert result.links == ["https://example.com/link"]
        
        # Verify Playwright calls
        mock_page.goto.assert_called_once_with("https://example.com", timeout=30000)
        mock_browser.close.assert_called_once()
    
    @patch('prospector.core.scrapers.playwright_scraper.sync_playwright')
    def test_scrape_timeout(self, mock_playwright):
        """Test scraping with timeout error."""
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        
        mock_page = Mock()
        mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout")
        
        mock_context = Mock()
        mock_context.new_page.return_value = mock_page
        
        mock_browser = Mock()
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        
        scraper = PlaywrightScraper()
        
        with pytest.raises(Exception, match="Timeout scraping"):
            scraper.scrape("https://example.com")
        
        mock_browser.close.assert_called_once()
    
    @patch('prospector.core.scrapers.playwright_scraper.sync_playwright')
    def test_scrape_general_error(self, mock_playwright):
        """Test scraping with general error."""
        mock_page = Mock()
        mock_page.goto.side_effect = Exception("Network error")
        
        mock_context = Mock()
        mock_context.new_page.return_value = mock_page
        
        mock_browser = Mock()
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = Mock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        
        scraper = PlaywrightScraper()
        
        with pytest.raises(Exception, match="Failed to scrape"):
            scraper.scrape("https://example.com")
    
    def test_extract_links_valid_urls(self):
        """Test extracting valid links from page."""
        mock_page = Mock()
        mock_page.evaluate.return_value = [
            "https://example.com/page1",
            "https://example.com/page2",
            "/relative/path",
            "mailto:test@example.com",  # Should be filtered out
            "javascript:void(0)"  # Should be filtered out
        ]
        
        scraper = PlaywrightScraper()
        links = scraper._extract_links(mock_page, "https://example.com")
        
        # Should include absolute URLs and convert relative paths
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://example.com/relative/path" in links
        
        # Should exclude non-HTTP URLs
        assert "mailto:test@example.com" not in links
        assert "javascript:void(0)" not in links
    
    def test_extract_links_error_handling(self):
        """Test link extraction error handling."""
        mock_page = Mock()
        mock_page.evaluate.side_effect = Exception("JavaScript error")
        
        scraper = PlaywrightScraper()
        links = scraper._extract_links(mock_page, "https://example.com")
        
        # Should return empty list on error
        assert links == []