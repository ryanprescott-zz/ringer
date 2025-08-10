"""Service handler for sending crawl records to a web service."""

import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from prospector.core.models import CrawlRecord, HandleCrawlRecordRequest
from prospector.core.settings import HandlerSettings
from .crawl_record_handler import CrawlRecordHandler


logger = logging.getLogger(__name__)

class ServiceCrawlRecordHandler(CrawlRecordHandler):
    """Handler that sends crawl records to a web service via HTTP POST."""
    
    def __init__(self):
        """Initialize the service handler with settings and session."""
        self.settings = HandlerSettings()
        # Create a requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def handle(self, crawl_record: CrawlRecord, crawl_name: str, crawl_datetime: str) -> None:
        """
        Send a crawl record to the configured web service.
        
        Makes an HTTP POST request with retry logic. On failure after all retries,
        the record is logged and discarded.
        
        Args:
            crawl_record: The crawl record to send
            crawl_name: Name of the crawl
            crawl_datetime: Datetime string of the crawl
        """
        try:
            self._send_record_with_retry(crawl_record, crawl_name, crawl_datetime)
        except Exception as e:
            logger.error(
                f"Failed to send crawl record after all retries for {crawl_record.url}: {e}. "
                f"Record discarded."
            )
    
    def _send_record_with_retry(self, crawl_record: CrawlRecord, crawl_name: str, crawl_datetime: str) -> None:
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
            request_data = HandleCrawlRecordRequest(
                record=crawl_record,
                crawl_name=crawl_name,
                crawl_datetime=crawl_datetime
            )
            
            try:
                # Make the HTTP POST request
                response = self.session.post(
                    self.settings.service_url,
                    json=request_data.model_dump(mode='json'),
                    timeout=self.settings.service_timeout
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