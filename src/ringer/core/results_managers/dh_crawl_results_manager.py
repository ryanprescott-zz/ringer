"""DH crawl results manager for storing crawl records via the DH service."""

import logging
import requests
import uuid
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ringer.core.models import (
    CrawlRecord,
    CrawlRecordSummary,
    CrawlSpec,
    CrawlResultsId,
    StoreCrawlRecordRequest,
)
from ringer.core.settings import DhCrawlResultsManagerSettings
from .crawl_results_manager import CrawlResultsManager


logger = logging.getLogger(__name__)

class DhCrawlResultsManager(CrawlResultsManager):
    """Crawl Results manager that stores crawl data to the DH service."""
    
    def __init__(self):
        """Initialize the results manager with settings and session."""
        self.settings = DhCrawlResultsManagerSettings()
        # Create a requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })


    def create_crawl(self, crawl_spec: CrawlSpec, results_id: CrawlResultsId) -> None:
        """
        Create a new crawl with the given spec and results ID by calling the DH service.
        
        Args:
            crawl_spec: Specification of the crawl to create.
            results_id: Identifier for the crawl results data set.
        """
        
        # TODO: Implement creation call to DH service with crawl spec as metadata when available
        logger.warning(f"DH Crawl Results Manager does not support crawl creation. Received results_id: {results_id}")

    
    def store_record(self, crawl_record, results_id: CrawlResultsId, crawl_id: str) -> None:
        """
        Store a crawl record to the DH service.
        
        Args:
            crawl_record: The crawl record to process.
            results_id: Identifier for the crawl results data set
            crawl_id: Unique identifier for the crawl
        """

        try:
            self._send_record_with_retry(crawl_record, results_id, crawl_id)
        except Exception as e:
            logger.error(
                f"Failed to send crawl record after all retries for {crawl_record.url}: {e}. "
                f"Record discarded."
            )
        
    
    def delete_crawl(self, results_id: CrawlResultsId) -> None:
        """
        Delete a crawl by results ID.
        
        Args:
            results_id: the results ID of the crawl to delete.
        """
        logger.warning(f"DH Crawl Results Manager does not support crawl deletion. Received results_id: {results_id}")

    
    def _send_record_with_retry(self, crawl_record: CrawlRecord, results_id: CrawlResultsId, crawl_id: str) -> None:
        """
        Send a crawl record with retry logic.
        
        Args:
            crawl_record: The crawl record to send
            results_id: Identifier for the crawl results data set
            crawl_id: Unique identifier for the crawl
            
        Raises:
            requests.exceptions.RequestException: For HTTP-related errors
            Exception: For other errors that should trigger retries
        """
        # Apply retry decorator with settings-based configuration
        @retry(
            stop=stop_after_attempt(self.settings.service_max_retries),
            wait=wait_exponential(multiplier=1, exp_base=self.settings.service_retry_exponential_base),
            retry=retry_if_exception_type((requests.exceptions.RequestException, Exception))
        )
        def _do_send():
            # Create the request payload
            request_data = StoreCrawlRecordRequest(
                operation="add_from_docs",
                operation_info={
                    "documents": [crawl_record],
                    "source": crawl_id
                }
            )
            
            # Construct the URL
            url = f"{self.settings.service_url}/workbook/{results_id.collection_id}/bin/{results_id.data_id}"
            
            try:
                # Make the HTTP PATCH request
                response = self.session.patch(
                    url,
                    json=request_data.model_dump(mode='json'),
                    timeout=self.settings.service_timeout_sec
                )
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_msg = (
                        f"Service returned status {response.status_code} for {crawl_record.url}. "
                        f"Response: {response.text}"
                    )
                    logger.error(error_msg)
                    raise requests.exceptions.HTTPError(error_msg)
                
                logger.debug(f"Successfully sent crawl record for {crawl_record.url}")
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {crawl_record.url}: {e}")
                raise
            except Exception as e:
                logger.warning(f"Unexpected error sending record for {crawl_record.url}: {e}")
                raise
        
        # Execute with retry logic
        _do_send()
    
    def get_crawl_record_summaries(self, results_id: CrawlResultsId, record_count: int = 10, score_type: str = "composite") -> List[CrawlRecordSummary]:
        """
        Get crawl record summaries sorted by score type.
        
        Note: DH service doesn't support retrieving record summaries, so this returns empty list.
        
        Args:
            results_id: Identifier for the crawl results data set
            record_count: Number of record summaries to return
            score_type: Type of score to sort by ('composite' or analyzer name)
            
        Returns:
            Empty list (DH service doesn't support record summary retrieval)
        """
        logger.warning("DH service doesn't support crawl record summary retrieval")
        return []

    def get_crawl_records(self, results_id: CrawlResultsId, record_ids: List[str]) -> List[CrawlRecord]:
        """
        Get crawl records by their IDs.
        
        Note: DH service doesn't support retrieving full records, so this returns empty list.
        
        Args:
            results_id: Identifier for the crawl results data set
            record_ids: List of record IDs to retrieve
            
        Returns:
            Empty list (DH service doesn't support full record retrieval)
        """
        logger.warning("DH service doesn't support crawl record retrieval")
        return []

    def __del__(self):
        """Cleanup the requests session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
