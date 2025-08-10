"""FastAPI router for crawl-related endpoints."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from prospector.api.v1.models import (
    SubmitCrawlRequest, SubmitCrawlResponse,
    CrawlStartRequest, StartCrawlResponse,
    CrawlStopRequest, StopCrawlResponse,
    CrawlDeleteRequest, DeleteCrawlResponse
)

router = APIRouter()


@router.post("/submit", response_model=SubmitCrawlResponse)
def submit_crawl(request: SubmitCrawlRequest, app_request: Request) -> SubmitCrawlResponse:
    """
    Submit a new crawl for processing.
    
    Args:
        request: The crawl submission request containing crawl specification
        app_request: FastAPI request object to access application state
        
    Returns:
        SubmitCrawlResponse: Response containing crawl ID and submission time
        
    Raises:
        HTTPException: If crawl submission fails
    """
    try:
        prospector = app_request.app.state.prospector
        crawl_id = prospector.submit(request.crawl_spec)
        
        # Get the submitted time from the crawl state
        crawl_state = prospector.crawls[crawl_id]
        
        return SubmitCrawlResponse(
            crawl_id=crawl_id,
            crawl_submitted_time=crawl_state.crawl_submitted_time
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/start", response_model=StartCrawlResponse)
def start_crawl(request: CrawlStartRequest, app_request: Request) -> StartCrawlResponse:
    """
    Start a previously submitted crawl.
    
    Args:
        request: The crawl start request containing crawl ID
        app_request: FastAPI request object to access application state
        
    Returns:
        StartCrawlResponse: Response containing crawl ID and start time
        
    Raises:
        HTTPException: If crawl start fails
    """
    try:
        prospector = app_request.app.state.prospector
        prospector.start(request.crawl_id)
        
        # Get the started time from the crawl state
        crawl_state = prospector.crawls[request.crawl_id]
        
        return StartCrawlResponse(
            crawl_id=request.crawl_id,
            crawl_started_time=crawl_state.crawl_started_time
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/stop", response_model=StopCrawlResponse)
def stop_crawl(request: CrawlStopRequest, app_request: Request) -> StopCrawlResponse:
    """
    Stop a running crawl.
    
    Args:
        request: The crawl stop request containing crawl ID
        app_request: FastAPI request object to access application state
        
    Returns:
        StopCrawlResponse: Response containing crawl ID and stop time
        
    Raises:
        HTTPException: If crawl stop fails
    """
    try:
        prospector = app_request.app.state.prospector
        prospector.stop(request.crawl_id)
        
        # Get the stopped time from the crawl state
        crawl_state = prospector.crawls[request.crawl_id]
        
        return StopCrawlResponse(
            crawl_id=request.crawl_id,
            crawl_stopped_time=crawl_state.crawl_stopped_time
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/delete", response_model=DeleteCrawlResponse)
def delete_crawl(request: CrawlDeleteRequest, app_request: Request) -> DeleteCrawlResponse:
    """
    Delete a crawl from the system.
    
    Args:
        request: The crawl delete request containing crawl ID
        app_request: FastAPI request object to access application state
        
    Returns:
        DeleteCrawlResponse: Response containing crawl ID and deletion time
        
    Raises:
        HTTPException: If crawl deletion fails
    """
    try:
        prospector = app_request.app.state.prospector
        prospector.delete(request.crawl_id)
        
        # Set deletion time to now since the crawl state is removed
        deletion_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return DeleteCrawlResponse(
            crawl_id=request.crawl_id,
            crawl_deleted_time=deletion_time
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
