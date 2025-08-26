"""SQLite crawl results manager for storing crawl records in a SQLite database."""

import logging
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.sqlite import JSON

from ringer.core.models import CrawlRecord, CrawlSpec, CrawlResultsId
from ringer.core.settings import SQLiteCrawlResultsManagerSettings
from .crawl_results_manager import CrawlResultsManager


logger = logging.getLogger(__name__)

Base = declarative_base()


class CrawlSpecTable(Base):
    """SQLAlchemy model for CrawlSpec."""
    __tablename__ = 'crawl_specs'
    
    id = Column(String, primary_key=True)
    collection_id = Column(String, nullable=False)
    data_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    seeds = Column(JSON, nullable=False)
    analyzer_specs = Column(JSON, nullable=False)
    worker_count = Column(Integer, nullable=False)
    domain_blacklist = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to crawl records
    records = relationship("CrawlRecordTable", back_populates="crawl_spec", cascade="all, delete-orphan")


class CrawlRecordTable(Base):
    """SQLAlchemy model for CrawlRecord."""
    __tablename__ = 'crawl_records'
    
    id = Column(String, primary_key=True)
    crawl_spec_id = Column(String, ForeignKey('crawl_specs.id'), nullable=False)
    crawl_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    page_source = Column(Text, nullable=False)
    extracted_content = Column(Text, nullable=False)
    links = Column(JSON, nullable=False)
    scores = Column(JSON, nullable=False)
    composite_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to crawl spec
    crawl_spec = relationship("CrawlSpecTable", back_populates="records")


class SQLiteCrawlResultsManager(CrawlResultsManager):
    """Results Manager that stores crawl records in a SQLite database using SQLAlchemy."""
    
    def __init__(self):
        """Initialize the SQLite results manager with settings and database connection."""
        self.settings = SQLiteCrawlResultsManagerSettings()
        
        # Ensure the database directory exists
        db_path = Path(self.settings.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create SQLAlchemy engine
        database_url = f"sqlite:///{self.settings.database_path}"
        self.engine = create_engine(
            database_url,
            echo=self.settings.echo_sql,
            pool_size=self.settings.pool_size,
            max_overflow=self.settings.max_overflow,
            # SQLite-specific settings
            connect_args={"check_same_thread": False}
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Initialized SQLiteCrawlResultsManager with database: {self.settings.database_path}")
    
    def create_crawl(self, crawl_spec: CrawlSpec, results_id: CrawlResultsId) -> None:
        """
        Create a new crawl record in the database.
        
        Args:
            crawl_spec: Specification for the crawl to create
            results_id: Identifier for the crawl results data set
        """
        logger.debug(f"Creating crawl in database for results_id: collection_id={results_id.collection_id}, data_id={results_id.data_id}")
        
        session = self.SessionLocal()
        try:
            # Check if crawl already exists
            existing_crawl = session.query(CrawlSpecTable).filter_by(id=crawl_spec.id).first()
            if existing_crawl:
                logger.warning(f"Crawl with ID {crawl_spec.id} already exists in database")
                return
            
            # Create new crawl spec record
            crawl_spec_record = CrawlSpecTable(
                id=crawl_spec.id,
                collection_id=results_id.collection_id,
                data_id=results_id.data_id,
                name=crawl_spec.name,
                seeds=crawl_spec.seeds,
                analyzer_specs=[spec.model_dump() for spec in crawl_spec.analyzer_specs],
                worker_count=crawl_spec.worker_count,
                domain_blacklist=crawl_spec.domain_blacklist
            )
            
            session.add(crawl_spec_record)
            session.commit()
            
            logger.info(f"Successfully created crawl in database: {crawl_spec.id} with results_id: {results_id.collection_id}/{results_id.data_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create crawl in database for {crawl_spec.id}: {e}")
            raise
        finally:
            session.close()
    
    def store_record(self, crawl_record: CrawlRecord, results_id: CrawlResultsId, crawl_id: str) -> None:
        """
        Store a crawl record in the database.
        
        Args:
            crawl_record: The crawl record to store
            results_id: Identifier for the crawl results data set
            crawl_id: Unique identifier for the crawl
        """
        session = self.SessionLocal()
        try:
            # Find the crawl spec by results_id
            crawl_spec_record = session.query(CrawlSpecTable).filter_by(
                collection_id=results_id.collection_id,
                data_id=results_id.data_id
            ).first()
            
            if not crawl_spec_record:
                logger.error(f"Crawl spec not found for results_id: {results_id.collection_id}/{results_id.data_id}")
                raise ValueError(f"Crawl spec not found for results_id: {results_id.collection_id}/{results_id.data_id}")
            
            # Check if record already exists
            existing_record = session.query(CrawlRecordTable).filter_by(
                id=crawl_record.id,
                crawl_spec_id=crawl_spec_record.id
            ).first()
            
            if existing_record:
                logger.debug(f"Crawl record {crawl_record.id} already exists, updating")
                # Update existing record
                existing_record.url = crawl_record.url
                existing_record.page_source = crawl_record.page_source
                existing_record.extracted_content = crawl_record.extracted_content
                existing_record.links = crawl_record.links
                existing_record.scores = crawl_record.scores
                existing_record.composite_score = crawl_record.composite_score
                existing_record.timestamp = crawl_record.timestamp
                existing_record.crawl_id = crawl_id
            else:
                # Create new record
                record = CrawlRecordTable(
                    id=crawl_record.id,
                    crawl_spec_id=crawl_spec_record.id,
                    crawl_id=crawl_id,
                    url=crawl_record.url,
                    page_source=crawl_record.page_source,
                    extracted_content=crawl_record.extracted_content,
                    links=crawl_record.links,
                    scores=crawl_record.scores,
                    composite_score=crawl_record.composite_score,
                    timestamp=crawl_record.timestamp
                )
                session.add(record)
            
            session.commit()
            logger.debug(f"Stored crawl record in database: {crawl_record.url}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to store crawl record for {crawl_record.url}: {e}")
            raise
        finally:
            session.close()
    
    def delete_crawl(self, results_id: CrawlResultsId) -> None:
        """
        Delete a crawl and all its records from the database.
        
        Args:
            results_id: Results ID of the crawl to delete
        """
        session = self.SessionLocal()
        try:
            # Find the crawl spec
            crawl_spec_record = session.query(CrawlSpecTable).filter_by(
                collection_id=results_id.collection_id,
                data_id=results_id.data_id
            ).first()
            
            if crawl_spec_record:
                # Delete the crawl spec (cascade will delete all records)
                session.delete(crawl_spec_record)
                session.commit()
                logger.info(f"Deleted crawl from database: {results_id.collection_id}/{results_id.data_id}")
            else:
                logger.warning(f"Crawl not found in database: {results_id.collection_id}/{results_id.data_id}")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete crawl from database for {results_id.collection_id}/{results_id.data_id}: {e}")
            raise
        finally:
            session.close()
    
    def get_crawl_records(self, results_id: CrawlResultsId, limit: Optional[int] = None) -> list:
        """
        Retrieve crawl records for a given results_id.
        
        Args:
            results_id: Results ID to get records for
            limit: Optional limit on number of records to return
            
        Returns:
            List of CrawlRecord objects
        """
        session = self.SessionLocal()
        try:
            # Find the crawl spec
            crawl_spec_record = session.query(CrawlSpecTable).filter_by(
                collection_id=results_id.collection_id,
                data_id=results_id.data_id
            ).first()
            
            if not crawl_spec_record:
                return []
            
            # Query records
            query = session.query(CrawlRecordTable).filter_by(crawl_spec_id=crawl_spec_record.id)
            
            if limit:
                query = query.limit(limit)
            
            records = query.all()
            
            # Convert to CrawlRecord objects
            crawl_records = []
            for record in records:
                crawl_record = CrawlRecord(
                    url=record.url,
                    page_source=record.page_source,
                    extracted_content=record.extracted_content,
                    links=record.links,
                    scores=record.scores,
                    composite_score=record.composite_score,
                    timestamp=record.timestamp
                )
                crawl_records.append(crawl_record)
            
            return crawl_records
            
        except Exception as e:
            logger.error(f"Failed to retrieve crawl records for {results_id.collection_id}/{results_id.data_id}: {e}")
            raise
        finally:
            session.close()
    
    def get_crawl_stats(self, results_id: CrawlResultsId) -> dict:
        """
        Get statistics for a crawl.
        
        Args:
            results_id: Results ID to get stats for
            
        Returns:
            Dictionary with crawl statistics
        """
        session = self.SessionLocal()
        try:
            # Find the crawl spec
            crawl_spec_record = session.query(CrawlSpecTable).filter_by(
                collection_id=results_id.collection_id,
                data_id=results_id.data_id
            ).first()
            
            if not crawl_spec_record:
                return {"total_records": 0, "avg_score": 0.0, "max_score": 0.0, "min_score": 0.0}
            
            # Get record statistics
            from sqlalchemy import func
            stats = session.query(
                func.count(CrawlRecordTable.id).label('total_records'),
                func.avg(CrawlRecordTable.composite_score).label('avg_score'),
                func.max(CrawlRecordTable.composite_score).label('max_score'),
                func.min(CrawlRecordTable.composite_score).label('min_score')
            ).filter_by(crawl_spec_id=crawl_spec_record.id).first()
            
            return {
                "total_records": stats.total_records or 0,
                "avg_score": float(stats.avg_score or 0.0),
                "max_score": float(stats.max_score or 0.0),
                "min_score": float(stats.min_score or 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get crawl stats for {results_id.collection_id}/{results_id.data_id}: {e}")
            raise
        finally:
            session.close()
    
    def __del__(self):
        """Cleanup database connections on deletion."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
