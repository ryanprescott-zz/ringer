"""Search engine service for generating seed URLs."""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from ..models import SearchEngineSeed, SearchEngineEnum
from ..settings import SearchEngineSettings


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
        
        # Google search results are typically in <a> tags with specific patterns
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Google result links often start with /url?q= or /search?q=
            if href.startswith('/url?q='):
                # Extract the actual URL from Google's redirect
                url_match = re.search(r'/url\?q=([^&]+)', href)
                if url_match:
                    url = url_match.group(1)
                    if self._is_valid_url(url):
                        urls.append(url)
            elif href.startswith('http') and not 'google.com' in href:
                # Direct links that aren't Google's own
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
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout),
            headers={'User-Agent': self.settings.user_agent}
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
            search_url = f"{base_url}?q={seed.query}"
        elif seed.search_engine == SearchEngineEnum.BING:
            search_url = f"{base_url}?q={seed.query}"
        elif seed.search_engine == SearchEngineEnum.DUCKDUCKGO:
            search_url = f"{base_url}?q={seed.query}"
        else:
            raise ValueError(f"Unsupported search engine: {seed.search_engine}")
        
        for attempt in range(self.settings.max_retries):
            try:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        urls = parser.parse_results(html_content, seed.result_count)
                        logger.info(f"Fetched {len(urls)} URLs from {seed.search_engine} for query: {seed.query}")
                        return urls
                    else:
                        logger.warning(f"Search engine {seed.search_engine} returned status {response.status}")
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {seed.search_engine}: {e}")
                if attempt < self.settings.max_retries - 1:
                    await asyncio.sleep(self.settings.rate_limit_delay * (attempt + 1))
        
        logger.error(f"All attempts failed for {seed.search_engine} query: {seed.query}")
        return []
