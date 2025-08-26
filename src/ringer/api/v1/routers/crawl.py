"""FastAPI router for crawl-related endpoints."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from ringer.api.v1.models import (
    CreateCrawlRequest, CreateCrawlResponse,
    StartCrawlResponse,
    StopCrawlResponse,
    DeleteCrawlResponse,
    CrawlStatusResponse, CrawlStatusListResponse,
    CrawlInfoResponse, CrawlInfoListResponse
)

router = APIRouter(
    prefix="/crawls",
    tags=["crawls"],
)


@router.post("", response_model=CreateCrawlResponse)
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
        ringer = app_request.app.state.ringer
        crawl_id, run_state = ringer.create(request.crawl_spec)
        
        return CreateCrawlResponse(
            crawl_id=crawl_id,
            run_state=run_state
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{crawl_id}/start", response_model=StartCrawlResponse)
def start_crawl(crawl_id: str, app_request: Request) -> StartCrawlResponse:
    """
    Start a previously created crawl.
    
    Args:
        crawl_id: ID of the crawl to start
        app_request: FastAPI request object to access application state
        
    Returns:
        StartCrawlResponse: Response containing crawl ID and start time
        
    Raises:
        HTTPException: If crawl start fails
    """
    try:
        ringer = app_request.app.state.ringer
        crawl_id, run_state = ringer.start(crawl_id)
        
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


@router.post("/{crawl_id}/stop", response_model=StopCrawlResponse)
def stop_crawl(crawl_id: str, app_request: Request) -> StopCrawlResponse:
    """
    Stop a running crawl.
    
    Args:
        crawl_id: ID of the crawl to stop
        app_request: FastAPI request object to access application state
        
    Returns:
        StopCrawlResponse: Response containing crawl ID and stop time
        
    Raises:
        HTTPException: If crawl stop fails
    """
    try:
        ringer = app_request.app.state.ringer
        crawl_id, run_state = ringer.stop(crawl_id)
        
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


@router.delete("/{crawl_id}", response_model=DeleteCrawlResponse)
def delete_crawl(crawl_id: str, app_request: Request) -> DeleteCrawlResponse:
    """
    Delete a crawl from the system.
    
    Args:
        crawl_id: ID of the crawl to delete
        app_request: FastAPI request object to access application state
        
    Returns:
        DeleteCrawlResponse: Response containing crawl ID and deletion time
        
    Raises:
        HTTPException: If crawl deletion fails
    """
    try:
        ringer = app_request.app.state.ringer
        ringer.delete(crawl_id)
        
        # Set deletion time to now since the crawl state is removed
        deletion_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return DeleteCrawlResponse(
            crawl_id=crawl_id,
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
        ringer = app_request.app.state.ringer
        crawl_status_dicts = ringer.get_all_crawl_statuses()
        
        # Create the API models from the dictionaries
        from ringer.api.v1.models import CrawlStatus
        crawl_statuses = [CrawlStatus(**status_dict) for status_dict in crawl_status_dicts]
        
        return CrawlStatusListResponse(crawls=crawl_statuses)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("", response_model=CrawlInfoListResponse)
def get_all_crawl_info(app_request: Request) -> CrawlInfoListResponse:
    """
    Get complete information (spec + status) for all crawls.
    
    Args:
        app_request: FastAPI request object to access application state
        
    Returns:
        CrawlInfoListResponse: Response containing list of crawl information
        
    Raises:
        HTTPException: If crawl info retrieval fails
    """
    try:
        ringer = app_request.app.state.ringer
        crawl_info_dicts = ringer.get_all_crawl_info()
        
        # Create the API models from the dictionaries
        from ringer.api.v1.models import CrawlInfo, CrawlStatus
        from ringer.core.models import CrawlSpec
        
        crawl_infos = []
        for info_dict in crawl_info_dicts:
            crawl_spec = CrawlSpec(**info_dict["crawl_spec"])
            crawl_status = CrawlStatus(**info_dict["crawl_status"])
            crawl_info = CrawlInfo(crawl_spec=crawl_spec, crawl_status=crawl_status)
            crawl_infos.append(crawl_info)
        
        return CrawlInfoListResponse(crawls=crawl_infos)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{crawl_id}", response_model=CrawlInfoResponse)
def get_crawl_info(crawl_id: str, app_request: Request) -> CrawlInfoResponse:
    """
    Get complete information (spec + status) for a crawl.
    
    Args:
        crawl_id: ID of the crawl to get info for
        app_request: FastAPI request object to access application state
        
    Returns:
        CrawlInfoResponse: Response containing crawl information
        
    Raises:
        HTTPException: If crawl info retrieval fails
    """
    try:
        ringer = app_request.app.state.ringer
        crawl_info_dict = ringer.get_crawl_info(crawl_id)
        
        # Create the API models from the dictionary
        from ringer.api.v1.models import CrawlInfo, CrawlStatus
        from ringer.core.models import CrawlSpec
        
        crawl_spec = CrawlSpec(**crawl_info_dict["crawl_spec"])
        crawl_status = CrawlStatus(**crawl_info_dict["crawl_status"])
        crawl_info = CrawlInfo(crawl_spec=crawl_spec, crawl_status=crawl_status)
        
        return CrawlInfoResponse(info=crawl_info)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
        ringer = app_request.app.state.ringer
        crawl_status_dict = ringer.get_crawl_status(crawl_id)
        
        # Create the API models from the dictionary
        from ringer.api.v1.models import CrawlStatus
        crawl_status = CrawlStatus(**crawl_status_dict)
        
        return CrawlStatusResponse(status=crawl_status)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{crawl_id}/spec/download")
def download_crawl_spec(crawl_id: str, app_request: Request) -> JSONResponse:
    """
    Download the CrawlSpec for a crawl as a JSON file.
    
    Args:
        crawl_id: ID of the crawl to download spec for
        app_request: FastAPI request object to access application state
        
    Returns:
        JSONResponse: Response containing crawl spec as downloadable JSON
        
    Raises:
        HTTPException: If crawl does not exist
    """
    try:
        ringer = app_request.app.state.ringer
        crawl_info_dict = ringer.get_crawl_info(crawl_id)
        
        # Extract just the crawl spec
        crawl_spec_dict = crawl_info_dict["crawl_spec"]
        
        # Set headers to trigger download
        headers = {
            "Content-Disposition": f"attachment; filename=crawl_spec_{crawl_id}.json",
            "Content-Type": "application/json"
        }
        
        return JSONResponse(content=crawl_spec_dict, headers=headers)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail="The requested crawl does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
