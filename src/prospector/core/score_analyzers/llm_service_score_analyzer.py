"""LLMServiceScoreAnalyzer - A score analyzer that uses an external LLM service for content scoring."""

import json
import logging
import requests

from prospector.core.models import LLMScoreServiceInput, LLMScoreRequest
from prospector.core.settings import ScoreAnalyzerSettings
from .score_analyzer import ScoreAnalyzer

logger = logging.getLogger(__name__)


class LLMServiceScoreAnalyzer(ScoreAnalyzer):
    """Score analyzer that uses an external LLM service for content scoring."""
    
    def __init__(self):
        """Initialize the LLM service analyzer with settings and session."""
        self.settings = ScoreAnalyzerSettings()
        # Create a requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def score(self, content: LLMScoreServiceInput) -> float:
        """
        Score content using an external LLM service.
        
        Makes an HTTP POST request to the configured LLM service with the text
        content and prompt. Returns the score provided by the service.
        
        Args:
            content: LLMScoreServiceInput containing text and optional prompt
            
        Returns:
            float: Score between 0 and 1 from the LLM service
            
        Raises:
            TypeError: If content is not LLMScoreServiceInput
        """
        if not isinstance(content, LLMScoreServiceInput):
            raise TypeError("Content must be LLMScoreServiceInput")
        
        try:
            # Use provided prompt or default from settings
            prompt = content.prompt if content.prompt is not None else self.settings.llm_default_prompt
            
            # Create the request payload
            request_data = LLMScoreRequest(
                prompt=f"{prompt}\n\nText to score: {content.text}",
                model_output_format=self.settings.llm_model_output_format
            )
            
            # Make the HTTP POST request
            response = self.session.post(
                self.settings.llm_service_url,
                json=request_data.model_dump(),
                timeout=self.settings.llm_request_timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            response_data = response.json()
            
            # Extract score from response
            if 'score' not in response_data:
                logger.error(f"LLM service response missing 'score' field: {response_data}")
                return 0.0
            
            try:
                score = float(response_data['score'])
                
                # Validate score is in range 0-1
                if not (0.0 <= score <= 1.0):
                    logger.error(f"LLM service returned score outside 0-1 range: {score}")
                    return 0.0
                
                return score
                
            except (ValueError, TypeError) as e:
                logger.error(f"Could not parse score value '{response_data['score']}': {e}")
                return 0.0
        
        except requests.exceptions.Timeout as e:
            logger.error(f"LLM service request timeout: {e}")
            return 0.0
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM service request failed: {e}")
            return 0.0
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM service: {e}")
            return 0.0
        
        except Exception as e:
            logger.error(f"Unexpected error calling LLM service: {e}")
            return 0.0
    
    def __del__(self):
        """Cleanup the requests session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()