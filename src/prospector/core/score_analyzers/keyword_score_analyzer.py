import math
import re
from typing import List

from prospector.core.models import KeywordScoringSpec, WeightedKeyword, WeightedRegex
from .score_analyzer import ScoreAnalyzer


class KeywordScoreAnalyzer(ScoreAnalyzer):
    """Score analyzer that scores text based on keyword and regex matches."""
    
    def __init__(self, spec: KeywordScoringSpec):
        """
        Initialize the keyword analyzer.
        
        Args:
            spec: KeywordScoringSpec containing weighted keywords and regexes
            
        Raises:
            ValueError: If spec is None or contains no keywords/regexes
        """

        if not spec:
            raise ValueError("KeywordScoringSpec cannot be None")

        self.keywords = spec.keywords
        self.regexes = spec.regexes
        
        # Pre-compile regex patterns for efficiency
        self.compiled_regexes = []
        for weighted_regex in self.regexes:
            try:
                compiled_pattern = re.compile(weighted_regex.regex, weighted_regex.flags)
                self.compiled_regexes.append((compiled_pattern, weighted_regex.weight))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{weighted_regex.regex}': {e}")
    
    def score(self, content: str) -> float:
        """
        Score content based on weighted keyword and regex matches.
        
        Keywords use case-insensitive matching and count all occurrences.
        Regexes use the specified flags and count all non-overlapping matches.
        Uses logarithmic scaling to normalize scores to 0-1 range.
        
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
        
        total_weighted_score = 0.0
        
        # Score keywords (case-insensitive)
        content_lower = content.lower()
        for weighted_keyword in self.keywords:
            keyword_lower = weighted_keyword.keyword.lower()
            # Use regex to find non-overlapping matches
            matches = len(re.findall(re.escape(keyword_lower), content_lower))
            total_weighted_score += matches * weighted_keyword.weight
        
        # Score regexes (using specified flags)
        for compiled_pattern, weight in self.compiled_regexes:
            matches = len(compiled_pattern.findall(content))
            total_weighted_score += matches * weight
        
        # Apply logarithmic scaling for better separation
        if total_weighted_score == 0:
            return 0.0
        
        # Log normalization with base adjustment
        normalized_score = math.log10(1 + total_weighted_score) / math.log10(101)  # Scale to 0-1
        return min(1.0, max(0.0, normalized_score))
