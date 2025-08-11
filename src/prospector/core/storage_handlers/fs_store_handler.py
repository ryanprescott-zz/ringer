import logging
import json
import os
from pathlib import Path

from prospector.core.models import (
    CrawlRecord,
    CrawlSpec,
)
from prospector.core.settings import FsStoreHandlerSettings
from .crawl_storage_handler import CrawlStorageHandler

logger = logging.getLogger(__name__)

class FsStoreHandler(CrawlStorageHandler):
    """Handler that stores crawl records as JSON files on the filesystem."""
    
    def __init__(self):
        """Initialize the filesystem handler with settings."""
        self.settings = FsStoreHandlerSettings()

        self.output_directory = Path(self.settings.output_directory)
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True, exist_ok=True)

    
    def create_crawl(self, crawl_spec: CrawlSpec) -> None:
        """
        Create a new crawl with the given spec in the filesystem store.
        
        Args:
            crawl_spec: Specification of the crawl to create.
        
        Raises:
            ValueError: If crawl_spec is not provided.
            OSError: If directory creation fails.
        """

        logger.info(f"Creating crawl with spec: {crawl_spec}")

        if not crawl_spec:
            raise ValueError("Crawl specification must be provided.")

        crawl_directory = Path(self.settings.output_directory) / crawl_spec.name
        if not crawl_directory.exists():
            logger.info(f"Creating crawl directory: {crawl_directory}")

            try:
                crawl_directory.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create crawl directory {crawl_directory}: {str(e)}")
                raise OSError(f"Failed to create crawl directory {crawl_directory}: {str(e)}")
        else:
            logger.warning(f"Crawl directory already exists: {crawl_directory}")
        
    
    def store_record(self, crawl_record: CrawlRecord, crawl_name: str) -> None:
        """
        Store a crawl record.
        
        Args:
            crawl_record: The crawl record to process
            
        Raises:
            OSError: If file system operations fail
            ValueError: If serialization fails
        """
        try:

            crawl_directory = Path(self.settings.output_directory) / crawl_name
            if not crawl_directory.exists():
                raise ValueError(f"Unable to store record to crawl directory that does not exist: {crawl_directory}")

            record_directory = crawl_directory / self.settings.record_directory
            if not record_directory.exists():
                record_directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created record directory: {record_directory}")
            
            # Generate filename from URL hash

            filename = f"{crawl_record.id}.json"
            filepath = record_directory / filename
            
            # Serialize and write the record
            record_data = crawl_record.model_dump(mode='json')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to store crawl record for {crawl_record.url}: {str(e)}")
            raise OSError(f"Failed to store crawl record for {crawl_record.url}: {str(e)}")


    def delete_crawl(self, crawl_name: str) -> None:
        """
        Delete a crawl by crawl name.
        
        Args:
            crawl_name: the name of the crawl to delete.
        Raises:
            OSError: If file system operations fail
        """

        crawl_directory = Path(self.settings.output_directory) / crawl_name
        if crawl_directory.exists():
            logger.info(f"Deleting crawl directory: {crawl_directory}")
            try:
                import shutil
                shutil.rmtree(crawl_directory)
                logger.info(f"Deleted crawl directory: {crawl_directory}")
            except OSError as e:
                logger.error(f"Failed to delete crawl directory {crawl_directory}: {str(e)}")
                raise OSError(f"Failed to delete crawl directory {crawl_directory}: {str(e)}")
        else:
            logger.warning(f"Unable to delete crawl directory - directory does not exist: {crawl_directory}")
