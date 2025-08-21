"""DH crawl results manager for storing crawl records via the DH service."""

import logging
import requests
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ringer.core.models import (
    CrawlRecord,
    CrawlSpec,
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


    def create_crawl(self, crawl_spec: CrawlSpec) -> str:
        """
        Create a new crawl with the given spec by calling the DH service.
        
        Args:
            crawl_spec: Specification of the crawl to create.
            
        Returns:
            str: Storage ID for the created crawl
        """
        # Generate a UUID4 storage ID
        storage_id = str(uuid.uuid4())
        logger.debug(f"Creating crawl with storage ID: {storage_id}")
        
        error_msg = "Create functionality is not implemented for DhCrawlResultsManager"
        logger.error(f"{error_msg} for storage ID {storage_id}")
        raise NotImplementedError(error_msg)
        # TODO send HTTP post to dh create endpoint using the storage_id.
        # return storage_id

    
    def store_record(self, crawl_record: CrawlRecord, storage_id: str)-> None:
        """
        Store a crawl record to the DH service.
        
        Args:
            crawl_record: The crawl record to process.
            storage_id: Storage ID for the crawl
        """

        try:
            self._send_record_with_retry(crawl_record, storage_id)
        except Exception as e:
            logger.error(
                f"Failed to send crawl record after all retries for {crawl_record.url}: {e}. "
                f"Record discarded."
            )
        
    
    def delete_crawl(self, storage_id: str) -> None:
        """
        Delete a crawl by storage ID.
        
        Args:
            storage_id: the storage ID of the crawl to delete.
        """
        logger.debug(f"Attempting to delete crawl with storage ID: {storage_id}")
        
        error_msg = "Delete functionality is not implemented for DhCrawlResultsManager"
        logger.error(f"{error_msg} for storage ID {storage_id}")
        raise NotImplementedError(error_msg)
        # TODO implement deletion logic by calling the DH service.
    
    def _send_record_with_retry(self, crawl_record: CrawlRecord, storage_id: str) -> None:
        """
        Send a crawl record with retry logic.
        
        Args:
            crawl_record: The crawl record to send
            storage_id: Storage ID for the crawl
            
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
                record=crawl_record,
                crawl_id=storage_id
            )
            
            try:
                # Make the HTTP POST request
                response = self.session.post(
                    self.settings.service_url,
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
    
    def __del__(self):
        """Cleanup the requests session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
