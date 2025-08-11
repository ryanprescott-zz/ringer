"""Service handler for sending crawl records to a web service."""

import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from prospector.core.models import (
    CrawlRecord,
    CrawlSpec,
    StoreCrawlRecordRequest,
)
from prospector.core.settings import DhStoreHandlerSettings
from .crawl_storage_handler import CrawlStorageHandler


logger = logging.getLogger(__name__)

class DhStoreHandler(CrawlStorageHandler):
    """Handler that stores crawl data to the DH service."""
    
    def __init__(self):
        """Initialize the storage handler with settings and session."""
        self.settings = DhStoreHandlerSettings()
        # Create a requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })


    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """
        Create a new crawl with the given spec by calling the DH service.
        
        Args:
            crawl_spec: Specification of the crawl to create.
        """

        # TODO send HTTP post to dh create endpoint.

    
    def store_record(self, crawl_record: CrawlRecord, crawl_name: str)-> None:
        """
        Store a crawl record to the DH service.
        
        Args:
            crawl_record: The crawl record to process.
            crawl_name: Name of the crawl
        """

        try:
            self._send_record_with_retry(crawl_record, crawl_name)
        except Exception as e:
            logger.error(
                f"Failed to send crawl record after all retries for {crawl_record.url}: {e}. "
                f"Record discarded."
            )
        
    
    def delete_crawl(self, crawl_name: str) -> None:
        """
        Delete a crawl by crawl name. This method does not perform any action as the 
        DH service does not support deletion from this application.
        
        Args:
            crawl_name: the name of the crawl to delete.
        """

        logger.warning(f"Delete operation for crawl name {crawl_name} is not supported by the DH service. No action taken.")
        # No action needed as per current service capabilities

    
    def _send_record_with_retry(self, crawl_record: CrawlRecord, crawl_name: str) -> None:
        """
        Send a crawl record with retry logic.
        
        Args:
            crawl_record: The crawl record to send
            crawl_name: Name of the crawl
            crawl_datetime: Datetime string of the crawl
            
        Raises:
            requests.exceptions.RequestException: For HTTP-related errors
            Exception: For other errors that should trigger retries
        """
        # Apply retry decorator with settings-based configuration
        @retry(
            stop=stop_after_attempt(self.settings.service_max_retries),
            wait=wait_exponential(multiplier=1, base=self.settings.service_retry_exponential_base),
            retry=retry_if_exception_type((requests.exceptions.RequestException, Exception))
        )
        def _do_send():
            # Create the request payload
            request_data = StoreCrawlRecordRequest(
                record=crawl_record,
                crawl_name=crawl_name
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
