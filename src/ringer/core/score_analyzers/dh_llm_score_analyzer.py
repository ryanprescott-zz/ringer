"""DhLlmScoreAnalyzer - A score analyzer that uses the DH LLM service for content scoring."""

import json
import logging
import requests

from ringer.core.models import (
    DhLlmScoringSpec,
    PromptInput,
    TextInput,
    DhLlmScoreRequest
)
from ringer.core.settings import DhLlmScoreAnalyzerSettings
from .score_analyzer import ScoreAnalyzer

logger = logging.getLogger(__name__)


class DhLlmScoreAnalyzer(ScoreAnalyzer):
    """Score analyzer that uses the DH LLM service for content scoring."""
    
    def __init__(self, spec: DhLlmScoringSpec):
        """
        Initialize the score analyzer.
        
        Args:
            spec: DhLlmScoringSpec containing LLM inputs (prompt or topics)
            
        Raises:
            ValueError: If keywords list is empty
        """
        self.settings = DhLlmScoreAnalyzerSettings()
        # Create a requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        # Store the prompt input for scoring
        self._scoring_prompt_input = spec.prompt_input

        logger.info(f"Scoring prompt: {self._scoring_prompt_input.prompt}")
    

    def score(self, content: str) -> float:
        """
        Score content using the DH LLM service.
        
        Makes an HTTP POST request to the configured service with the text
        content and prompt. Returns the score provided by the service.
        
        Args:
            content (str): Content to score
            
        Returns:
            float: Score between 0 and 1 from the service
            
        Raises:
            TypeError: If content is not DhLlmScoreServiceInput
        """
        if not isinstance(content, str):
            raise TypeError("Content must be a string")
            
        logger.debug(f"Scoring content with DH LLM service (length: {len(content)} chars)")
        
        try:
            # Create the request payload
            try:
                request_data = DhLlmScoreRequest(
                    prompt_input=self._scoring_prompt_input,
                    text_inputs=[TextInput(id="1", text=content)],
                )
                logger.debug("Created LLM service request payload")
            except Exception as e:
                logger.error(f"Failed to create LLM service request payload: {e}")
                return 0.0
            
            # Make the HTTP POST request
            try:
                logger.debug(f"Making request to LLM service: {self.settings.service_url}")
                response = self.session.post(
                    self.settings.service_url,
                    json=request_data.model_dump(),
                    timeout=self.settings.request_timeout,
                )
                logger.debug(f"Received response from LLM service with status: {response.status_code}")
            except Exception as e:
                logger.error(f"Failed to make request to LLM service: {e}")
                raise
            
            # Check for HTTP errors
            try:
                response.raise_for_status()
            except Exception as e:
                logger.error(f"LLM service returned HTTP error {response.status_code}: {e}")
                raise
            
            # Parse JSON response
            try:
                response_data = response.json()
                logger.debug("Successfully parsed LLM service JSON response")
            except Exception as e:
                logger.error(f"Failed to parse LLM service JSON response: {e}")
                raise
            
            # Extract score from response
            if 'scored_responses_json' not in response_data:
                logger.error(f"LLM service response missing 'scored_responses_json' field: {response_data}")
                return 0.0
            
            scored_responses = response_data['scored_responses_json']
            if not isinstance(scored_responses, list) or len(scored_responses) == 0:
                logger.error(f"LLM service response 'scored_responses_json' is not a non-empty list: {scored_responses}")
                return 0.0
            
            first_response = scored_responses[0]
            if 'score' not in first_response:
                logger.error(f"LLM service response missing 'score' field in first scored response: {first_response}")
                return 0.0
            
            try:
                score = float(first_response['score'])
                logger.debug(f"Extracted score from LLM service response: {score}")
                
                # Validate score is in range 0-1
                if not (0.0 <= score <= 1.0):
                    logger.error(f"LLM service returned score outside 0-1 range: {score}")
                    return 0.0
                
                logger.debug(f"Successfully scored content with LLM service: {score}")
                return score
                
            except (ValueError, TypeError) as e:
                logger.error(f"Could not parse score value '{first_response['score']}': {e}")
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
