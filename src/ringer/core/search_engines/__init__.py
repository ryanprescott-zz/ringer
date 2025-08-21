"""Search engine integration for seed URL generation."""

from .search_engine_service import (
    SearchEngineService,
    SearchEngineParser,
    GoogleParser,
    BingParser,
    DuckDuckGoParser,
)

__version__ = "1.0.0"
__all__ = [
    "SearchEngineService",
    "SearchEngineParser",
    "GoogleParser",
    "BingParser",
    "DuckDuckGoParser",
]
