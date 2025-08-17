"""File system crawl results manager for storing crawl records as JSON files."""

import json
import logging
import uuid
import shutil
from pathlib import Path

from prospector.core.models import CrawlRecord, CrawlSpec
from prospector.core.settings import FsCrawlResultsManagerSettings
from .crawl_results_manager import CrawlResultsManager


logger = logging.getLogger(__name__)

class FsCrawlResultsManager(CrawlResultsManager):
    """Results Manager that stores crawl records as JSON files on the filesystem."""
    
    def __init__(self):
        """Initialize the file system results manager with settings."""
        self.settings = FsCrawlResultsManagerSettings()
        
        # Ensure the base directory exists
        self.base_dir = Path(self.settings.crawl_data_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized FsCrawlResultsManager with base directory: {self.base_dir}")
    
    def create_crawl(self, crawl_spec: CrawlSpec) -> str:
        """
        Create a new crawl directory structure.
        
        Args:
            crawl_spec: Specification for the crawl to create
            
        Returns:
            str: Storage ID for the created crawl
        """
        # Generate a UUID4 storage ID
        storage_id = str(uuid.uuid4())
        
        crawl_dir = self.base_dir / storage_id
        crawl_dir.mkdir(parents=True, exist_ok=True)
        
        # Store the crawl spec
        spec_file = crawl_dir / "crawl_spec.json"
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(crawl_spec.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Created crawl directory: {crawl_dir} with storage ID: {storage_id}")
        return storage_id
    
    def store_record(self, crawl_record: CrawlRecord, storage_id: str) -> None:
        """
        Store a crawl record as a JSON file.
        
        Args:
            crawl_record: The crawl record to store
            storage_id: Storage ID for the crawl
        """
        try:
            crawl_dir = self.base_dir / storage_id / "records"
            crawl_dir.mkdir(parents=True, exist_ok=True)
            
            # Use the record's ID as the filename
            record_file = crawl_dir / f"{crawl_record.id}.json"
            
            # Store the record as JSON
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(crawl_record.model_dump(), f, indent=2, default=str)
            
            logger.debug(f"Stored crawl record: {record_file}")
            
        except Exception as e:
            logger.error(f"Failed to store crawl record for {crawl_record.url}: {e}")
            raise
    
    def delete_crawl(self, storage_id: str) -> None:
        """
        Delete a crawl directory and all its contents.
        
        Args:
            storage_id: Storage ID of the crawl to delete
        """
        try:
            crawl_dir = self.base_dir / storage_id
            
            if crawl_dir.exists():
                shutil.rmtree(crawl_dir)
                logger.info(f"Deleted crawl directory: {crawl_dir}")
            else:
                logger.warning(f"Crawl directory does not exist: {crawl_dir}")
        except Exception as e:
            logger.error(f"Failed to delete crawl directory for {storage_id}: {e}")
            raise
