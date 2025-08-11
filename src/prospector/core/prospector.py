"""Prospector web crawler implementation."""

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from queue import Queue, Empty
from threading import Lock
from typing import Dict, List, Set, Optional
from urllib.parse import urlparse
from sortedcontainers import SortedSet

from .models import CrawlSpec, CrawlRecord, AnalyzerSpec, RunStateEnum, RunState
from .score_analyzers import ScoreAnalyzer, KeywordScoreAnalyzer, LLMServiceScoreAnalyzer
from .scrapers import Scraper, PlaywrightScraper  
from .storage_handlers import CrawlStorageHandler, FsStoreHandler, DhStoreHandler
from .settings import ProspectorSettings, HandlerType


logger = logging.getLogger(__name__)


class ScoreUrlTuple:
    """A tuple-like class that sorts by score but compares equality by URL."""
    
    def __init__(self, score: float, url: str):
        self.score = score
        self.url = url
    
    def __lt__(self, other):
        # Sort by score descending (higher scores first)
        return self.score > other.score
    
    def __eq__(self, other):
        # Equality based on URL for uniqueness
        return self.url == other.url
    
    def __hash__(self):
        # Hash based on URL for set operations
        return hash(self.url)
    
    def __repr__(self):
        return f"ScoreUrlTuple({self.score}, '{self.url}')"
    
    def __iter__(self):
        # Allow tuple unpacking: score, url = tuple_obj
        yield self.score
        yield self.url


class CrawlState:
    """Thread-safe state management for a single crawl."""
    
    def __init__(self, crawl_spec: CrawlSpec):
        """
        Initialize crawl state.
        
        Args:
            crawl_spec: Specification for the crawl
        """
        self.crawl_spec = crawl_spec
        self.frontier = SortedSet()  # Will contain ScoreUrlTuple objects
        self.visited_urls: Set[str] = set()
        self.analyzers: List[ScoreAnalyzer] = []
        self.analyzer_weights: Dict[str, float] = {}
        self.run_state_history: List[RunState] = []
        self.lock = Lock()
        
        # Initialize frontier with seed URLs (score 0.0 initially)
        for url in crawl_spec.seed_urls:
            self.frontier.add(ScoreUrlTuple(0.0, url))
    
    @property
    def current_state(self) -> RunStateEnum:
        """
        Get the current run state of the crawl.
        
        Returns:
            RunStateEnum: The most recent state from the history
        """
        if not self.run_state_history:
            return RunStateEnum.CREATED
        return self.run_state_history[-1].state
    
    def add_state(self, run_state: RunState) -> None:
        """
        Add a new state to the crawl's history.
        
        Args:
            run_state: The RunState object to add
        """
        with self.lock:
            self.run_state_history.append(run_state)
    
    def add_urls_with_scores(self, url_scores: List[tuple]) -> None:
        """
        Add URLs with their scores to the frontier.
        
        Args:
            url_scores: List of (score, url) tuples
        """
        with self.lock:
            for score, url in url_scores:
                if url not in self.visited_urls:
                    self.frontier.add(ScoreUrlTuple(score, url))
    
    def get_next_url(self) -> str:
        """
        Get the next URL to process from the frontier.
        
        Returns:
            str: Next URL to process, or None if frontier is empty
        """
        with self.lock:
            while self.frontier:
                score_url_tuple = self.frontier.pop(0)  # Get highest scoring URL
                url = score_url_tuple.url
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    return url
            return None
    
    def is_url_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed based on domain blacklist and file type filters.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL is allowed
        """
        parsed = urlparse(url)
        
        # Check domain blacklist
        if self.crawl_spec.domain_blacklist:
            domain = parsed.netloc.lower()
            for blacklisted_domain in self.crawl_spec.domain_blacklist:
                if blacklisted_domain.lower() in domain:
                    return False
        
        return True


class Prospector:
    """Best-first-search web crawler."""
    
    def __init__(self):
        """Initialize the Prospector with settings and components."""
        self.settings = ProspectorSettings()
        self.crawls: Dict[str, CrawlState] = {}
        self.scraper: Scraper = PlaywrightScraper()
        
        # Initialize handler based on settings
        if self.settings.handler_type == HandlerType.FILE_SYSTEM:
            self.handler: CrawlStorageHandler = FsStoreHandler()
        elif self.settings.handler_type == HandlerType.DH:
            self.handler: CrawlStorageHandler = DhStoreHandler()
        else:
            raise ValueError(f"Unknown handler type: {self.settings.handler_type}")
        
        self.executor = ThreadPoolExecutor(
            max_workers=min(max(1, os.cpu_count() - 2), self.settings.max_workers)
        )
        self.crawls_lock = Lock()
    
    def create(self, crawl_spec: CrawlSpec) -> tuple:
        """
        Create a new crawl.
        
        Args:
            crawl_spec: Specification for the crawl including seed URLs and analyzers
            
        Returns:
            tuple: (crawl_id, RunState) containing the crawl ID and creation state
            
        Raises:
            ValueError: If crawl with same ID already exists or invalid analyzer specs
        """
        crawl_id = crawl_spec.id
        
        with self.crawls_lock:
            if crawl_id in self.crawls:
                raise ValueError(f"Crawl with ID {crawl_id} already exists")
            
            # Create crawl state
            crawl_state = CrawlState(crawl_spec)
            
            # Initialize analyzers
            self._initialize_analyzers(crawl_state, crawl_spec.analyzer_specs)
            
            # Add CREATED state
            created_state = RunState(state=RunStateEnum.CREATED)
            crawl_state.add_state(created_state)
            
            # Store crawl state
            self.crawls[crawl_id] = crawl_state

            # Create crawl in storage handler
            self.handler.create_crawl(crawl_spec)
            
        logger.info(f"Created crawl {crawl_spec.name} with ID {crawl_id}")
        return (crawl_id, created_state)
    

    def start(self, crawl_id: str) -> tuple:
        """
        Start a crawl.
        
        Args:
            crawl_id: ID of the crawl to start
            
        Returns:
            tuple: (crawl_id, RunState) containing the crawl ID and start state
            
        Raises:
            ValueError: If crawl ID not found
            RuntimeError: If crawl is already running
        """
        started_state = None
        with self.crawls_lock:
            if crawl_id not in self.crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            crawl_state = self.crawls[crawl_id]
            if crawl_state.current_state == RunStateEnum.RUNNING:
                raise RuntimeError(f"Crawl {crawl_id} is already running")
            
            started_state = RunState(state=RunStateEnum.RUNNING)
            crawl_state.add_state(started_state)
        
        # create crawl workers to thread pool
        futures = []
        for _ in range(crawl_state.crawl_spec.worker_count):
            future = self.executor.submit(self._crawl_worker, crawl_id)
            futures.append(future)
        
        logger.info(f"Started crawl {crawl_id} with {len(futures)} workers")
        return (crawl_id, started_state)
    

    def stop(self, crawl_id: str) -> tuple:
        """
        Stop a running crawl.
        
        Args:
            crawl_id: ID of the crawl to stop
            
        Returns:
            tuple: (crawl_id, RunState) containing the crawl ID and stop state
            
        Raises:
            ValueError: If crawl ID not found
        """
        stopped_state = None
        with self.crawls_lock:
            if crawl_id not in self.crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            crawl_state = self.crawls[crawl_id]
            stopped_state = RunState(state=RunStateEnum.STOPPED)
            crawl_state.add_state(stopped_state)
        
        logger.info(f"Stopped crawl {crawl_id}")
        return (crawl_id, stopped_state)
    

    def delete(self, crawl_id: str) -> None:
        """
        Remove a crawl from Prospector state.
        
        Args:
            crawl_id: ID of the crawl to delete
            
        Raises:
            ValueError: If crawl ID not found
            RuntimeError: If crawl is still running
        """
        with self.crawls_lock:
            if crawl_id not in self.crawls:
                raise ValueError(f"Crawl {crawl_id} not found")
            
            crawl_state = self.crawls[crawl_id]
            if crawl_state.current_state == RunStateEnum.RUNNING:
                raise RuntimeError(f"Cannot delete running crawl {crawl_id}")
            
            del self.crawls[crawl_id]

            # Delete from storage handler
            self.handler.delete_crawl(crawl_state.crawl_spec.id)
        
        logger.info(f"Deleted crawl {crawl_id}")
    

    def _initialize_analyzers(self, crawl_state: CrawlState, analyzer_specs: List[AnalyzerSpec]) -> None:
        """
        Initialize analyzers for a crawl based on specifications.
        
        Args:
            crawl_state: Crawl state to initialize
            analyzer_specs: List of analyzer specifications
            
        Raises:
            ValueError: If unknown analyzer type or invalid parameters
        """
        for spec in analyzer_specs:
            if spec.name == "KeywordScoreAnalyzer":
                if not hasattr(spec.params, '__iter__'):
                    raise ValueError(f"KeywordScoreAnalyzer requires iterable params")
                analyzer = KeywordScoreAnalyzer(spec.params)
            elif spec.name == "LLMServiceScoreAnalyzer":
                analyzer = LLMServiceScoreAnalyzer()
            else:
                raise ValueError(f"Unknown analyzer type: {spec.name}")
            
            crawl_state.analyzers.append(analyzer)
            crawl_state.analyzer_weights[spec.name] = spec.composite_weight
    
    def _crawl_worker(self, crawl_id: str) -> None:
        """
        Worker function that processes URLs from the frontier.
        
        Args:
            crawl_id: ID of the crawl to process
        """
        crawl_state = self.crawls[crawl_id]
        
        while crawl_state.current_state == RunStateEnum.RUNNING:
            url = crawl_state.get_next_url()
            if url is None:
                # No more URLs to process
                time.sleep(1)
                continue
            
            try:
                self._process_url(crawl_state, url)
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                continue
    
    def _process_url(self, crawl_state: CrawlState, url: str) -> None:
        """
        Process a single URL: scrape, score, and handle the result.
        
        Args:
            crawl_state: State of the current crawl
            url: URL to process
        """
        # Check if URL is allowed
        if not crawl_state.is_url_allowed(url):
            logger.debug(f"URL filtered out: {url}")
            return
        
        try:
            # Scrape the page
            crawl_record = self.scraper.scrape(url)
            
            # Score the content
            self._score_content(crawl_state, crawl_record)
            
            # Filter and score discovered links
            scored_links = self._score_links(crawl_state, crawl_record.links)
            
            # Add scored links to frontier
            if scored_links:
                crawl_state.add_urls_with_scores(scored_links)
            
            # Handle the crawl record
            self.handler.store_record(
                crawl_record,
                crawl_state.crawl_spec.id,
            )
            
            logger.debug(f"Processed URL {url} with score {crawl_record.composite_score}")
            
        except Exception as e:
            logger.error(f"Failed to process URL {url}: {e}")
            # Do not retry failed URLs
    
    def _score_content(self, crawl_state: CrawlState, crawl_record: CrawlRecord) -> None:
        """
        Score the content of a crawl record using configured analyzers.
        
        Args:
            crawl_state: State of the current crawl
            crawl_record: Record to score
        """
        scores = {}
        total_weighted_score = 0.0
        total_weights = 0.0
        
        for i, analyzer in enumerate(crawl_state.analyzers):
            analyzer_name = type(analyzer).__name__
            try:
                score = analyzer.score(crawl_record.extracted_content)
                scores[analyzer_name] = score
                
                weight = crawl_state.analyzer_weights[analyzer_name]
                total_weighted_score += score * weight
                total_weights += weight
                
            except Exception as e:
                logger.error(f"Error scoring with {analyzer_name}: {e}")
                scores[analyzer_name] = 0.0
        
        # Calculate composite score as weighted average
        composite_score = total_weighted_score / total_weights if total_weights > 0 else 0.0
        
        crawl_record.scores = scores
        crawl_record.composite_score = composite_score
    
    def _score_links(self, crawl_state: CrawlState, links: List[str]) -> List[tuple]:
        """
        Filter and score discovered links for addition to frontier.
        
        For now, assigns the same composite score as the parent page.
        In the future, this could be enhanced with link-specific scoring.
        
        Args:
            crawl_state: State of the current crawl  
            links: List of discovered links
            
        Returns:
            List[tuple]: List of (score, url) tuples for allowed links
        """
        scored_links = []
        
        for link in links:
            if crawl_state.is_url_allowed(link):
                # For now, use a default score for new links
                # In the future, this could be enhanced with link analysis
                scored_links.append((0.5, link))
        
        return scored_links
    
    def shutdown(self) -> None:
        """
        Shutdown the Prospector and cleanup resources.
        """
        # Stop all running crawls
        with self.crawls_lock:
            for crawl_id, crawl_state in self.crawls.items():
                if crawl_state.current_state == RunStateEnum.RUNNING:
                    crawl_state.add_state(RunState(state=RunStateEnum.STOPPED))
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        logger.info("Prospector shutdown complete")
