"""Search engine service for generating seed URLs."""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Set
from urllib.parse import urljoin, urlparse, unquote

import aiohttp
from bs4 import BeautifulSoup

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
        
        # Bing results are typically in <a> tags with class containing 'b_algo'
        for result in soup.find_all('li', class_=re.compile(r'b_algo')):
            link = result.find('a', href=True)
            if link:
                href = link['href']
                if self._is_valid_url(href):
                    urls.append(href)
                    
            if len(urls) >= result_count:
                break
        
        return urls[:result_count]
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid HTTP/HTTPS."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and parsed.netloc
        except Exception:
            return False


class DuckDuckGoParser(SearchEngineParser):
    """Parser for DuckDuckGo search results."""
    
    def parse_results(self, html_content: str, result_count: int) -> List[str]:
        """Parse DuckDuckGo search results."""
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        
        # DuckDuckGo results are typically in <a> tags with specific classes
        for link in soup.find_all('a', class_=re.compile(r'result__a')):
            href = link.get('href')
            if href and self._is_valid_url(href):
                urls.append(href)
                
            if len(urls) >= result_count:
                break
        
        return urls[:result_count]
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid HTTP/HTTPS."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and parsed.netloc
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
        Fetch seed URLs from multiple search engine seeds.
        
        Args:
            search_engine_seeds: List of search engine seed specifications
            
        Returns:
            Deduplicated list of URLs from all search engines
        """
        all_urls: Set[str] = set()
        
        connector = None
        if self.settings.proxy_server:
            connector = aiohttp.TCPConnector()
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout),
            headers={'User-Agent': self.settings.user_agent},
            connector=connector
        ) as session:
            
            tasks = []
            for seed in search_engine_seeds:
                task = self._fetch_from_single_engine(session, seed)
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
