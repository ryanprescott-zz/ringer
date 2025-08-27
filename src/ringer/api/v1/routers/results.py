"""Results router for crawl record retrieval endpoints."""

from fastapi import APIRouter, HTTPException, Path, Request
from ringer.api.v1.models import CrawlRecordsRequest, CrawlRecordsResponse
from ringer.core.ringer import Ringer

router = APIRouter(prefix="/results", tags=["results"])

# Global Ringer instance
ringer = Ringer()


@router.post("/{crawl_id}/records", response_model=CrawlRecordsResponse)
async def get_crawl_records(
    crawl_id: str,
    request: CrawlRecordsRequest,
    app_request: Request
) -> CrawlRecordsResponse:
    """
    Retrieve crawl records for a specific crawl.
    
    Args:
        crawl_id: The ID of the crawl to retrieve records for
        request: Request containing record_count and score_type parameters
        
    Returns:
        CrawlRecordsResponse containing the list of crawl records
        
    Raises:
        HTTPException: 404 if crawl not found, 400 if score_type is invalid
    """
    try:
        ringer = app_request.app.state.ringer
        records = ringer.get_crawl_records(
            crawl_id=crawl_id,
            record_count=request.record_count,
            score_type=request.score_type
        )
        
        return CrawlRecordsResponse(records=records)
        
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
