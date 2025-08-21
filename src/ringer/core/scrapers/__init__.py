"""scrapers - Implementation of web scrapers for Prospector."""

from .scraper import Scraper
from .playwright_scraper import PlaywrightScraper

__version__ = "1.0.0"
__all__ = [
    "Scraper",
    "PlaywrightScraper",
]