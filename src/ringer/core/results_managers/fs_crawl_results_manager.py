"""File system crawl results manager for storing crawl records as JSON files."""

import json
import logging
import uuid
import shutil
from pathlib import Path

from typing import List
from ringer.core.models import CrawlRecord, CrawlRecordSummary, CrawlSpec, CrawlResultsId
from ringer.core.settings import FsCrawlResultsManagerSettings
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
    
    def create_crawl(self, crawl_spec: CrawlSpec, results_id: CrawlResultsId) -> None:
        """
        Create a new crawl directory structure.
        
        Args:
            crawl_spec: Specification for the crawl to create
            results_id: Identifier for the crawl results data set
        """
        logger.debug(f"Creating crawl directory for results_id: collection_id={results_id.collection_id}, data_id={results_id.data_id}")
        
        try:
            crawl_dir = self.base_dir / results_id.collection_id / results_id.data_id
            try:
                crawl_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created crawl directory: {crawl_dir}")
            except Exception as e:
                logger.error(f"Failed to create crawl directory {crawl_dir}: {e}")
                raise
            
            # Store the crawl spec
            spec_file = crawl_dir / "crawl_spec.json"
            try:
                with open(spec_file, 'w', encoding='utf-8') as f:
                    json.dump(crawl_spec.model_dump(), f, indent=2, default=str)
                logger.debug(f"Stored crawl spec to: {spec_file}")
            except Exception as e:
                logger.error(f"Failed to store crawl spec to {spec_file}: {e}")
                # Cleanup directory if spec storage fails
                try:
                    shutil.rmtree(crawl_dir)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup directory after spec storage failure: {cleanup_error}")
                raise
            
            # Store the results ID
            results_id_file = crawl_dir / "results_id.json"
            try:
                with open(results_id_file, 'w', encoding='utf-8') as f:
                    json.dump(results_id.model_dump(), f, indent=2, default=str)
                logger.debug(f"Stored results ID to: {results_id_file}")
            except Exception as e:
                logger.error(f"Failed to store results ID to {results_id_file}: {e}")
                # Cleanup directory if results ID storage fails
                try:
                    shutil.rmtree(crawl_dir)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup directory after results ID storage failure: {cleanup_error}")
                raise
            
            logger.info(f"Successfully created crawl directory: {crawl_dir} with results_id: {results_id.collection_id}/{results_id.data_id}")
            
        except Exception as e:
            logger.error(f"Failed to create crawl for results_id {results_id.collection_id}/{results_id.data_id}: {e}")
            raise
    
    def store_record(self, crawl_record: CrawlRecord, results_id: CrawlResultsId, crawl_id: str) -> None:
        """
        Store a crawl record as a JSON file.
        
        Args:
            crawl_record: The crawl record to store
            results_id: Identifier for the crawl results data set
            crawl_id: Unique identifier for the crawl
        """
        try:
            crawl_dir = self.base_dir / results_id.collection_id / results_id.data_id / "records"
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
    
    def delete_crawl(self, results_id: CrawlResultsId) -> None:
        """
        Delete a crawl directory and all its contents.
        
        Args:
            results_id: Results ID of the crawl to delete
        """
        try:
            crawl_dir = self.base_dir / results_id.collection_id / results_id.data_id
            
            if crawl_dir.exists():
                shutil.rmtree(crawl_dir)
                logger.info(f"Deleted crawl directory: {crawl_dir}")
            else:
                logger.warning(f"Crawl directory does not exist: {crawl_dir}")
        except Exception as e:
            logger.error(f"Failed to delete crawl directory for {results_id.collection_id}/{results_id.data_id}: {e}")
            raise
    
    def get_crawl_records(self, results_id: CrawlResultsId, record_count: int = 10, score_type: str = "composite") -> List[CrawlRecord]:
        """
        Get crawl records sorted by score type.
        
        Args:
            results_id: Identifier for the crawl results data set
            record_count: Number of records to return
            score_type: Type of score to sort by ('composite' or analyzer name)
            
        Returns:
            List of CrawlRecord objects sorted by score in descending order
        """
        try:
            records_dir = self.base_dir / results_id.collection_id / results_id.data_id / "records"
            
            if not records_dir.exists():
                return []
            
            # Load all records
            records = []
            for record_file in records_dir.glob("*.json"):
                try:
                    with open(record_file, 'r', encoding='utf-8') as f:
                        record_data = json.load(f)
                        record = CrawlRecord(**record_data)
                        records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to load record from {record_file}: {e}")
                    continue
            
            # Sort records by score type in descending order
            if score_type == "composite":
                records.sort(key=lambda r: r.composite_score, reverse=True)
            else:
                # Sort by specific analyzer score
                records.sort(key=lambda r: r.scores.get(score_type, 0.0), reverse=True)
            
            # Return top record_count records
            return records[:record_count]
            
        except Exception as e:
            logger.error(f"Failed to get crawl records for {results_id.collection_id}/{results_id.data_id}: {e}")
            raise

    def get_crawl_record_summaries(self, results_id: CrawlResultsId, record_count: int = 10, score_type: str = "composite") -> List[CrawlRecordSummary]:
        """
        Get crawl record summaries sorted by score type.
        
        Args:
            results_id: Identifier for the crawl results data set
            record_count: Number of record summaries to return
            score_type: Type of score to sort by ('composite' or analyzer name)
            
        Returns:
            List of CrawlRecordSummary objects sorted by score in descending order
        """
        try:
            records_dir = self.base_dir / results_id.collection_id / results_id.data_id / "records"
            
            if not records_dir.exists():
                return []
            
            # Load all records but only extract id and url for summaries
            record_summaries = []
            for record_file in records_dir.glob("*.json"):
                try:
                    with open(record_file, 'r', encoding='utf-8') as f:
                        record_data = json.load(f)
                        # Create a minimal CrawlRecord to get the sorting score
                        record = CrawlRecord(**record_data)
                        # Get the score for sorting
                        if score_type == "composite":
                            sort_score = record.composite_score
                        else:
                            sort_score = record.scores.get(score_type, 0.0)
                        
                        record_summary = CrawlRecordSummary(
                            id=record.id,
                            url=record.url,
                            score=sort_score
                        )
                        record_summaries.append((sort_score, record_summary))
                except Exception as e:
                    logger.warning(f"Failed to load record from {record_file}: {e}")
                    continue
            
            # Sort by score in descending order and extract summaries
            record_summaries.sort(key=lambda x: x[0], reverse=True)
            sorted_summaries = [summary for _, summary in record_summaries[:record_count]]
            
            return sorted_summaries
            
        except Exception as e:
            logger.error(f"Failed to get crawl record summaries for {results_id.collection_id}/{results_id.data_id}: {e}")
            raise
