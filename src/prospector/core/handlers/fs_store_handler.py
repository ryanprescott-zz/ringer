import json
import os
from pathlib import Path

from prospector.core.models import CrawlRecord
from prospector.core.settings import HandlerSettings
from .crawl_record_handler import CrawlRecordHandler


class FsStoreCrawlRecordHandler(CrawlRecordHandler):
    """Handler that stores crawl records as JSON files on the filesystem."""
    
    def __init__(self):
        """Initialize the filesystem handler with settings."""
        self.settings = HandlerSettings()
    
    def handle(self, crawl_record: CrawlRecord, crawl_name: str, crawl_datetime: str) -> None:
        """
        Store a crawl record as a JSON file in the filesystem.
        
        Files are organized as: /{crawl_name}_{datetime}/records/{url_hash}.json
        
        Args:
            crawl_record: The crawl record to store
            crawl_name: Name of the crawl
            crawl_datetime: Datetime string of the crawl
            
        Raises:
            OSError: If file system operations fail
            ValueError: If serialization fails
        """
        try:
            # Create directory structure
            crawl_dir = Path(self.settings.output_directory) / f"{crawl_name}_{crawl_datetime}"
            records_dir = crawl_dir / "records"
            records_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename from URL hash
            import hashlib
            url_hash = hashlib.md5(crawl_record.url.encode()).hexdigest()
            filename = f"{url_hash}.json"
            filepath = records_dir / filename
            
            # Serialize and write the record
            record_data = crawl_record.model_dump(mode='json')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise OSError(f"Failed to store crawl record for {crawl_record.url}: {str(e)}")