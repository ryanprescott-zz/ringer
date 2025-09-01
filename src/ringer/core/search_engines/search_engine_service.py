"""Search engine service for generating seed URLs."""

import asyncio
import base64
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Set
from urllib.parse import urljoin, urlparse, unquote, parse_qs

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from ..models import SearchEngineSeed
from ..settings import SearchEngineSettings

# Define SearchEngineEnum if not available in models
try:
    from ..models import SearchEngineEnum
except ImportError:
    from enum import Enum
    class SearchEngineEnum(str, Enum):
        GOOGLE = "google"
        BING = "bing"
        DUCKDUCKGO = "duckduckgo"


logger = logging.getLogger(__name__)


class SearchEngineParser(ABC):
    """Abstract base class for search engine result parsers."""
    
    @abstractmethod
    def parse_results(self, html_content: str, result_count: int) -> List[str]:
        """
        Parse search results from HTML content.
        
        Args:
            html_content: HTML content from search engine
            result_count: Maximum number of results to extract
            
        Returns:
            List of URLs extracted from search results
        """
        pass


class GoogleParser(SearchEngineParser):
    """Parser for Google search results."""
    
    def parse_results(self, html_content: str, result_count: int) -> List[str]:
        """Parse Google search results."""
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        
        logger.debug(f"Parsing Google results, HTML length: {len(html_content)}")
        
        # Save HTML for debugging if no results found
        if logger.isEnabledFor(logging.DEBUG):
            with open('/tmp/google_debug.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug("Saved Google HTML to /tmp/google_debug.html for debugging")
        
        # Try multiple selectors for Google results as they change frequently
        selectors = [
            'div.g a[href]',  # Standard organic results
            'div[data-ved] a[href]',  # Alternative structure  
            'h3 a[href]',  # Header links
            'a[href^="/url?q="]',  # URL redirect links
            'div.yuRUbf a[href]',  # Updated Google structure
            'div.tF2Cxc a[href]',  # Another common structure
            'a[jsname][href]',  # Links with jsname attribute
        ]
        
        for i, selector in enumerate(selectors):
            links = soup.select(selector)
            logger.debug(f"Selector {i+1} '{selector}' found {len(links)} links")
            
            for link in links:
                href = link.get('href', '')
                logger.debug(f"Processing href: {href[:100]}...")
                
                # Handle Google's URL redirect format
                if href.startswith('/url?q='):
                    # Extract the actual URL from Google's redirect
                    url_match = re.search(r'/url\?q=([^&]+)', href)
                    if url_match:
                        url = unquote(url_match.group(1))
                        logger.debug(f"Extracted URL from redirect: {url}")
                        if self._is_valid_url(url):
                            urls.append(url)
                            logger.debug(f"Added valid URL: {url}")
                elif href.startswith('http') and not any(domain in href for domain in ['google.com', 'googleusercontent.com', 'gstatic.com']):
                    # Direct links that aren't Google's own
                    if self._is_valid_url(href):
                        urls.append(href)
                        logger.debug(f"Added direct URL: {href}")
                
                if len(urls) >= result_count:
                    break
            
            if len(urls) >= result_count:
                break
        
        logger.info(f"Google parser found {len(urls)} URLs before deduplication")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"Google parser returning {len(unique_urls)} unique URLs")
        return unique_urls[:result_count]
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid HTTP/HTTPS."""
        try:
            parsed = urlparse(url)
            return (parsed.scheme in ('http', 'https') and 
                   parsed.netloc and 
                   not parsed.netloc.endswith('.google.com') and
                   not parsed.netloc.endswith('.googleusercontent.com'))
        except Exception:
            return False


class BingParser(SearchEngineParser):
    """Parser for Bing search results."""
    
    def parse_results(self, html_content: str, result_count: int) -> List[str]:
        """Parse Bing search results."""
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        
        logger.debug(f"Parsing Bing results, HTML length: {len(html_content)}")
        
        # Save HTML for debugging if no results found
        if logger.isEnabledFor(logging.DEBUG):
            with open('/tmp/bing_debug_parser.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug("Saved Bing HTML to /tmp/bing_debug_parser.html for debugging")
        
        # Try multiple selectors for Bing results as they change frequently
        selectors = [
            'li.b_algo a[href]',  # Standard organic results
            'ol.b_algo li a[href]',  # Results in ordered list
            '.b_algo a[href]',  # Any element with b_algo class
            'h2 a[href]',  # Header links
            'h3 a[href]',  # Another common header structure
            '[data-h] a[href]',  # Elements with data-h attribute containing links
            '.b_title a[href]',  # Title links
            '.b_algoheader a[href]',  # Algorithm header links
            '.b_attribution a[href]',  # Attribution links (but we'll filter these)
        ]
        
        for i, selector in enumerate(selectors):
            links = soup.select(selector)
            logger.debug(f"Selector {i+1} '{selector}' found {len(links)} links")
            
            for link in links:
                href = link.get('href', '')
                logger.debug(f"Processing href: {href[:100]}...")
                
                # Handle Bing redirect URLs
                actual_url = self._extract_actual_url(href)
                if actual_url and self._is_valid_url(actual_url):
                    urls.append(actual_url)
                    logger.debug(f"Added valid URL: {actual_url}")
                
                if len(urls) >= result_count:
                    break
            
            if len(urls) >= result_count:
                break
        
        logger.info(f"Bing parser found {len(urls)} URLs before deduplication")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"Bing parser returning {len(unique_urls)} unique URLs")
        return unique_urls[:result_count]
    
    def _extract_actual_url(self, href: str) -> str:
        """Extract the actual URL from Bing's redirect URL."""
        if not href:
            return None
            
        # Handle Bing redirect URLs like:
        # https://www.bing.com/ck/a?!&&p=...&u=a1aHR0cHM6Ly9lbi53aWtpcGVkaWEub3JnL3dpa2kvRG9n&ntb=1
        if 'bing.com/ck/a' in href and 'u=' in href:
            try:
                # Parse the URL to get query parameters
                parsed = urlparse(href)
                query_params = parse_qs(parsed.query)
                
                # Get the 'u' parameter which contains the base64-encoded actual URL
                if 'u' in query_params and query_params['u']:
                    encoded_url = query_params['u'][0]
                    
                    # The URL is base64 encoded with a prefix (usually 'a1')
                    # Remove the prefix and decode
                    if encoded_url.startswith('a1'):
                        encoded_url = encoded_url[2:]  # Remove 'a1' prefix
                        try:
                            # Add padding if necessary
                            missing_padding = len(encoded_url) % 4
                            if missing_padding:
                                encoded_url += '=' * (4 - missing_padding)
                            
                            actual_url = base64.b64decode(encoded_url).decode('utf-8')
                            logger.debug(f"Decoded Bing redirect URL: {href[:50]}... -> {actual_url}")
                            return actual_url
                        except Exception as e:
                            logger.debug(f"Failed to decode base64 URL: {e}")
                            
            except Exception as e:
                logger.debug(f"Failed to parse Bing redirect URL: {e}")
        
        # If it's not a redirect URL or we can't decode it, return as-is
        return href
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid HTTP/HTTPS."""
        try:
            parsed = urlparse(url)
            is_valid = (parsed.scheme in ('http', 'https') and 
                       parsed.netloc and 
                       not parsed.netloc.endswith('.bing.com') and
                       not parsed.netloc.endswith('.microsoft.com'))
            logger.debug(f"URL validation for {url}: {is_valid}")
            return is_valid
        except Exception:
            return False


class DuckDuckGoParser(SearchEngineParser):
    """Parser for DuckDuckGo search results."""
    
    def parse_results(self, html_content: str, result_count: int) -> List[str]:
        """Parse DuckDuckGo search results."""
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        
        logger.debug(f"Parsing DuckDuckGo results, HTML length: {len(html_content)}")
        
        # Save HTML for debugging if needed
        if logger.isEnabledFor(logging.DEBUG):
            with open('/tmp/duckduckgo_debug_parser.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug("Saved DuckDuckGo HTML to /tmp/duckduckgo_debug_parser.html for debugging")
        
        # Try multiple selectors for DuckDuckGo results
        selectors = [
            'a.result__a',  # Main result links
            '.result a[href]',  # Any links in result containers
            '.results_links a.result__a',  # Links in results_links containers
            'div.result a[href]',  # Links in result divs
        ]
        
        for i, selector in enumerate(selectors):
            links = soup.select(selector)
            logger.debug(f"Selector {i+1} '{selector}' found {len(links)} links")
            
            for link in links:
                href = link.get('href', '')
                logger.debug(f"Processing href: {href[:100]}...")
                
                # Handle DuckDuckGo redirect URLs
                actual_url = self._extract_actual_url(href)
                if actual_url and self._is_valid_url(actual_url):
                    urls.append(actual_url)
                    logger.debug(f"Added valid URL: {actual_url}")
                
                if len(urls) >= result_count:
                    break
            
            if len(urls) >= result_count:
                break
        
        logger.info(f"DuckDuckGo parser found {len(urls)} URLs before deduplication")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"DuckDuckGo parser returning {len(unique_urls)} unique URLs")
        return unique_urls[:result_count]
    
    def _extract_actual_url(self, href: str) -> str:
        """Extract the actual URL from DuckDuckGo's redirect URL."""
        if not href:
            return None
            
        # Handle DuckDuckGo redirect URLs like:
        # //duckduckgo.com/l/?uddg=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FDog&rut=...
        if 'duckduckgo.com/l/' in href and 'uddg=' in href:
            try:
                # Parse the URL to get query parameters
                if href.startswith('//'):
                    href = 'https:' + href  # Add protocol for proper parsing
                parsed = urlparse(href)
                query_params = parse_qs(parsed.query)
                
                # Get the 'uddg' parameter which contains the URL-encoded actual URL
                if 'uddg' in query_params and query_params['uddg']:
                    encoded_url = query_params['uddg'][0]
                    try:
                        actual_url = unquote(encoded_url)
                        logger.debug(f"Decoded DuckDuckGo redirect URL: {href[:50]}... -> {actual_url}")
                        return actual_url
                    except Exception as e:
                        logger.debug(f"Failed to decode DuckDuckGo URL: {e}")
                        
            except Exception as e:
                logger.debug(f"Failed to parse DuckDuckGo redirect URL: {e}")
        
        # If it's not a redirect URL or we can't decode it, return as-is
        return href
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid HTTP/HTTPS."""
        try:
            parsed = urlparse(url)
            is_valid = (parsed.scheme in ('http', 'https') and 
                       parsed.netloc and 
                       not parsed.netloc.endswith('.duckduckgo.com'))
            logger.debug(f"URL validation for {url}: {is_valid}")
            return is_valid
        except Exception:
            return False


class SearchEngineService:
    """Service for fetching URLs from search engines."""
    
    def __init__(self):
        """Initialize the search engine service."""
        self.settings = SearchEngineSettings()
        self.parsers = {
            SearchEngineEnum.GOOGLE: GoogleParser(),
            SearchEngineEnum.BING: BingParser(),
            SearchEngineEnum.DUCKDUCKGO: DuckDuckGoParser(),
        }
        self.base_urls = {
            SearchEngineEnum.GOOGLE: self.settings.google_base_url,
            SearchEngineEnum.BING: self.settings.bing_base_url,
            SearchEngineEnum.DUCKDUCKGO: self.settings.duckduckgo_base_url,
        }
    
    async def fetch_seed_urls(self, search_engine_seeds: List[SearchEngineSeed]) -> List[str]:
        """
        Fetch seed URLs from multiple search engine seeds using Playwright.
        
        Args:
            search_engine_seeds: List of search engine seed specifications
            
        Returns:
            Deduplicated list of URLs from all search engines
        """
        all_urls: Set[str] = set()
        
        tasks = []
        for seed in search_engine_seeds:
            task = self._fetch_from_single_engine_playwright(seed)
            tasks.append(task)
        
        # Execute all search engine requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Search engine request failed: {result}")
                continue
            
            if isinstance(result, list):
                all_urls.update(result)
            
            # Rate limiting between requests
            await asyncio.sleep(self.settings.rate_limit_delay)
        
        return list(all_urls)
    
    async def _fetch_from_single_engine_playwright(self, seed: SearchEngineSeed) -> List[str]:
        """
        Fetch URLs from a single search engine using Playwright.
        
        Args:
            seed: Search engine seed specification
            
        Returns:
            List of URLs from the search engine
        """
        base_url = self.base_urls[seed.search_engine]
        parser = self.parsers[seed.search_engine]
        
        # Build search URL with query parameters
        if seed.search_engine == SearchEngineEnum.GOOGLE:
            search_url = f"{base_url}?q={seed.query}&num={min(seed.result_count, 100)}&hl=en&safe=off"
        elif seed.search_engine == SearchEngineEnum.BING:
            search_url = f"{base_url}?q={seed.query}&count={min(seed.result_count, 50)}"
        elif seed.search_engine == SearchEngineEnum.DUCKDUCKGO:
            search_url = f"{base_url}?q={seed.query}"
        else:
            raise ValueError(f"Unsupported search engine: {seed.search_engine}")
        
        logger.info(f"Fetching from {seed.search_engine} using Playwright: {search_url}")
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            try:
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1366, 'height': 768}
                )
                
                page = await context.new_page()
                
                # Navigate to the search URL
                response = await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                
                logger.debug(f"Response status: {response.status}")
                
                if response.status == 200:
                    # Wait a bit for any JavaScript to render
                    await page.wait_for_timeout(3000)
                    
                    # Get the HTML content
                    html_content = await page.content()
                    logger.debug(f"Received HTML content via Playwright, length: {len(html_content)}")
                    
                    urls = parser.parse_results(html_content, seed.result_count)
                    logger.info(f"Fetched {len(urls)} URLs from {seed.search_engine} for query: {seed.query}")
                    return urls
                else:
                    logger.warning(f"Search engine {seed.search_engine} returned status {response.status}")
                    
            except Exception as e:
                logger.error(f"Playwright request failed for {seed.search_engine}: {e}")
                
            finally:
                await browser.close()
        
        # Fallback to aiohttp for DuckDuckGo if Playwright failed
        if seed.search_engine == SearchEngineEnum.DUCKDUCKGO:
            logger.info(f"Falling back to aiohttp for {seed.search_engine}")
            return await self._fetch_from_single_engine_aiohttp(seed)
        
        logger.error(f"Failed to fetch from {seed.search_engine} using Playwright for query: {seed.query}")
        return []

    async def _fetch_from_single_engine_aiohttp(self, seed: SearchEngineSeed) -> List[str]:
        """
        Fetch URLs from a single search engine using aiohttp.
        
        Args:
            seed: Search engine seed specification
            
        Returns:
            List of URLs from the search engine
        """
        base_url = self.base_urls[seed.search_engine]
        parser = self.parsers[seed.search_engine]
        
        # Build search URL with query parameters
        if seed.search_engine == SearchEngineEnum.DUCKDUCKGO:
            search_url = f"{base_url}?q={seed.query}"
        else:
            raise ValueError(f"aiohttp fallback not implemented for: {seed.search_engine}")
        
        logger.info(f"Fetching from {seed.search_engine} using aiohttp: {search_url}")
        
        headers = {
            'User-Agent': self.settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        timeout = aiohttp.ClientTimeout(total=self.settings.request_timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(search_url, headers=headers) as response:
                    logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        html_content = await response.text()
                        logger.debug(f"Received HTML content via aiohttp, length: {len(html_content)}")
                        
                        urls = parser.parse_results(html_content, seed.result_count)
                        logger.info(f"Fetched {len(urls)} URLs from {seed.search_engine} for query: {seed.query}")
                        return urls
                    else:
                        logger.warning(f"Search engine {seed.search_engine} returned status {response.status}")
                        
            except Exception as e:
                logger.error(f"aiohttp request failed for {seed.search_engine}: {e}")
        
        logger.error(f"Failed to fetch from {seed.search_engine} using aiohttp for query: {seed.query}")
        return []

    async def _fetch_from_single_engine(self, session: aiohttp.ClientSession, seed: SearchEngineSeed) -> List[str]:
        """
        Fetch URLs from a single search engine.
        
        Args:
            session: aiohttp session
            seed: Search engine seed specification
            
        Returns:
            List of URLs from the search engine
        """
        base_url = self.base_urls[seed.search_engine]
        parser = self.parsers[seed.search_engine]
        
        # Build search URL with query parameters
        if seed.search_engine == SearchEngineEnum.GOOGLE:
            # Add more parameters to look more like a real browser request
            search_url = f"{base_url}?q={seed.query}&num={min(seed.result_count, 100)}&hl=en&safe=off"
        elif seed.search_engine == SearchEngineEnum.BING:
            search_url = f"{base_url}?q={seed.query}&count={min(seed.result_count, 50)}"
        elif seed.search_engine == SearchEngineEnum.DUCKDUCKGO:
            search_url = f"{base_url}?q={seed.query}"
        else:
            raise ValueError(f"Unsupported search engine: {seed.search_engine}")
        
        logger.info(f"Fetching from {seed.search_engine}: {search_url}")
        
        # Enhanced headers for Google to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
        
        for attempt in range(self.settings.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1} for {seed.search_engine}")
                
                # Configure proxy if specified
                request_kwargs = {'headers': headers}
                if self.settings.proxy_server:
                    request_kwargs['proxy'] = self.settings.proxy_server
                    logger.debug(f"Using proxy: {self.settings.proxy_server}")
                
                async with session.get(search_url, **request_kwargs) as response:
                    logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        html_content = await response.text()
                        logger.debug(f"Received HTML content, length: {len(html_content)}")
                        
                        urls = parser.parse_results(html_content, seed.result_count)
                        logger.info(f"Fetched {len(urls)} URLs from {seed.search_engine} for query: {seed.query}")
                        return urls
                    elif response.status == 429:
                        logger.warning(f"Rate limited by {seed.search_engine}, waiting longer...")
                        await asyncio.sleep(self.settings.rate_limit_delay * 3)
                    else:
                        logger.warning(f"Search engine {seed.search_engine} returned status {response.status}")
                        # Log response content for debugging
                        content = await response.text()
                        logger.debug(f"Response content preview: {content[:500]}")
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {seed.search_engine}: {e}")
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(self.settings.rate_limit_delay * (attempt + 1))
        
        logger.error(f"All attempts failed for {seed.search_engine} query: {seed.query}")
        return []
