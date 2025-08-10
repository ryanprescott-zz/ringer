"""Score analyzers for web page content."""

from abc import ABC, abstractmethod
from typing import Any

from prospector.core.models import WeightedKeyword


class ScoreAnalyzer(ABC):
    """Abstract base class for content score analyzers."""
    
    @abstractmethod
    def score(self, content: Any) -> float:
        """
        Score the provided content.
        
        Args:
            content: Content to score (type varies by analyzer)
            
        Returns:
            float: Score between 0 and 1
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError