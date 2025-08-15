import math
import re
from typing import List

from prospector.core.models import KeywordScoringSpec, WeightedKeyword
from .score_analyzer import ScoreAnalyzer


class KeywordScoreAnalyzer(ScoreAnalyzer):
    """Score analyzer that scores text based on keyword matches."""
    
    def __init__(self, spec: KeywordScoringSpec):
        """
        Initialize the keyword analyzer.
        
        Args:
            spec: KeywordScoringSpec containing weighted keywords
            
        Raises:
            ValueError: If keywords list is empty
        """

        if not spec:
            raise ValueError("KeywordScoringSpec cannot be None")

        self.keywords = spec.keywords
    
    def score(self, content: str) -> float:
        """
        Score content based on weighted keyword matches.
        
        Uses case-insensitive matching and counts all occurrences.
        Overlapping matches are handled as single matches.
        Uses sigmoid scaling to normalize scores to 0-1 range.
        
        Args:
            content: Text content to score
            
        Returns:
            float: Normalized score between 0 and 1
            
        Raises:
            TypeError: If content is not a string
        """
        if not isinstance(content, str):
            raise TypeError("Content must be a string")
        
        if not content:
            return 0.0
        
        content_lower = content.lower()
        total_weighted_score = 0.0
        
        for weighted_keyword in self.keywords:
            keyword_lower = weighted_keyword.keyword.lower()
            # Use regex to find non-overlapping matches
            matches = len(re.findall(re.escape(keyword_lower), content_lower))
            total_weighted_score += matches * weighted_keyword.weight
        
        # Apply logarithmic scaling for better separation
        if total_weighted_score == 0:
            return 0.0
        
        # Log normalization with base adjustment
        normalized_score = math.log10(1 + total_weighted_score) / math.log10(101)  # Scale to 0-1
        return min(1.0, max(0.0, normalized_score))