"""Results router for crawl record retrieval endpoints."""

from fastapi import APIRouter, HTTPException, Path, Request
from ringer.api.v1.models import (
    CrawlRecordSummaryRequest, 
    CrawlRecordSummaryResponse, 
    CrawlRecordRequest, 
    CrawlRecordResponse
)
from ringer.core.ringer import Ringer

router = APIRouter(prefix="/results", tags=["results"])



@router.post("/{crawl_id}/record_summaries", response_model=CrawlRecordSummaryResponse)
async def get_crawl_record_summaries(
    crawl_id: str,
    request: CrawlRecordSummaryRequest,
    app_request: Request
) -> CrawlRecordSummaryResponse:
    """
    Retrieve crawl record summaries for a specific crawl.
    
    Args:
        crawl_id: The ID of the crawl to retrieve record summaries for
        request: Request containing record_count and score_type parameters
        
    Returns:
        CrawlRecordSummaryResponse containing the list of crawl record summaries
        
    Raises:
        HTTPException: 404 if crawl not found, 400 if score_type is invalid
    """
    try:
        ringer = app_request.app.state.ringer
        record_summaries = ringer.get_crawl_record_summaries(
            crawl_id=crawl_id,
            record_count=request.record_count,
            score_type=request.score_type
        )
        
        return CrawlRecordSummaryResponse(records=record_summaries)
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "score_type" in error_msg.lower() or "invalid" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{crawl_id}/records", response_model=CrawlRecordResponse)
async def get_crawl_records(
    crawl_id: str,
    request: CrawlRecordRequest,
    app_request: Request
) -> CrawlRecordResponse:
    """
    Retrieve crawl records for a specific crawl by record IDs.
    
    Args:
        crawl_id: The ID of the crawl to retrieve records for
        request: Request containing list of record IDs to retrieve
        
    Returns:
        CrawlRecordResponse containing the list of crawl records
        
    Raises:
        HTTPException: 404 if crawl not found or no records exist for the given IDs
    """
    try:
        ringer = app_request.app.state.ringer
        records = ringer.get_crawl_records(
            crawl_id=crawl_id,
            record_ids=request.record_ids
        )
        
        # If no records found, return 404
        if not records:
            raise HTTPException(
                status_code=404, 
                detail=f"No records found for the provided record IDs in crawl {crawl_id}"
            )
        
        return CrawlRecordResponse(records=records)
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
