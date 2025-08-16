"""FastAPI router for crawl-related endpoints."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from prospector.api.v1.models import (
    CreateCrawlRequest, CreateCrawlResponse,
    StartCrawlRequest, StartCrawlResponse,
    StopCrawlRequest, StopCrawlResponse,
    DeleteCrawlRequest, DeleteCrawlResponse,
    CrawlStatusResponse, CrawlStatusListResponse
)

router = APIRouter(
    prefix="/crawl",
    tags=["crawl"],
)


@router.post("/create", response_model=CreateCrawlResponse)
def create_crawl(request: CreateCrawlRequest, app_request: Request) -> CreateCrawlResponse:
    """
    Create a new crawl.
    
    Args:
        request: The crawl creation request containing crawl specification
        app_request: FastAPI request object to access application state
        
    Returns:
        CreateCrawlResponse: Response containing crawl ID and creation time
        
    Raises:
        HTTPException: If crawl creation fails
    """
    try:
        prospector = app_request.app.state.prospector
        crawl_id, run_state = prospector.create(request.crawl_spec)
        
        return CreateCrawlResponse(
            crawl_id=crawl_id,
            run_state=run_state
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/start", response_model=StartCrawlResponse)
def start_crawl(request: StartCrawlRequest, app_request: Request) -> StartCrawlResponse:
    """
    Start a previously created crawl.
    
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
        crawl_id, run_state = prospector.start(request.crawl_id)
        
        return StartCrawlResponse(
            crawl_id=crawl_id,
            run_state=run_state
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/stop", response_model=StopCrawlResponse)
def stop_crawl(request: StopCrawlRequest, app_request: Request) -> StopCrawlResponse:
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
        crawl_id, run_state = prospector.stop(request.crawl_id)
        
        return StopCrawlResponse(
            crawl_id=crawl_id,
            run_state=run_state
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/delete", response_model=DeleteCrawlResponse)
def delete_crawl(request: DeleteCrawlRequest, app_request: Request) -> DeleteCrawlResponse:
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


@router.get("/status", response_model=CrawlStatusListResponse)
def get_all_crawl_statuses(app_request: Request) -> CrawlStatusListResponse:
    """
    Get status information for all crawls.
    
    Args:
        app_request: FastAPI request object to access application state
        
    Returns:
        CrawlStatusListResponse: Response containing list of crawl status information
        
    Raises:
        HTTPException: If crawl status retrieval fails
    """
    try:
        prospector = app_request.app.state.prospector
        crawl_status_dicts = prospector.get_all_crawl_statuses()
        
        # Create the API models from the dictionaries
        from prospector.api.v1.models import CrawlStatus
        crawl_statuses = [CrawlStatus(**status_dict) for status_dict in crawl_status_dicts]
        
        return CrawlStatusListResponse(crawls=crawl_statuses)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{crawl_id}/status", response_model=CrawlStatusResponse)
def get_crawl_status(crawl_id: str, app_request: Request) -> CrawlStatusResponse:
    """
    Get status information for a crawl.
    
    Args:
        crawl_id: ID of the crawl to get status for
        app_request: FastAPI request object to access application state
        
    Returns:
        CrawlStatusResponse: Response containing crawl status information
        
    Raises:
        HTTPException: If crawl status retrieval fails
    """
    try:
        prospector = app_request.app.state.prospector
        crawl_status_dict = prospector.get_crawl_status(crawl_id)
        
        # Create the API models from the dictionary
        from prospector.api.v1.models import CrawlStatus
        crawl_status = CrawlStatus(**crawl_status_dict)
        
        return CrawlStatusResponse(status=crawl_status)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
