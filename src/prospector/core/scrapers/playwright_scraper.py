import logging
from typing import List
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from prospector.core.models import CrawlRecord
from prospector.core.settings import PlaywrightScraperSettings
from .scraper import Scraper


logger = logging.getLogger(__name__)

class PlaywrightScraper(Scraper):
    """Web scraper using Playwright for dynamic content extraction."""
    
    def __init__(self):
        """Initialize the Playwright scraper with settings."""
        self.settings = PlaywrightScraperSettings()
    
    def scrape(self, url: str) -> CrawlRecord:
        """
        Scrape a web page using Playwright.
        
        Extracts page source, text content, and links from the page.
        Handles both static and dynamic content.
        
        Args:
            url: URL to scrape
            
        Returns:
            CrawlRecord: Scraped content including source, text, and links
            
        Raises:
            Exception: If scraping fails due to network, timeout, or parsing errors
        """
        browser = None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    context = browser.new_context(
                        user_agent=self.settings.user_agent,
                    )
                    page = context.new_page()
                    
                    # Navigate to the page with timeout
                    page.goto(url, timeout=self.settings.timeout * 1000)
                    
                    # Wait for the page to load if JavaScript is enabled
                    if self.settings.javascript_enabled:
                        page.wait_for_load_state("networkidle")
                    
                    # Extract page source
                    page_source = page.content()
                    
                    # Extract text content
                    extracted_content = page.evaluate("""
                        () => {
                            // Remove script and style elements
                            const scripts = document.querySelectorAll('script, style');
                            scripts.forEach(el => el.remove());
                            
                            // Get text content
                            return document.body ? document.body.innerText : '';
                        }
                    """)
                    
                    # Extract links
                    links = self._extract_links(page, url)
                    
                    return CrawlRecord(
                        url=url,
                        page_source=page_source,
                        extracted_content=extracted_content,
                        links=links,
                        scores={},  # Will be populated by analyzers
                        composite_score=0.0  # Will be calculated later
                    )
                    
                finally:
                    # Always close browser, even on errors
                    if browser:
                        browser.close()
                
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout scraping URL {url}: {e}")
            raise Exception(f"Timeout scraping {url}")
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            raise Exception(f"Failed to scrape {url}: {str(e)}")
    
    def _extract_links(self, page, base_url: str) -> List[str]:
        """
        Extract and normalize links from the page.
        
        Args:
            page: Playwright page object
            base_url: Base URL for resolving relative links
            
        Returns:
            List[str]: List of absolute URLs found on the page
        """
        try:
            # Get all href attributes from anchor tags
            href_list = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => link.href).filter(href => href);
                }
            """)
            
            # Convert to absolute URLs and filter
            absolute_links = []
            for href in href_list:
                try:
                    absolute_url = urljoin(base_url, href)
                    # Basic URL validation
                    parsed = urlparse(absolute_url)
                    if parsed.scheme in ('http', 'https'):
                        absolute_links.append(absolute_url)
                except Exception as e:
                    logger.debug(f"Skipping invalid URL {href}: {e}")
                    continue
            
            return absolute_links
            
        except Exception as e:
            logger.warning(f"Error extracting links from {base_url}: {e}")
            return []
