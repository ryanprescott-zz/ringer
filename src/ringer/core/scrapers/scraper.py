"""Scraper base class for web scraping functionality."""

from abc import ABC, abstractmethod

from ringer.core.models import CrawlRecord


class Scraper(ABC):
    """Abstract base class for web scrapers."""
    
    @abstractmethod
    def scrape(self, url: str) -> CrawlRecord:
        """
        Scrape content from a web page.
        
        Args:
            url: URL to scrape
            
        Returns:
            CrawlRecord: Scraped content and metadata
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError
