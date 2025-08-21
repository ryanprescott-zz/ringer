import logging
from typing import List
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from ringer.core.models import CrawlRecord
from ringer.core.settings import PlaywrightScraperSettings
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
        logger.debug(f"Starting to scrape URL: {url}")
        browser = None
        
        try:
            with sync_playwright() as p:
                try:
                    browser = (
                        p.chromium.launch(
                            headless=True,
                            proxy={
                                "server": self.settings.proxy_server, 
                            }
                        )
                        if self.settings.proxy_server is not None
                        else p.chromium.launch(headless=True)
                    )
                    logger.debug(f"Launched browser for URL: {url}")
                except Exception as e:
                    logger.error(f"Failed to launch browser for URL {url}: {e}")
                    raise
                
                try:
                    context = browser.new_context(
                        user_agent=self.settings.user_agent,
                    )
                    page = context.new_page()
                    logger.debug(f"Created browser context and page for URL: {url}")
                    
                    # Navigate to the page with timeout
                    try:
                        page.goto(url, timeout=self.settings.timeout * 1000)
                        logger.debug(f"Successfully navigated to URL: {url}")
                    except Exception as e:
                        logger.error(f"Failed to navigate to URL {url}: {e}")
                        raise
                    
                    # Wait for the page to load if JavaScript is enabled
                    if self.settings.javascript_enabled:
                        try:
                            page.wait_for_load_state("networkidle")
                            logger.debug(f"Waited for network idle for URL: {url}")
                        except Exception as e:
                            logger.warning(f"Failed to wait for network idle for URL {url}: {e}")
                            # Continue processing even if network idle fails
                    
                    # Extract page source
                    try:
                        page_source = page.content()
                        logger.debug(f"Extracted page source for URL: {url} ({len(page_source)} chars)")
                    except Exception as e:
                        logger.error(f"Failed to extract page source for URL {url}: {e}")
                        raise
                    
                    # Extract text content
                    try:
                        extracted_content = page.evaluate("""
                            () => {
                                // Remove script and style elements
                                const scripts = document.querySelectorAll('script, style');
                                scripts.forEach(el => el.remove());
                                
                                // Get text content
                                return document.body ? document.body.innerText : '';
                            }
                        """)
                        logger.debug(f"Extracted text content for URL: {url} ({len(extracted_content)} chars)")
                    except Exception as e:
                        logger.error(f"Failed to extract text content for URL {url}: {e}")
                        # Use empty string if text extraction fails
                        extracted_content = ""
                    
                    # Extract links
                    try:
                        links = self._extract_links(page, url)
                        logger.debug(f"Extracted {len(links)} links from URL: {url}")
                    except Exception as e:
                        logger.error(f"Failed to extract links from URL {url}: {e}")
                        # Use empty list if link extraction fails
                        links = []
                    
                    crawl_record = CrawlRecord(
                        url=url,
                        page_source=page_source,
                        extracted_content=extracted_content,
                        links=links,
                        scores={},  # Will be populated by analyzers
                        composite_score=0.0  # Will be calculated later
                    )
                    
                    logger.debug(f"Successfully created crawl record for URL: {url}")
                    return crawl_record
                    
                finally:
                    # Always close browser, even on errors
                    if browser:
                        try:
                            browser.close()
                            logger.debug(f"Closed browser for URL: {url}")
                        except Exception as e:
                            logger.error(f"Failed to close browser for URL {url}: {e}")
                
        except PlaywrightTimeoutError as e:
            error_msg = f"Timeout scraping URL {url} after {self.settings.timeout}s: {e}"
            logger.error(error_msg)
            raise Exception(f"Timeout scraping {url}")
        except Exception as e:
            error_msg = f"Error scraping URL {url}: {e}"
            logger.error(error_msg)
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
