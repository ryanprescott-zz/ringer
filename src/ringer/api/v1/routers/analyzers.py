"""FastAPI router for analyzer information endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from ringer.api.v1.models import AnalyzerInfoResponse, AnalyzerInfo, FieldDescriptor
from ringer.core.utils import ScoreAnalyzerInfoUtil

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analyzers",
    tags=["analyzers"],
)


@router.get("/info", response_model=AnalyzerInfoResponse)
def get_analyzer_info() -> AnalyzerInfoResponse:
    """
    Get information about available score analyzers.
    
    Returns information about all available ScoreAnalyzer subclasses that can be
    configured as part of a CrawlSpec, including their parameter specifications.
    
    Returns:
        AnalyzerInfoResponse: Response containing analyzer information
        
    Raises:
        HTTPException: If analyzer information retrieval fails
    """
    try:
        # Get analyzer information from utility class
        analyzer_info_list = ScoreAnalyzerInfoUtil.get_analyzer_info_list()
        
        # Convert to API model format
        api_analyzers = []
        for analyzer_info in analyzer_info_list:
            # Convert field descriptors
            api_fields = []
            for field_desc in analyzer_info.spec_fields:
                api_field = FieldDescriptor(
                    name=field_desc.name,
                    type=field_desc.type_str,
                    description=field_desc.description,
                    required=field_desc.required,
                    default=field_desc.default
                )
                api_fields.append(api_field)
            
            # Create API analyzer info
            api_analyzer = AnalyzerInfo(
                name=analyzer_info.name,
                description=analyzer_info.description,
                spec_fields=api_fields
            )
            api_analyzers.append(api_analyzer)
        
        return AnalyzerInfoResponse(analyzers=api_analyzers)
        
    except Exception as e:
        logger.error(f"Failed to get analyzer information: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
